import { useEffect } from 'react';
const hidden = () => document.visibilityState === 'hidden';

// A poll waits for the previous read to settle. Hiding the page cancels its
// current read; resuming starts one fresh read, not a backlog of timer ticks.
export function useSerialPoll(read: (signal: AbortSignal) => Promise<unknown>, delay: number, enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    let stopped = false, resumeRequested = false, timer: ReturnType<typeof setTimeout> | undefined, controller: AbortController | undefined;
    const run = async () => {
      if (stopped || hidden()) return;
      const current = new AbortController(); controller = current;
      try { await read(current.signal); }
      catch { /* Each reader owns its user-facing error state. */ }
      finally {
        if (controller === current) controller = undefined;
        if (!stopped && !hidden()) {
          if (resumeRequested) {resumeRequested = false; void run();}
          else if (!current.signal.aborted) timer = setTimeout(run, delay);
        }
      }
    };
    const visibility = () => {
      clearTimeout(timer);
      if (hidden()) {resumeRequested = false; controller?.abort();}
      else if (!controller) void run();
      else resumeRequested = true;
    };
    document.addEventListener('visibilitychange', visibility);
    void run();
    return () => {stopped = true; clearTimeout(timer); controller?.abort(); document.removeEventListener('visibilitychange', visibility);};
  }, [read, delay, enabled]);
}
