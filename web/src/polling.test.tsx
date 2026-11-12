// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useSerialPoll } from './polling';
const deferred = () => {let resolve!: () => void; const promise = new Promise<void>(done => {resolve = done;}); return {promise, resolve};};
const visibility = (value: 'visible' | 'hidden') => {Object.defineProperty(document, 'visibilityState', {configurable: true, value}); document.dispatchEvent(new Event('visibilitychange'));};
beforeEach(() => {vi.useFakeTimers(); visibility('visible');});
afterEach(() => {cleanup(); vi.useRealTimers();});
describe('completion-based reads, one factor at a time', () => {
  it('does not overlap slow reads, unlike a fixed interval under the same latency', async () => {
    const first = deferred(), read = vi.fn(() => first.promise);
    renderHook(() => useSerialPoll(read, 100, true));
    const intervalRead = vi.fn(() => first.promise), interval = setInterval(intervalRead, 100);
    await act(async () => {await vi.advanceTimersByTimeAsync(500);});
    expect(read).toHaveBeenCalledTimes(1); expect(intervalRead).toHaveBeenCalledTimes(5);
    clearInterval(interval);
    await act(async () => {first.resolve(); await Promise.resolve();});
    await act(async () => {await vi.advanceTimersByTimeAsync(99);}); expect(read).toHaveBeenCalledTimes(1);
    await act(async () => {await vi.advanceTimersByTimeAsync(1);}); expect(read).toHaveBeenCalledTimes(2);
  });
  it('aborts when hidden and waits for the old reader to settle before resuming', async () => {
    const first = deferred(), read = vi.fn((_signal: AbortSignal) => first.promise);
    renderHook(() => useSerialPoll(read, 100, true));
    await act(async () => {visibility('hidden');}); expect(read.mock.calls[0][0].aborted).toBe(true);
    await act(async () => {visibility('visible'); await vi.advanceTimersByTimeAsync(1000);}); expect(read).toHaveBeenCalledTimes(1);
    await act(async () => {first.resolve(); await Promise.resolve();}); expect(read).toHaveBeenCalledTimes(2);
  });
  it('starts nothing while hidden, then starts one fresh read with no timer backlog', async () => {
    visibility('hidden'); const read = vi.fn(async () => {});
    renderHook(() => useSerialPoll(read, 100, true));
    await act(async () => {await vi.advanceTimersByTimeAsync(1000);}); expect(read).not.toHaveBeenCalled();
    await act(async () => {visibility('visible');}); expect(read).toHaveBeenCalledTimes(1);
    await act(async () => {visibility('hidden'); await vi.advanceTimersByTimeAsync(1000);}); expect(read).toHaveBeenCalledTimes(1);
  });
  it('does not keep polling after disable/unmount or restart an aborted old effect', async () => {
    const first = deferred(), read = vi.fn((_signal: AbortSignal) => first.promise);
    const hook = renderHook(({enabled}) => useSerialPoll(read, 100, enabled), {initialProps: {enabled: true}});
    hook.rerender({enabled: false}); expect(read.mock.calls[0][0].aborted).toBe(true);
    await act(async () => {first.resolve(); await vi.advanceTimersByTimeAsync(1000);}); expect(read).toHaveBeenCalledTimes(1);
    hook.rerender({enabled: true}); expect(read).toHaveBeenCalledTimes(2); hook.unmount();
    await act(async () => {visibility('hidden'); visibility('visible'); await vi.advanceTimersByTimeAsync(1000);}); expect(read).toHaveBeenCalledTimes(2);
  });
  it('lets a handled read error settle before a later fresh read', async () => {
    const read = vi.fn(async () => {throw new Error('reader owns error');});
    renderHook(() => useSerialPoll(read, 100, true));
    await act(async () => {await vi.advanceTimersByTimeAsync(100);}); expect(read).toHaveBeenCalledTimes(2);
  });
});
