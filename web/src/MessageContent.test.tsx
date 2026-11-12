// @vitest-environment jsdom
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render } from '@testing-library/react';
import { MessageContent } from './MessageContent';
const calls = vi.hoisted(() => ({markdown: 0, user: 0}));
vi.mock('./vendor/agent-elements/markdown', () => ({Markdown: ({content}: {content: string}) => {calls.markdown++; return <div data-testid="markdown">{content}</div>;}}));
vi.mock('./vendor/agent-elements/user-message', () => ({UserMessage: ({message}: {message: {parts: {text: string}[]}}) => {calls.user++; return <div data-testid="user">{message.parts[0].text}</div>;}}));
afterEach(() => {cleanup(); calls.markdown = 0; calls.user = 0;});
const toggle = async (details: HTMLDetailsElement, open: boolean) => {await act(async () => {details.open = open; fireEvent(details, new Event('toggle'));});};
describe('large content is complete, but hydration is demand-driven', () => {
  it.each([1, 10])('%i MiB fixture skips Markdown; explicit expansion reaches every original code unit', async size => {
    const content = '开头\n' + 'x'.repeat(size * 1024 * 1024) + '\n末尾';
    const {container} = render(<MessageContent id="large" content={content}/>);
    expect(calls.markdown).toBe(0); expect(calls.user).toBe(0);
    expect(container.querySelector('.message-preview')!.textContent).toHaveLength(2001);
    expect(container.querySelector('.message-full-text')).toBeNull();
    const details = container.querySelector('details')!;
    await toggle(details, true); expect(container.querySelector('.message-full-text')!.textContent).toBe(content);
    await toggle(details, false); expect(container.querySelector('.message-full-text')).toBeNull();
  });
  it('does not reparse unchanged message primitives when the parent polls again', () => {
    const hook = render(<MessageContent id="one" content="small result"/>);
    hook.rerender(<MessageContent id="one" content="small result"/>); expect(calls.markdown).toBe(1);
    hook.rerender(<MessageContent id="one" content="changed"/>); expect(calls.markdown).toBe(2);
  });
  it('retains the existing role-specific small content components', () => {
    render(<><MessageContent id="u" content="user body" user/><MessageContent id="a" content="agent body"/></>);
    expect(calls.user).toBe(1); expect(calls.markdown).toBe(1);
  });
  it('does not mount the full body under a closed replacement details after long→short→long', async () => {
    const content = 'x'.repeat(13000), hook = render(<MessageContent id="same" content={content}/>);
    await toggle(hook.container.querySelector('details')!, true);
    hook.rerender(<MessageContent id="same" content="short"/>);
    hook.rerender(<MessageContent id="same" content={content}/>);
    expect(hook.container.querySelector('details')!.open).toBe(false);
    expect(hook.container.querySelector('.message-full-text')).toBeNull();
    await toggle(hook.container.querySelector('details')!, true);
    expect(hook.container.querySelector('.message-full-text')!.textContent).toBe(content);
  });
});
