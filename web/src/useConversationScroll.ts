import { useCallback, useLayoutEffect, useRef, useState } from 'react';

const BOTTOM_TOLERANCE = 2;

/** One scroll owner for the focused conversation; terminal geometry is unrelated. */
export function useConversationScroll({scopeKey, enabled}: {scopeKey: string; enabled: boolean}) {
  const [viewport, viewportRef] = useState<HTMLElement | null>(null);
  const [content, contentRef] = useState<HTMLDivElement | null>(null);
  const [following, setFollowing] = useState(true);
  const sticky = useRef(true);
  const requestScroll = useRef<(() => void) | null>(null);
  const cancelScroll = useRef<(() => void) | null>(null);
  const setSticky = useCallback((value: boolean) => {
    // Scroll events do not create React updates unless the intent changes.
    if (sticky.current === value) return;
    sticky.current = value; setFollowing(value);
  }, []);
  const pause = useCallback(() => {setSticky(false); cancelScroll.current?.();}, [setSticky]);
  const jumpToLatest = useCallback(() => {setSticky(true); requestScroll.current?.();}, [setSticky]);

  useLayoutEffect(() => {setSticky(true);}, [scopeKey, setSticky]);
  useLayoutEffect(() => {
    if (!enabled || !viewport || !content) return;
    let frame: number | null = null, disposed = false, pointerDown = false, touchY: number | null = null;
    const read = () => ({top: viewport.scrollTop, height: viewport.scrollHeight, viewport: viewport.clientHeight});
    let previous = read();
    const cancel = () => {if (frame !== null) cancelAnimationFrame(frame); frame = null;};
    const request = () => {
      if (disposed || !sticky.current || frame !== null) return;
      frame = requestAnimationFrame(() => {
        frame = null;
        if (disposed || !sticky.current) return;
        const bottom = Math.max(0, viewport.scrollHeight - viewport.clientHeight);
        if (Math.abs(viewport.scrollTop - bottom) > 0.5) viewport.scrollTop = bottom;
        previous = read();
      });
    };
    requestScroll.current = request; cancelScroll.current = cancel;
    const scroll = () => {
      const next = read();
      const geometryChanged = next.height !== previous.height || next.viewport !== previous.viewport;
      const upward = next.top < previous.top - 0.5;
      // Resizing can clamp scrollTop or leave a gap without any user action.
      // Stable geometry (or an active scrollbar drag) distinguishes reading.
      if (upward && (!geometryChanged || pointerDown)) pause();
      else if (!sticky.current && !geometryChanged && next.top > previous.top && next.height - next.viewport - next.top <= BOTTOM_TOLERANCE) setSticky(true);
      else if (sticky.current && geometryChanged) request();
      previous = next;
    };
    const nestedCanScrollUp = (target: EventTarget | null) => {
      let node = target instanceof Element ? target : null;
      while (node && node !== viewport) {
        if (node instanceof HTMLElement && node.scrollTop > 0 && node.scrollHeight > node.clientHeight && /auto|scroll/.test(getComputedStyle(node).overflowY)) return true;
        node = node.parentElement;
      }
      return false;
    };
    const retreat = (event: Event) => {
      if (!event.defaultPrevented && viewport.scrollTop > 0 && !nestedCanScrollUp(event.target)) pause();
    };
    const wheel = (event: WheelEvent) => {if (event.deltaY < 0) retreat(event);};
    const keydown = (event: KeyboardEvent) => {
      const target = event.target;
      if (event.isComposing || event.ctrlKey || event.metaKey || event.altKey || target instanceof Element && target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])')) return;
      if (['ArrowUp', 'PageUp', 'Home'].includes(event.key) || event.key === ' ' && event.shiftKey) retreat(event);
    };
    const touchstart = (event: TouchEvent) => {touchY = event.touches[0]?.clientY ?? null;};
    const touchmove = (event: TouchEvent) => {
      const next = event.touches[0]?.clientY ?? null;
      if (next !== null && touchY !== null && next > touchY) retreat(event);
      touchY = next;
    };
    const pointerstart = (event: PointerEvent) => {pointerDown = event.target === viewport;};
    const pointerend = () => {pointerDown = false; touchY = null;};
    viewport.addEventListener('scroll', scroll, {passive: true});
    viewport.addEventListener('wheel', wheel, {passive: true});
    viewport.addEventListener('keydown', keydown);
    viewport.addEventListener('touchstart', touchstart, {passive: true});
    viewport.addEventListener('touchmove', touchmove, {passive: true});
    viewport.addEventListener('pointerdown', pointerstart);
    document.addEventListener('pointerup', pointerend);
    document.addEventListener('pointercancel', pointerend);
    const observer = new ResizeObserver(request);
    observer.observe(viewport); observer.observe(content);
    request();
    return () => {
      disposed = true; cancel(); observer.disconnect();
      viewport.removeEventListener('scroll', scroll);
      viewport.removeEventListener('wheel', wheel);
      viewport.removeEventListener('keydown', keydown);
      viewport.removeEventListener('touchstart', touchstart);
      viewport.removeEventListener('touchmove', touchmove);
      viewport.removeEventListener('pointerdown', pointerstart);
      document.removeEventListener('pointerup', pointerend);
      document.removeEventListener('pointercancel', pointerend);
      if (requestScroll.current === request) requestScroll.current = null;
      if (cancelScroll.current === cancel) cancelScroll.current = null;
    };
  }, [viewport, content, enabled, scopeKey, pause, setSticky]);

  return {viewportRef, contentRef, following, pause, jumpToLatest};
}
