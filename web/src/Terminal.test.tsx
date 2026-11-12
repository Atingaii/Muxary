// @vitest-environment jsdom
import React from 'react';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AgentTerminal, inputBase64, terminalGeometry, MAX_PENDING_OUTPUT } from './Terminal';

const mock = vi.hoisted(() => ({
  api: vi.fn(), fit: vi.fn(), terminals: [] as {cols: number; rows: number; resize: ReturnType<typeof vi.fn>; write: ReturnType<typeof vi.fn>; input?: (data: string) => void; dispose: ReturnType<typeof vi.fn>}[],
  resize: undefined as (() => void) | undefined,
}));
vi.mock('./model', async importOriginal => ({...await importOriginal<typeof import('./model')>(), api: mock.api}));
vi.mock('@xterm/xterm', () => ({Terminal: class {
  cols = 80; rows = 24; input?: (data: string) => void;
  resize = vi.fn((columns: number, rows: number) => {this.cols = columns; this.rows = rows;});
  write = vi.fn(); dispose = vi.fn();
  constructor() {mock.terminals.push(this);}
  loadAddon() {} open() {}
  onData(callback: (data: string) => void) {this.input = callback; return {dispose: vi.fn()};}
}}));
vi.mock('@xterm/addon-fit', () => ({FitAddon: class {fit = mock.fit;}}));
class Socket {
  static OPEN = 1; static instances: Socket[] = [];
  readyState = 0; sent: Record<string, unknown>[] = []; failSend = false;
  onopen?: () => void; onmessage?: (event: {data: string}) => void; onclose?: () => void; onerror?: () => void;
  constructor(public url: string) {Socket.instances.push(this);}
  send(data: string) {if (this.failSend) throw new Error('transport failed'); this.sent.push(JSON.parse(data));}
  close = vi.fn(() => {this.readyState = 3; this.onclose?.();});
  open() {this.readyState = 1; this.onopen?.();}
  frame(value: Record<string, unknown>) {this.onmessage?.({data: JSON.stringify(value)});}
}
beforeEach(() => {
  mock.api.mockReset(); mock.api.mockResolvedValue({terminal_id: 'term_fixture', terminal_token: 'native-token'});
  mock.fit.mockClear(); mock.terminals.length = 0; mock.resize = undefined; Socket.instances = [];
  vi.stubGlobal('WebSocket', Socket);
  vi.stubGlobal('ResizeObserver', class {constructor(callback: () => void) {mock.resize = callback;} observe() {} disconnect() {}});
});
afterEach(() => {cleanup(); vi.unstubAllGlobals();});
async function ready() {
  const rendered = render(<AgentTerminal project="p" agent="buddy" epoch={1} />);
  await waitFor(() => expect(Socket.instances).toHaveLength(1));
  const socket = Socket.instances[0];
  act(() => {socket.open(); socket.frame({type: 'open', geometry: {columns: 140, rows: 42}, resize_policy: 'fixed_source', last_input_seq: 0});});
  return {socket, terminal: mock.terminals[0], ...rendered};
}
describe('native terminal wire contract', () => {
  it('reads nested open geometry and top-level geometry changes', () => {
    expect(terminalGeometry({type: 'open', geometry: {columns: 132, rows: 40}})).toEqual({columns: 132, rows: 40});
    expect(terminalGeometry({type: 'geometry', columns: 90, rows: 24})).toEqual({columns: 90, rows: 24});
    expect(terminalGeometry({type: 'open', columns: 80, rows: 24})).toBeNull();
    expect(terminalGeometry({type: 'geometry', columns: 0, rows: 24})).toBeNull();
  });
  it('keeps UTF-8 and large paste bytes intact without spread-stack overflow', () => {
    const original = '中文🙂'.repeat(10000);
    const encoded = inputBase64(original);
    expect(new TextDecoder().decode(Uint8Array.from(atob(encoded), byte => byte.charCodeAt(0)))).toBe(original);
    expect(() => inputBase64('x'.repeat(512 * 1024 + 1))).toThrow('输入过大');
  });
  it('uses exact open token, keeps the shared pane grid, and writes compatibility output', async () => {
    const {socket, terminal} = await ready();
    expect(socket.sent[0]).toEqual({type: 'open', terminal_id: 'term_fixture', token: 'native-token'});
    expect(terminal.resize).toHaveBeenLastCalledWith(140, 42);
    const fits = mock.fit.mock.calls.length;
    act(() => {mock.resize?.(); socket.frame({type: 'geometry', columns: 120, rows: 35, resize_policy: 'fixed_source'}); socket.frame({type: 'output', bytes_b64: btoa('hello')});});
    expect(mock.fit).toHaveBeenCalledTimes(fits);
    expect(socket.sent.some(frame => frame.type === 'resize')).toBe(false);
    expect(terminal.resize).toHaveBeenLastCalledWith(120, 35);
    expect(terminal.write).toHaveBeenCalledWith(Uint8Array.from([104, 101, 108, 108, 111]), expect.any(Function));
  });
  it('does not consume an input sequence when local encoding rejects a paste', async () => {
    const {socket, terminal} = await ready();
    act(() => {terminal.input?.('x'.repeat(512 * 1024 + 1)); terminal.input?.('a');});
    expect(socket.sent.filter(frame => frame.type === 'input')).toEqual([{type: 'input', seq: 1, bytes_b64: 'YQ=='}]);
  });
  it('treats a send failure as unknown and closes without replay', async () => {
    const {socket, terminal} = await ready(); socket.failSend = true;
    act(() => {terminal.input?.('a'); terminal.input?.('b');});
    expect(screen.getByText(/输入接收状态未知/)).toBeTruthy();
    expect(socket.close).toHaveBeenCalledTimes(1);
    expect(socket.sent.filter(frame => frame.type === 'input')).toHaveLength(0);
  });
  it('closes with the original gateway closed frame and always disposes locally', async () => {
    const {socket, terminal, unmount} = await ready();
    unmount();
    expect(socket.sent.at(-1)).toEqual({type: 'closed', reason: 'client_closed'});
    expect(socket.close).toHaveBeenCalled(); expect(terminal.dispose).toHaveBeenCalled();
  });
  it('ignores a late terminal receipt after effect disposal', async () => {
    let resolve: (value: unknown) => void = () => {};
    mock.api.mockReturnValue(new Promise(value => {resolve = value;}));
    const rendered = render(<AgentTerminal project="p" agent="buddy" epoch={1} />);
    const signal = mock.api.mock.calls[0][2] as AbortSignal;
    rendered.unmount(); expect(signal.aborted).toBe(true);
    await act(async () => {resolve({terminal_id: 'term_late', terminal_token: 'token'});});
    expect(Socket.instances).toHaveLength(0);
  });
  it('bounds pending renderer output and closes only this mirror without dropping ANSI silently', async () => {
    const {socket, terminal} = await ready();
    const chunk = 'x'.repeat(MAX_PENDING_OUTPUT / 2);
    act(() => {for (let index = 0; index < 4; index++) socket.frame({type: 'output', bytes_b64: btoa(chunk)});});
    expect(terminal.write).toHaveBeenCalledTimes(2);
    expect(socket.close).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/输出积压/)).toBeTruthy();
    expect(socket.sent.some(frame => frame.type === 'input')).toBe(false);
  });
  it('releases the renderer byte budget only after write callbacks complete', async () => {
    const {socket, terminal} = await ready();
    const chunk = btoa('x'.repeat(MAX_PENDING_OUTPUT / 2));
    act(() => {socket.frame({type: 'output', bytes_b64: chunk}); socket.frame({type: 'output', bytes_b64: chunk});});
    act(() => {terminal.write.mock.calls[0][1](); socket.frame({type: 'output', bytes_b64: chunk});});
    expect(terminal.write).toHaveBeenCalledTimes(3); expect(socket.close).not.toHaveBeenCalled();
  });
});
