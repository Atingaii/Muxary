// @vitest-environment jsdom
import { StrictMode } from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useConversationScroll } from './useConversationScroll';

type Geometry = {height: number; viewport: number; top: number; writes: number[]};
let geometry: Geometry;
let frames: Map<number, FrameRequestCallback>;
let frameId: number;
const observers: {callback: ResizeObserverCallback; targets: Set<Element>; disconnected: boolean}[] = [];
function flushFrame() {
  act(() => {const callbacks = [...frames.values()]; frames.clear(); callbacks.forEach(callback => callback(0));});
}
function resize() {
  act(() => observers.filter(observer => !observer.disconnected).forEach(observer => observer.callback([], {} as ResizeObserver)));
}
function scroll(top: number) {geometry.top = top; fireEvent.scroll(screen.getByRole('region', {name: 'conversation'}));}
function Harness({scope = 'p/a/1/tasks', enabled = true}: {scope?: string; enabled?: boolean}) {
  const {viewportRef, contentRef, following, pause, jumpToLatest} = useConversationScroll({scopeKey: scope, enabled});
  return <><output>{following ? 'following' : 'reading'}</output><button onClick={pause}>pause</button><button onClick={jumpToLatest}>latest</button>{enabled && <section aria-label="conversation" ref={node => {
    if (node) {
      Object.defineProperties(node, {
        scrollHeight: {configurable: true, get: () => geometry.height},
        clientHeight: {configurable: true, get: () => geometry.viewport},
        scrollTop: {configurable: true, get: () => geometry.top, set: (value: number) => {geometry.top = Math.max(0, Math.min(value, geometry.height - geometry.viewport)); geometry.writes.push(geometry.top);}},
      });
    }
    viewportRef(node);
  }}><div ref={contentRef}><p>Message</p><textarea aria-label="editable"/><div data-testid="nested" tabIndex={0}>nested scroll</div></div></section>}</>;
}
function mount() {return render(<StrictMode><Harness/></StrictMode>);}

beforeEach(() => {
  geometry = {height: 1200, viewport: 400, top: 0, writes: []}; frames = new Map(); frameId = 0; observers.length = 0;
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {frames.set(++frameId, callback); return frameId;});
  vi.stubGlobal('cancelAnimationFrame', (id: number) => frames.delete(id));
  vi.stubGlobal('ResizeObserver', class {
    value: typeof observers[number];
    constructor(callback: ResizeObserverCallback) {this.value = {callback, targets: new Set(), disconnected: false}; observers.push(this.value);}
    observe(target: Element) {this.value.targets.add(target);}
    unobserve(target: Element) {this.value.targets.delete(target);}
    disconnect() {this.value.disconnected = true; this.value.targets.clear();}
  });
});
afterEach(() => {cleanup(); vi.unstubAllGlobals();});

