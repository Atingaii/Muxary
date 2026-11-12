import { useEffect, useRef, useState } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { api, projectPath, row, text, type Row } from './model';
import '@xterm/xterm/css/xterm.css';

export const MAX_PENDING_OUTPUT = 2 * 1024 * 1024;

export function terminalGeometry(frame: Row): {columns: number; rows: number} | null {
  const geometry = frame.type === 'open' ? row(frame.geometry) : frame;
  const columns = Number(geometry.columns), rows = Number(geometry.rows);
  return Number.isInteger(columns) && Number.isInteger(rows) && columns > 0 && rows > 0
    ? {columns, rows} : null;
}

export function inputBase64(data: string): string {
  const bytes = new TextEncoder().encode(data);
  // Avoid a spread-argument stack overflow on a large paste. Keep one native
  // input event intact: splitting can bisect UTF-8 or a terminal key sequence.
  if (bytes.length > 512 * 1024) throw new Error('单次终端输入过大，请分次粘贴');
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

export function AgentTerminal({project, agent, epoch}: {project: string; agent: string; epoch: unknown}) {
  const element = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState('正在连接原生终端…');
  const [generation, setGeneration] = useState(0);
  useEffect(() => {
    if (!element.current) return;
    setStatus('正在连接原生终端…');
    const terminal = new XTerm({fontSize: 12, fontFamily: '"SFMono-Regular", Consolas, monospace', cursorBlink: true,
      theme: {background: '#15181f', foreground: '#d9dfe9'}, scrollback: 2000, convertEol: true});
    const fit = new FitAddon(); terminal.loadAddon(fit); terminal.open(element.current); fit.fit();
    let disposed = false, outputStopped = false, pendingOutput = 0, socket: WebSocket | undefined, seq = 0, opened = false, resizePolicy = '', endReason = '';
    const stopOutput = (reason: string) => {
      outputStopped = true; opened = false; endReason = reason; setStatus(reason); socket?.close();
    };
    const controller = new AbortController();
    const resize = new ResizeObserver(() => {
      if (disposed || resizePolicy === 'fixed_source') return;
      fit.fit();
      if (opened && resizePolicy === 'client' && socket?.readyState === WebSocket.OPEN)
        socket.send(JSON.stringify({type: 'resize', columns: terminal.cols, rows: terminal.rows}));
    }); resize.observe(element.current);
    const input = terminal.onData(data => {
      if (opened && socket?.readyState === WebSocket.OPEN) {
        let bytes: string;
        try {bytes = inputBase64(data);}
        catch (error) {setStatus(error instanceof Error ? error.message : '终端输入未发送'); return;}
        try { socket.send(JSON.stringify({type: 'input', seq: ++seq, bytes_b64: bytes})); }
        catch {
          opened = false; endReason = '终端输入接收状态未知；连接已关闭，不会重放输入';
          setStatus(endReason); socket.close();
        }
      }
    });
    // Each reconnect obtains a new handle with full history. Never replay input
    // whose acknowledgement is unknown, and never resize the shared Agent pane.
    api(projectPath(project, '/terminals'), {target: {kind: 'agent', agent}, namespace_epoch: epoch,
      geometry: {columns: terminal.cols, rows: terminal.rows}}, controller.signal).then(handle => {
      if (disposed) return;
      const id = text(handle.terminal_id), token = text(handle.terminal_token) || text(handle.token);
      if (!id || !token) throw new Error('网关未返回可用的终端句柄');
      socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/terminals/${encodeURIComponent(id)}/ws`);
      socket.onopen = () => {
        if (disposed) {socket?.close(); return;}
        socket?.send(JSON.stringify({type: 'open', terminal_id: id, token}));
      };
      socket.onmessage = event => {
        if (disposed || outputStopped) return;
        try {
          const frame = row(JSON.parse(event.data));
          if (frame.type === 'open' || frame.type === 'geometry') {
            resizePolicy = text(frame.resize_policy) || resizePolicy;
            const geometry = terminalGeometry(frame);
            // Agent panes are desktop-owned. Match their grid locally rather
            // than reflowing cursor-addressed snapshots into a different grid.
            if (resizePolicy === 'fixed_source' && geometry)
              terminal.resize(geometry.columns, geometry.rows);
          }
          if (frame.type === 'open') { opened = true; seq = Number(frame.last_input_seq) || 0; setStatus('原生终端 · 输入直接交给当前 CLI'); }
          if (frame.type === 'output') {
            // The gateway explicitly preserves this ANSI compatibility stream;
            // fixed_source geometry keeps it correct without a second renderer.
            const encoded = text(frame.bytes_b64);
            if (encoded.length > Math.ceil(MAX_PENDING_OUTPUT / 3) * 4) {
              stopOutput('终端输出过大；已关闭本页镜像。原 CLI 继续运行，可手动重连；不会重放输入。'); return;
            }
            const bytes = Uint8Array.from(atob(encoded), char => char.charCodeAt(0));
            if (pendingOutput + bytes.byteLength > MAX_PENDING_OUTPUT) {
              stopOutput('终端输出积压；已关闭本页镜像。原 CLI 继续运行，可手动重连；不会重放输入。'); return;
            }
            pendingOutput += bytes.byteLength;
            try {terminal.write(bytes, () => {pendingOutput -= bytes.byteLength;});}
            catch {stopOutput('终端渲染失败；已关闭本页镜像，可手动重连；不会重放输入。');}
          }
          if (frame.type === 'error') {opened = false; endReason = `终端错误：${text(frame.message) || text(frame.code)}`; setStatus(endReason);}
          if (frame.type === 'closed') { opened = false; endReason = `终端已断开：${text(frame.reason)}`; setStatus(endReason); }
        } catch {
          opened = false; endReason = '终端协议错误；输入未重放'; setStatus(endReason); socket?.close();
        }
      };
      socket.onerror = () => {opened = false; endReason = '终端连接失败；可手动重连，不会重放输入'; if (!disposed) setStatus(endReason);};
      socket.onclose = () => {opened = false; if (!disposed) setStatus(endReason || '终端连接已关闭；不会重放输入');};
    }).catch(error => {if (!disposed) setStatus(error instanceof Error ? error.message : '终端不可用');});
    return () => {
      disposed = true; controller.abort();
      try {
        if (opened && socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({type: 'closed', reason: 'client_closed'}));
      } catch { /* A broken transport cannot acknowledge closure; never replay. */ }
      opened = false; socket?.close(); input.dispose(); resize.disconnect(); terminal.dispose();
    };
  }, [project, agent, epoch, generation]);
  return <section className="terminal-pane" aria-label="原生终端">
    <div className="terminal-status"><span>{status}</span><button onClick={() => setGeneration(n => n + 1)}>重新连接</button></div>
    <div ref={element} className="terminal-surface" style={{overflow: 'auto'}} />
  </section>;
}