describe('conversation owns one sticky scrollport, not the terminal or page', () => {
  it('keeps following when opening and dragging a terminal changes viewport height', () => {
    mount(); flushFrame(); expect(geometry.top).toBe(800);
    geometry.viewport = 220; fireEvent.scroll(screen.getByRole('region', {name: 'conversation'})); resize(); flushFrame();
    expect(geometry.top).toBe(980); expect(screen.getByText('following')).toBeTruthy();
    geometry.viewport = 300; resize(); flushFrame(); expect(geometry.top).toBe(900);
  });
  it('does not move a reader when viewport or content dimensions change', () => {
    mount(); flushFrame(); scroll(500); expect(screen.getByText('reading')).toBeTruthy();
    geometry.writes.length = 0; geometry.viewport = 200; geometry.height = 1500; resize(); flushFrame();
    expect(geometry.top).toBe(500); expect(geometry.writes).toEqual([]);
  });
  it('follows async content growth without needing a React content key', () => {
    mount(); flushFrame(); geometry.height = 1700; resize(); flushFrame();
    expect(geometry.top).toBe(1300); expect(screen.getByText('following')).toBeTruthy();
  });
  it('coalesces repeated observer deliveries into one frame and one scroll write', () => {
    mount(); flushFrame(); geometry.writes.length = 0; geometry.height = 1400;
    resize(); resize(); resize(); expect(frames.size).toBe(1); flushFrame();
    expect(geometry.writes).toEqual([1000]);
  });
  it('does not mistake a geometry-only scrollTop clamp for the user reading upward', () => {
    mount(); flushFrame(); geometry.viewport = 700; geometry.top = 500;
    fireEvent.scroll(screen.getByRole('region', {name: 'conversation'})); resize(); flushFrame();
    expect(screen.getByText('following')).toBeTruthy();
    geometry.viewport = 300; resize(); flushFrame(); expect(geometry.top).toBe(900);
  });
  it('cancels a pending resize follow before upward wheel scroll takes effect', () => {
    mount(); flushFrame(); geometry.viewport = 200; resize(); expect(frames.size).toBe(1);
    fireEvent.wheel(screen.getByRole('region', {name: 'conversation'}), {deltaY: -30});
    scroll(770); flushFrame(); expect(geometry.top).toBe(770); expect(screen.getByText('reading')).toBeTruthy();
    geometry.height = 1500; resize(); flushFrame(); expect(geometry.top).toBe(770);
  });
  it('respects a scrollbar drag upward even when viewport geometry changes in the same event', () => {
    mount(); flushFrame(); const viewport = screen.getByRole('region', {name: 'conversation'});
    fireEvent.pointerDown(viewport); geometry.viewport = 220; scroll(600); resize(); flushFrame();
    expect(screen.getByText('reading')).toBeTruthy(); expect(geometry.top).toBe(600);
    fireEvent.pointerUp(document);
  });
  it.each(['ArrowUp', 'PageUp', 'Home', ' '])('pauses on upward keyboard intent %j before the browser scrolls', key => {
    mount(); flushFrame(); geometry.height = 1600; resize();
    fireEvent.keyDown(screen.getByRole('region', {name: 'conversation'}), {key, shiftKey: key === ' '});
    flushFrame(); expect(geometry.top).toBe(800); expect(screen.getByText('reading')).toBeTruthy();
  });
  it('does not treat textarea editing or IME confirmation as conversation scroll intent', () => {
    mount(); flushFrame(); fireEvent.keyDown(screen.getByRole('textbox'), {key: 'Home'});
    fireEvent.keyDown(screen.getByRole('region', {name: 'conversation'}), {key: 'ArrowUp', isComposing: true});
    expect(screen.getByText('following')).toBeTruthy();
  });
  it('does not steal wheel or key scrolling from an independently scrollable message detail', () => {
    mount(); flushFrame(); const nested = screen.getByTestId('nested'); nested.style.overflowY = 'auto';
    Object.defineProperties(nested, {scrollTop: {value: 100, configurable: true}, scrollHeight: {value: 600, configurable: true}, clientHeight: {value: 200, configurable: true}});
    fireEvent.wheel(nested, {deltaY: -30}); fireEvent.keyDown(nested, {key: 'PageUp'});
    expect(screen.getByText('following')).toBeTruthy();
  });
  it('pauses on touch movement toward earlier messages, not merely tapping a message', () => {
    mount(); flushFrame(); const viewport = screen.getByRole('region', {name: 'conversation'});
    fireEvent.touchStart(viewport, {touches: [{clientY: 100}]}); expect(screen.getByText('following')).toBeTruthy();
    geometry.viewport = 200; resize(); fireEvent.touchMove(viewport, {touches: [{clientY: 130}]});
    flushFrame(); expect(geometry.top).toBe(800); expect(screen.getByText('reading')).toBeTruthy();
  });
  it('re-enters following only after scrolling back to the actual bottom or explicitly jumping', () => {
    mount(); flushFrame(); scroll(500); scroll(750); expect(screen.getByText('reading')).toBeTruthy();
    scroll(799); expect(screen.getByText('following')).toBeTruthy();
    scroll(500); fireEvent.click(screen.getByText('latest')); flushFrame();
    expect(geometry.top).toBe(800); expect(screen.getByText('following')).toBeTruthy();
  });
  it('preserves explicit pause while earlier records are prepended and the scrollport is resized', () => {
    mount(); flushFrame(); fireEvent.click(screen.getByText('pause')); geometry.writes.length = 0;
    geometry.height = 2200; geometry.viewport = 200; resize(); flushFrame();
    expect(screen.getByText('reading')).toBeTruthy(); expect(geometry.writes).toEqual([]);
  });
  it('keeps reading intent through canvas unmount/remount but resets for a different conversation scope', () => {
    const app = mount(); flushFrame(); scroll(500);
    app.rerender(<StrictMode><Harness enabled={false}/></StrictMode>); expect(frames.size).toBe(0);
    app.rerender(<StrictMode><Harness/></StrictMode>); geometry.writes.length = 0; resize(); flushFrame();
    expect(screen.getByText('reading')).toBeTruthy(); expect(geometry.writes).toEqual([]);
    app.rerender(<StrictMode><Harness scope="p/other/1/tasks"/></StrictMode>); flushFrame();
    expect(geometry.top).toBe(800); expect(screen.getByText('following')).toBeTruthy();
  });
  it('starts one observer for the active two DOM nodes and leaves no callback or frame after unmount', () => {
    const app = mount(); flushFrame(); const active = observers.filter(observer => !observer.disconnected);
    expect(active).toHaveLength(1); expect(active[0].targets.size).toBe(2);
    geometry.height = 1400; resize(); expect(frames.size).toBe(1); app.unmount();
    expect(frames.size).toBe(0); expect(observers.every(observer => observer.disconnected)).toBe(true);
    geometry.writes.length = 0; active[0].callback([], {} as ResizeObserver); flushFrame(); expect(geometry.writes).toEqual([]);
  });
  it('does not write scrollTop again for unchanged dimensions at the bottom', () => {
    mount(); flushFrame(); geometry.writes.length = 0; resize(); flushFrame();
    expect(geometry.writes).toEqual([]);
  });

  it('does not confuse a held click inside message content with a scrollbar drag during content collapse', () => {
    mount(); flushFrame(); fireEvent.pointerDown(screen.getByText('Message'));
    geometry.height = 800; geometry.top = 400; fireEvent.scroll(screen.getByRole('region', {name: 'conversation'})); resize(); flushFrame();
    expect(screen.getByText('following')).toBeTruthy(); fireEvent.pointerUp(document);
  });

});
