// @vitest-environment jsdom
import React, { StrictMode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { App } from './App';
vi.mock('./vendor/agent-elements/markdown', () => ({Markdown: ({content}: {content: string}) => <div>{content}</div>}));
const terminalMounts = vi.hoisted(() => [] as {project: string; agent: string; epoch: unknown}[]);
vi.mock('./Terminal', () => ({AgentTerminal: (props: {project: string; agent: string; epoch: unknown}) => {terminalMounts.push(props); return <div>terminal</div>;}}));
vi.mock('./AgentCanvas', () => ({AgentCanvas: ({onSelect, onFocus, onTerminal}: {onSelect: (agent: string) => void; onFocus: (agent: string) => void; onTerminal: (agent: string) => void}) => <div aria-label="测试画布"><button onClick={() => onSelect('coder')}>选择 coder</button><button onClick={() => onFocus('coder')}>专注 coder</button><button onClick={() => onTerminal('coder')}>接管 coder</button></div>}));
const jobs: Record<string, unknown>[] = [];
let agents: Record<string, unknown>[] = [{name: 'buddy', provider: 'codebuddy'}];
let namespaceEpoch = 1;
let readOverride: ((path: string, options?: RequestInit) => Promise<Response> | undefined) | undefined;
let nativeItems: Record<string, unknown>[] = [];
let postMode = 'ok', readFailure = false, conversationFailure = false;
let sends: {path: string; body: Record<string, unknown>}[] = [];
let failAfterSubmit = false, holdView = false;
const json = (value: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(value), {status}));
const fetcher = vi.fn((path: string, options?: RequestInit) => {
  const overridden = readOverride?.(path, options); if (overridden) return overridden;
  const body = options?.body ? JSON.parse(String(options.body)) : undefined;
  if (path === '/api/session') return json({authenticated: true});
  if (path === '/api/projects') return json({projects: [{id: 'p', display_name: 'Fixture project', root: '/fixture'}]});
  if (body && path.includes('/jobs')) {
    sends.push({path, body});
    if (postMode === 'lost') return Promise.reject(new Error('network lost'));
    if (postMode === 'denied') return json({error: 'denied'}, 409);
    if (failAfterSubmit) readFailure = true;
    return json({job_id: 'job_new', status: 'queued'}, 202);
  }
  if (readFailure && path.includes('/jobs')) return json({error: 'read failed'}, 503);
  if (path.endsWith('/view') && holdView) return new Promise<Response>(() => {});
  if (path.endsWith('/view')) return json({view: {agents, namespace: {epoch: namespaceEpoch}}});
  if (path.endsWith('/jobs')) return json({jobs});
  if (path.includes('/conversation')) return conversationFailure ? json({error: 'stale namespace epoch'}, 409) : json({conversation: {items: nativeItems}});
  return json({});
});
beforeEach(() => {
  Object.defineProperty(document, 'visibilityState', {configurable: true, value: 'visible'});
  terminalMounts.length = 0; readOverride = undefined; namespaceEpoch = 1;
  jobs.length = 0; sends = []; postMode = 'ok'; readFailure = false; failAfterSubmit = false; conversationFailure = false; holdView = false;
  agents = [{name: 'buddy', provider: 'codebuddy'}];
  nativeItems = [];
  localStorage.clear(); sessionStorage.clear();
  vi.stubGlobal('fetch', fetcher); fetcher.mockClear();
  vi.stubGlobal('matchMedia', () => ({matches: false}));
  vi.stubGlobal('ResizeObserver', class {observe() {} unobserve() {} disconnect() {}});
  Element.prototype.scrollIntoView = vi.fn();
  HTMLDialogElement.prototype.showModal = function () {this.setAttribute('open', '');};
  HTMLDialogElement.prototype.close = function () {this.removeAttribute('open');};
});
afterEach(() => {cleanup(); vi.restoreAllMocks();});
async function ready() {render(<StrictMode><App /></StrictMode>); await waitFor(() => expect(screen.getByRole('textbox', {name: /给 buddy/}).hasAttribute('disabled')).toBe(false)); return screen.getByRole('textbox', {name: /给 buddy/});}
describe('real controlled composer and mutation evidence', () => {
  it('opens a project dialog without starting anything and does not stack Command over it', async () => {
    await ready(); fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    expect(screen.getByRole('dialog', {name: '打开项目'})).toBeTruthy();
    fireEvent.keyDown(window, {key: 'k', ctrlKey: true});
    expect(document.querySelector('.command-dialog')!.hasAttribute('open')).toBe(false);
    fireEvent.keyDown(window, {key: 'Escape', isComposing: true});
    expect(screen.getByRole('dialog', {name: '打开项目'})).toBeTruthy();
    fireEvent.keyDown(window, {key: 'Escape'});
    expect(document.querySelector('.project-dialog')!.hasAttribute('open')).toBe(false);
    expect(fetcher.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(false);
  });
  it('opens a new CCB project only on submit and joins duplicate clicks', async () => {
    await ready(); let finish!: (response: Response) => void;
    readOverride = path => path === '/api/projects/open' ? new Promise(resolve => {finish = resolve;}) : path === '/api/projects/new/view' ? json({view: {agents: [{name: 'new-agent', workspace_path: '/new'}], namespace: {epoch: 5}}}) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/new'}});
    const form = document.querySelector('.project-dialog form')!;
    fireEvent.submit(form); fireEvent.submit(form);
    expect(fetcher.mock.calls.filter(([path]) => path === '/api/projects/open')).toHaveLength(1);
    const request = fetcher.mock.calls.find(([path]) => path === '/api/projects/open')![1]!;
    expect(JSON.parse(String(request.body))).toEqual({path: '/new'});
    expect(screen.getByText(/关闭窗口不会取消/)).toBeTruthy();
    finish(new Response(JSON.stringify({project_id: 'new', root: '/new', status: 'ready'})));
    await screen.findByRole('textbox', {name: /给 new-agent/});
    expect(screen.getByRole('navigation').querySelector('.project-button.selected')?.textContent).toBe('new');
    expect(sends).toHaveLength(0);
  });
  it('keeps an unknown project-open outcome visible and never automatically resends', async () => {
    await ready(); readOverride = path => path === '/api/projects/open' ? json({error: 'startup_timeout'}, 504) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/slow'}});
    fireEvent.click(screen.getByRole('button', {name: '通过 CCB 打开'}));
    await screen.findByText(/打开结果未确认/);
    expect((screen.getByLabelText('本机项目目录') as HTMLInputElement).value).toBe('/slow');
    expect(screen.getByRole('button', {name: '通过 CCB 打开'}).hasAttribute('disabled')).toBe(true);
    fireEvent.submit(document.querySelector('.project-dialog form')!);
    fireEvent.click(screen.getByRole('button', {name: '查看已挂载项目（列表自动只读刷新）'}));
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(fetcher.mock.calls.filter(([path]) => path === '/api/projects/open')).toHaveLength(1);
    expect(screen.getByRole('textbox', {name: /给 buddy/})).toBeTruthy();
  });
  it('Command opens project confirmation without starting providers', async () => {
    await ready(); fireEvent.click(screen.getByRole('button', {name: '打开快速切换'}));
    fireEvent.change(screen.getByRole('combobox', {name: '跳转与操作'}), {target: {value: '打开本机项目目录'}});
    fireEvent.keyDown(screen.getByRole('combobox', {name: '跳转与操作'}), {key: 'Enter'});
    await screen.findByRole('dialog', {name: '打开项目'});
    expect(document.querySelector('.command-dialog')!.hasAttribute('open')).toBe(false);
    expect(fetcher.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(false);
  });
  it('does not let an older project-list response remove a newly opened project', async () => {
    let oldList!: (response: Response) => void;
    readOverride = path => path === '/api/projects' ? new Promise(resolve => {oldList = resolve;}) : path === '/api/projects/open' ? json({project_id: 'new', root: '/new'}) : undefined;
    render(<StrictMode><App /></StrictMode>);
    fireEvent.click(await screen.findByRole('button', {name: '打开项目'}));
    await waitFor(() => expect(oldList).toBeTypeOf('function'));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/new'}});
    fireEvent.click(screen.getByRole('button', {name: '通过 CCB 打开'}));
    await screen.findByRole('textbox', {name: /给 buddy/});
    oldList(new Response(JSON.stringify({projects: [{id: 'p', root: '/fixture', display_name: 'Old list'}]})));
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(screen.getByRole('navigation').querySelector('.project-button.selected')?.textContent).toBe('new');
    expect(screen.queryByRole('button', {name: 'Old list'})).toBeNull();
  });
  it('preserves an invalid path for correction without changing the active project', async () => {
    await ready(); readOverride = path => path === '/api/projects/open' ? json({error: 'project_directory_not_found'}, 400) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/missing'}});
    fireEvent.click(screen.getByRole('button', {name: '通过 CCB 打开'}));
    await screen.findByText('project_directory_not_found');
    expect((screen.getByLabelText('本机项目目录') as HTMLInputElement).value).toBe('/missing');
    expect(screen.getByRole('navigation').querySelector('.project-button.selected')?.textContent).toBe('Fixture project');
  });
  it('does not steal a later Agent selection when a closed project dialog finishes', async () => {
    agents.push({name: 'coder', provider: 'codex'}); await ready(); let finish!: (response: Response) => void;
    readOverride = path => path === '/api/projects/open' ? new Promise(resolve => {finish = resolve;}) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/new'}});
    fireEvent.click(screen.getByRole('button', {name: '通过 CCB 打开'}));
    fireEvent.click(screen.getByRole('button', {name: '关闭打开项目'}));
    fireEvent.click(screen.getByRole('button', {name: /^coder/}));
    await screen.findByRole('textbox', {name: /给 coder/});
    finish(new Response(JSON.stringify({project_id: 'new', root: '/new'})));
    await screen.findByRole('button', {name: 'new'});
    expect(screen.getByRole('textbox', {name: /给 coder/})).toBeTruthy();
  });
  it('does not steal a later selection even when the user returns to the original Agent (ABA)', async () => {
    agents.push({name: 'coder', provider: 'codex'}); await ready(); let finish!: (response: Response) => void;
    readOverride = path => path === '/api/projects/open' ? new Promise(resolve => {finish = resolve;}) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '打开项目'}));
    fireEvent.change(screen.getByLabelText('本机项目目录'), {target: {value: '/new'}});
    fireEvent.click(screen.getByRole('button', {name: '通过 CCB 打开'}));
    fireEvent.click(screen.getByRole('button', {name: '关闭打开项目'}));
    fireEvent.click(screen.getByRole('button', {name: /^coder/}));
    await screen.findByRole('textbox', {name: /给 coder/});
    fireEvent.click(screen.getByRole('button', {name: /^buddy/}));
    await screen.findByRole('textbox', {name: /给 buddy/});
    finish(new Response(JSON.stringify({project_id: 'new', root: '/new'})));
    await screen.findByRole('button', {name: 'new'});
    expect(screen.getByRole('navigation').querySelector('.project-button.selected')?.textContent).toBe('Fixture project');
  });
  it('shows actual directory groups and marks only a known shared directory', async () => {
    agents = [{name: 'buddy', workspace_path: '/one/tree'}, {name: 'coder', workspace_path: '/two/tree'}, {name: 'other', workspace_path: '/one/tree'}, {name: 'unknown'}];
    await ready();
    const first = screen.getByRole('group', {name: '工作目录 /one/tree'});
    expect(first.textContent).toContain('共享'); expect(first.textContent).toContain('other');
    expect(first.querySelector('.workspace-group-label span')?.textContent).toBe('/one/tree');
    expect(screen.getByRole('group', {name: '工作目录 /two/tree'}).querySelector('.workspace-group-label span')?.textContent).toBe('/two/tree');
    expect(screen.getByRole('group', {name: '工作目录 /two/tree'}).textContent).not.toContain('共享');
    expect(screen.getByRole('group', {name: '工作目录 待确认'}).textContent).not.toContain('共享');
  });
  it('displays the canonical flattened CCB project-view workspace without guessing the project root', async () => {
    agents = [{name: 'buddy', provider: 'codebuddy', workspace_path: '/fixture/agent-worktree'}];
    await ready(); expect(screen.getByRole('button', {name: 'agent-worktree'})).toBeTruthy();
    expect(screen.queryByRole('button', {name: '目录待确认'})).toBeNull();
  });
  it('a pending manual refresh is not duplicated when switching hydration views', async () => {
    await ready(); let finish!: (value: Response) => void;
    readOverride = path => path.endsWith('/view') ? new Promise(resolve => {finish = resolve;}) : undefined;
    const before = fetcher.mock.calls.filter(([path]) => path.endsWith('/view')).length;
    fireEvent.click(screen.getByRole('button', {name: '刷新状态'}));
    fireEvent.click(screen.getByRole('button', {name: /画布/}));
    await screen.findByRole('button', {name: '选择 coder'});
    expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/view')).length - before).toBe(1);
    finish(new Response(JSON.stringify({view: {agents, namespace: {epoch: 1}}})));
  });
  it('Command does not rank an unrelated fuzzy path ahead of an Agent name', async () => {
    agents.push({name: 'coder', provider: 'codex'});
    readOverride = path => path === '/api/projects' ? json({projects: [{id: 'p', display_name: 'Fixture project', root: '/path/code-review/project'}]}) : undefined;
    await ready(); fireEvent.click(screen.getByRole('button', {name: '打开快速切换'}));
    fireEvent.change(screen.getByRole('combobox', {name: '跳转与操作'}), {target: {value: 'coder'}});
    await waitFor(() => expect(screen.getByRole('option', {name: /coder.*codex/}).getAttribute('data-selected')).toBe('true'));
    expect(screen.queryByRole('option', {name: /Fixture project/})).toBeNull();
    fireEvent.keyDown(screen.getByRole('combobox', {name: '跳转与操作'}), {key: 'Enter'});
    await screen.findByRole('textbox', {name: /给 coder/}); expect(sends).toHaveLength(0);
  });
  it('waits for a slow sibling read even after another resource rejects', async () => {
    await ready(); let finish!: (value: Response) => void;
    readOverride = path => path.endsWith('/view') ? Promise.reject(new Error('view read failed')) : path.endsWith('/jobs') ? new Promise(resolve => {finish = resolve;}) : undefined;
    const before = fetcher.mock.calls.filter(([path]) => path.endsWith('/jobs')).length;
    fireEvent.click(screen.getByRole('button', {name: '刷新状态'}));
    await new Promise(resolve => setTimeout(resolve, 0));
    fireEvent.click(screen.getByRole('button', {name: '刷新状态'}));
    expect(fetcher.mock.calls.filter(([path]) => path.endsWith('/jobs')).length - before).toBe(1);
    finish(new Response(JSON.stringify({jobs: []}))); await screen.findByText('view read failed');
  });
  it('retains a receipt received while hidden without bypassing suspended read polling', async () => {
    const input = await ready(); let receipt!: (value: Response) => void;
    readOverride = (path, options) => path.endsWith('/jobs') && options?.body ? new Promise(resolve => {receipt = resolve;}) : undefined;
    fireEvent.change(input, {target: {value: 'accepted while hidden'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await waitFor(() => expect(receipt).toBeTypeOf('function'));
    Object.defineProperty(document, 'visibilityState', {configurable: true, value: 'hidden'}); fireEvent(document, new Event('visibilitychange'));
    const count = fetcher.mock.calls.length;
    receipt(new Response(JSON.stringify({job_id: 'job_hidden', status: 'queued'}), {status: 202}));
    await waitFor(() => expect((input as HTMLTextAreaElement).value).toBe(''));
    expect(fetcher.mock.calls.slice(count).some(([path, options]) => !options?.body && /view|jobs/.test(path))).toBe(false);
    expect(sessionStorage.getItem('muxary.pending.p.buddy')).toBeNull();
    Object.defineProperty(document, 'visibilityState', {configurable: true, value: 'visible'}); fireEvent(document, new Event('visibilitychange'));
    await waitFor(() => expect(fetcher.mock.calls.slice(count).some(([path]) => path.endsWith('/view'))).toBe(true));
  });
  it('keeps a per-project read gate through p→q→p even if an aborted transport is slow to settle', async () => {
    readOverride = path => path === '/api/projects' ? json({projects: [{id: 'p', display_name: 'Project P'}, {id: 'q', display_name: 'Project Q'}]}) : undefined;
    await ready();
    const reads: {path: string; signal?: AbortSignal | null; finish: (value: Response) => void}[] = [];
    readOverride = (path, options) => path === '/api/projects' ? json({projects: [{id: 'p', display_name: 'Project P'}, {id: 'q', display_name: 'Project Q'}]}) : path.endsWith('/view') ? new Promise(finish => reads.push({path, signal: options?.signal, finish})) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '刷新状态'}));
    fireEvent.click(screen.getByRole('button', {name: 'Project Q'}));
    await waitFor(() => expect(reads).toHaveLength(2));
    expect(reads[0].signal?.aborted).toBe(true);
    fireEvent.click(screen.getByRole('button', {name: 'Project P'}));
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(reads.filter(item => item.path === '/api/projects/p/view')).toHaveLength(1);
    reads[0].finish(new Response(JSON.stringify({view: {agents, namespace: {epoch: 1}}})));
    await waitFor(() => expect(reads.filter(item => item.path === '/api/projects/p/view')).toHaveLength(2));
    const latest = reads.at(-1)!; expect(latest.signal?.aborted).toBe(false);
    latest.finish(new Response(JSON.stringify({view: {agents, namespace: {epoch: 1}}})));
    await screen.findByRole('textbox', {name: /给 buddy/});
  });
  it('never transiently attaches a terminal using an old Agent under a pending new project', async () => {
    readOverride = path => path === '/api/projects' ? json({projects: [{id: 'p', display_name: 'Project P'}, {id: 'q', display_name: 'Project Q'}]}) : path === '/api/projects/q/view' ? new Promise(() => {}) : undefined;
    await ready(); fireEvent.click(screen.getByRole('button', {name: '原生终端'}));
    await screen.findByText('terminal'); expect(terminalMounts.some(item => item.project === 'p' && item.epoch === 1)).toBe(true);
    fireEvent.click(screen.getByRole('button', {name: 'Project Q'}));
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => path === '/api/projects/q/view')).toBe(true));
    expect(terminalMounts.some(item => item.project === 'q')).toBe(false); expect(screen.queryByText('terminal')).toBeNull();
  });
  it('ordinary Agent selection closes, rather than reattaches, the active terminal', async () => {
    agents.push({name: 'coder', provider: 'codex'}); await ready();
    fireEvent.click(screen.getByRole('button', {name: '原生终端'})); await screen.findByText('terminal');
    fireEvent.click(screen.getByRole('button', {name: /^coder/}));
    await screen.findByRole('textbox', {name: /给 coder/});
    expect(terminalMounts.some(item => item.agent === 'coder')).toBe(false); expect(screen.queryByText('terminal')).toBeNull();
    fireEvent.click(screen.getByRole('button', {name: /^buddy/})); expect(screen.queryByText('terminal')).toBeNull();
  });
  it('does not intercept composing Ctrl+K, Escape, or legacy IME keyCode 229', async () => {
    const input = await ready();
    fireEvent.keyDown(input, {key: 'k', ctrlKey: true, isComposing: true});
    fireEvent.keyDown(input, {key: 'k', ctrlKey: true, keyCode: 229});
    expect(document.querySelector('.command-dialog')!.hasAttribute('open')).toBe(false);
    fireEvent.click(screen.getByRole('button', {name: '快捷键与使用说明'}));
    fireEvent.keyDown(window, {key: 'Escape', isComposing: true});
    expect(document.querySelector('.help-dialog')!.hasAttribute('open')).toBe(true);
    expect(sends).toHaveLength(0);
  });
  it('a later manual diff response cannot be overwritten by an earlier refresh', async () => {
    await ready(); fireEvent.click(screen.getByRole('button', {name: '任务与上下文'}));
    fireEvent.click(screen.getByRole('button', {name: '代码变更'}));
    const pending: ((value: Response) => void)[] = [];
    readOverride = path => path.includes('/diff?') ? new Promise(resolve => pending.push(resolve)) : undefined;
    const refresh = screen.getByRole('button', {name: '刷新代码变更'});
    fireEvent.click(refresh); fireEvent.click(refresh); expect(pending).toHaveLength(2);
    pending[1](new Response(JSON.stringify({patch: 'newer diff'}))); await screen.findByText('newer diff');
    pending[0](new Response(JSON.stringify({patch: 'stale diff'})));
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(screen.getByText('newer diff')).toBeTruthy(); expect(screen.queryByText('stale diff')).toBeNull();
  });
  it.each(['workspace', 'epoch', 'agent', 'close'])('ignores a late diff after a %s scope transition', async change => {
    agents = [{name: 'buddy', provider: 'codebuddy', runtime: {workspace_path: '/fixture/old'}}, {name: 'coder', provider: 'codex'}];
    await ready(); fireEvent.click(screen.getByRole('button', {name: '任务与上下文'}));
    fireEvent.click(screen.getByRole('button', {name: '代码变更'}));
    let finish!: (value: Response) => void;
    readOverride = path => path.includes('/diff?') ? new Promise(resolve => {finish = resolve;}) : undefined;
    fireEvent.click(screen.getByRole('button', {name: '刷新代码变更'}));
    readOverride = path => path.includes('/diff?') ? json({patch: 'new scope diff'}) : undefined;
    if (change === 'workspace') {agents[0] = {...agents[0], runtime: {workspace_path: '/fixture/new'}}; fireEvent.click(screen.getByRole('button', {name: '刷新状态'})); await screen.findByText('new', {selector: '.workspace-strip button span'});}
    if (change === 'epoch') {namespaceEpoch = 2; fireEvent.click(screen.getByRole('button', {name: '刷新状态'})); await waitFor(() => expect(fetcher.mock.calls.filter(([path]) => path.includes('/diff?')).length).toBeGreaterThan(2));}
    if (change === 'agent') fireEvent.click(screen.getByRole('button', {name: /^coder/}));
    if (change === 'close') {fireEvent.click(screen.getByRole('button', {name: '收起上下文'})); fireEvent.click(screen.getByRole('button', {name: '任务与上下文'}));}
    await screen.findByText('new scope diff');
    finish(new Response(JSON.stringify({patch: 'late old scope diff'})));
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(screen.queryByText('late old scope diff')).toBeNull(); expect(screen.getByText('new scope diff')).toBeTruthy();
  });
  it('Escape closes only the top overlay before a mobile drawer', async () => {
    vi.stubGlobal('matchMedia', () => ({matches: true})); await ready();
    fireEvent.click(screen.getByRole('button', {name: '展开项目栏'}));
    fireEvent.click(screen.getByRole('button', {name: '打开快速切换'}));
    expect(document.querySelector('.command-dialog')!.hasAttribute('open')).toBe(true);
    fireEvent.keyDown(window, {key: 'Escape'});
    expect(document.querySelector('.command-dialog')!.hasAttribute('open')).toBe(false);
    expect(screen.getByRole('dialog', {name: '项目与 Agent'})).toBeTruthy();
    fireEvent.keyDown(window, {key: 'Escape'});
    expect(screen.queryByRole('dialog', {name: '项目与 Agent'})).toBeNull();
  });
  it('returns focus to the remounted mobile sidebar opener after Escape', async () => {
    vi.stubGlobal('matchMedia', () => ({matches: true})); await ready();
    const opener = screen.getByRole('button', {name: '展开项目栏'}); opener.focus(); fireEvent.click(opener);
    expect(opener.isConnected).toBe(false);
    await waitFor(() => expect(document.querySelector('.sidebar')!.contains(document.activeElement)).toBe(true));
    fireEvent.keyDown(window, {key: 'Escape'});
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole('button', {name: '展开项目栏'})));
  });
  it('mobile drawers make the background inert and close when going to the composer', async () => {
    vi.stubGlobal('matchMedia', () => ({matches: true}));
    await ready(); const trigger = screen.getByRole('button', {name: '展开项目栏'}); trigger.focus(); fireEvent.click(trigger);
    expect(screen.getByRole('dialog', {name: '项目与 Agent'})).toBeTruthy();
    expect(document.querySelector('.main-panel')!.hasAttribute('inert')).toBe(true);
    fireEvent.click(screen.getByRole('button', {name: '给当前 Agent 派活'}));
    await waitFor(() => expect(document.querySelector('.main-panel')!.hasAttribute('inert')).toBe(false));
    expect(screen.queryByRole('dialog', {name: '项目与 Agent'})).toBeNull();
    expect(sends).toHaveLength(0);
  });

  it('never enables a remembered Agent before its current project view is loaded', async () => {
    localStorage.setItem('muxary.selection', JSON.stringify({project: 'p', agent: 'buddy'}));
    holdView = true;
    render(<StrictMode><App /></StrictMode>);
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => path.endsWith('/view'))).toBe(true));
    const input = screen.getByRole('textbox', {name: /给 buddy/});
    expect(input.hasAttribute('disabled')).toBe(true);
    fireEvent.change(input, {target: {value: 'not before target verification'}});
    fireEvent.keyDown(input, {key: 'Enter'});
    expect(sends).toHaveLength(0);
  });
  it('binds native conversation reads to the observed namespace epoch', async () => {
    await ready();
    expect(fetcher.mock.calls.some(([path]) => path.includes('/conversation'))).toBe(false);
    fireEvent.click(screen.getByRole('button', {name: /原生会话/}));
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => path.includes('/conversation'))).toBe(true));
    expect(fetcher.mock.calls.filter(([path]) => path.includes('/conversation')).every(([path]) => path.includes('namespace_epoch=1'))).toBe(true);
  });
  it('does not hide unavailable native history as an empty successful conversation', async () => {
    conversationFailure = true; await ready();
    fireEvent.click(screen.getByRole('button', {name: /原生会话/}));
    expect(await screen.findByText(/原生会话暂不可用：stale namespace epoch/)).toBeTruthy();
    expect(sends).toHaveLength(0);
  });
  it('keeps native history and job evidence on separate source views', async () => {
    nativeItems.push({id: 'native-one', kind: 'agent_reply', body: 'native source evidence', source: 'provider_native/codebuddy'});
    jobs.push({job_id: 'job_one', agent_name: 'buddy', status: 'completed', request: {body: 'workbench evidence'}});
    await ready(); expect(screen.queryByText('native source evidence')).toBeNull();
    expect(screen.getByRole('region', {name: 'Agent 对话'}).textContent).toContain('workbench evidence');
    fireEvent.click(screen.getByRole('button', {name: /原生会话/}));
    expect(await screen.findByText('native source evidence')).toBeTruthy();
    expect(screen.getByRole('region', {name: 'Agent 对话'}).textContent).not.toContain('workbench evidence');
    expect(sends).toHaveLength(0);
  });
  it('does not clear a draft on rejected request', async () => {
    postMode = 'denied'; const input = await ready();
    fireEvent.change(input, {target: {value: '不要丢失正文'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await screen.findByText('denied'); expect((input as HTMLTextAreaElement).value).toBe('不要丢失正文'); expect(sends).toHaveLength(1);
  });
  it('retains uncertain draft and does not auto-resend on another Enter', async () => {
    postMode = 'lost'; const input = await ready();
    fireEvent.change(input, {target: {value: 'uncertain task'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await screen.findByText(/接收状态未知。没有自动重发/);
    fireEvent.keyDown(input, {key: 'Enter'}); expect(sends).toHaveLength(1); expect((input as HTMLTextAreaElement).value).toBe('uncertain task');
  });
  it('does not reclassify accepted submission when subsequent reads fail', async () => {
    const input = await ready(); failAfterSubmit = true;
    fireEvent.change(input, {target: {value: 'accepted task'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await screen.findByText(/任务已接收，状态刷新失败/);
    expect(screen.queryByText(/接收状态未知/)).toBeNull(); expect((input as HTMLTextAreaElement).value).toBe('');
    expect(sessionStorage.getItem('muxary.pending.p.buddy')).toBeNull();
  });
  it('IME composition and Shift+Enter never submit', async () => {
    const input = await ready(); fireEvent.change(input, {target: {value: '中文输入'}});
    fireEvent.compositionStart(input); fireEvent.keyDown(input, {key: 'Enter'}); expect(sends).toHaveLength(0);
    fireEvent.compositionEnd(input); fireEvent.keyDown(input, {key: 'Enter', shiftKey: true}); expect(sends).toHaveLength(0);
    fireEvent.keyDown(input, {key: 'Enter'}); await waitFor(() => expect(sends).toHaveLength(1));
  });
  it('retry clicks keep a stable idempotency key', async () => {
    jobs.push({job_id: 'job_old', agent_name: 'buddy', status: 'failed', request: {body: 'old task'}});
    await ready(); const retry = await screen.findByRole('button', {name: '重试'});
    fireEvent.click(retry); fireEvent.click(retry); await waitFor(() => expect(retry.hasAttribute('disabled')).toBe(false));
    fireEvent.click(retry); await waitFor(() => expect(sends).toHaveLength(2));
    expect(sends[0].body.idempotency_key).toBe(sends[1].body.idempotency_key);
  });
  it('storage failure sends nothing and never leaves the composer locked', async () => {
    const input = await ready(); const original = Storage.prototype.setItem;
    const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(function (this: Storage, key, value) {if (key.startsWith('muxary.pending.')) throw new Error('quota'); original.call(this, key, value);});
    fireEvent.change(input, {target: {value: 'storage failure'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await screen.findByText(/任务尚未发送/); expect(sends).toHaveLength(0); spy.mockRestore();
    fireEvent.keyDown(input, {key: 'Enter'}); await waitFor(() => expect(sends).toHaveLength(1));
  });
  it('an acknowledged receipt stays accepted even if pending-key cleanup fails', async () => {
    const input = await ready();
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {throw new Error('storage unavailable');});
    fireEvent.change(input, {target: {value: 'acknowledged'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await waitFor(() => expect((input as HTMLTextAreaElement).value).toBe(''));
    expect(sends).toHaveLength(1); expect(screen.queryByText(/接收状态未知/)).toBeNull();
  });
  it('a real vendored suggestion edits the draft without sending', async () => {
    const input = await ready();
    fireEvent.click(screen.getByRole('button', {name: '理解这个项目'}));
    expect((input as HTMLTextAreaElement).value).toContain('先总结，不修改文件');
    expect(sends).toHaveLength(0);
    expect(screen.getByText(/快捷任务模板/)).toBeTruthy();
  });
  it('shows conversation tasks oldest first even when the queue returns newest first', async () => {
    jobs.push({job_id: 'job_newest', agent_name: 'buddy', status: 'completed', created_at: '2026-11-11T08:01:00Z', request: {body: 'second task'}}, {job_id: 'job_oldest', agent_name: 'buddy', status: 'completed', created_at: '2026-11-11T08:00:00Z', request: {body: 'first task'}});
    await ready();
    const conversation = screen.getByRole('region', {name: 'Agent 对话'}).textContent!;
    expect(conversation.indexOf('first task')).toBeLessThan(conversation.indexOf('second task'));
  });
  it('a task-card target switch never sends and the next submit names that agent', async () => {
    agents.push({name: 'coder', provider: 'codex'});
    jobs.push({job_id: 'job_coder', agent_name: 'coder', status: 'completed', request: {body: 'switch target'}});
    await ready(); fireEvent.click(screen.getByRole('button', {name: 'switch target'}));
    const input = await screen.findByRole('textbox', {name: /给 coder/});
    expect(sends).toHaveLength(0); expect(screen.getByText(/发送给 coder/)).toBeTruthy();
    fireEvent.change(input, {target: {value: 'coder only'}}); fireEvent.keyDown(input, {key: 'Enter'});
    await waitFor(() => expect(sends).toHaveLength(1)); expect(sends[0].body.agent).toBe('coder');
  });
  it('shares selection and drafts across the two views, without a canvas composer', async () => {
    agents.push({name: 'coder', provider: 'codex'});
    const input = await ready(); fireEvent.change(input, {target: {value: 'buddy draft'}});
    fireEvent.click(screen.getByRole('button', {name: /画布/}));
    expect(await screen.findByRole('button', {name: '选择 coder'})).toBeTruthy();
    expect(screen.queryByRole('textbox', {name: /给 buddy/})).toBeNull();
    fireEvent.click(screen.getByRole('button', {name: '选择 coder'}));
    expect(sends).toHaveLength(0);
    fireEvent.click(screen.getByRole('button', {name: '专注 coder'}));
    expect(await screen.findByRole('textbox', {name: /给 coder/})).toBeTruthy();
    fireEvent.click(screen.getByRole('button', {name: /^buddy/}));
    expect((await screen.findByRole('textbox', {name: /给 buddy/}) as HTMLTextAreaElement).value).toBe('buddy draft');
  });
  it('does not fetch workspace or diff until requested, then scopes diff by Agent', async () => {
    await ready();
    expect(fetcher.mock.calls.some(([path]) => /workspace|diff/.test(path))).toBe(false);
    fireEvent.click(screen.getByRole('button', {name: '任务与上下文'}));
    fireEvent.click(screen.getByRole('button', {name: '代码变更'}));
    await waitFor(() => expect(fetcher.mock.calls.some(([path]) => path.endsWith('/diff?agent=buddy'))).toBe(true));
    expect(fetcher.mock.calls.some(([path]) => path.endsWith('/diff'))).toBe(false);
  });
  it('loads older history without losing the rest of the evidence', async () => {
    for (let index = 0; index < 25; index++) jobs.push({job_id: `job_${index}`, agent_name: 'buddy', status: 'completed', created_at: String(index).padStart(2, '0'), request: {body: `body-${index}`}});
    await ready();
    const region = screen.getByRole('region', {name: 'Agent 对话'});
    expect(region.textContent).not.toContain('body-0');
    expect(region.textContent).toContain('body-24');
    fireEvent.click(screen.getByRole('button', {name: /显示更早的记录/}));
    expect(region.textContent).toContain('body-0');
    expect(region.querySelectorAll('.job-turn')).toHaveLength(25);
  });
});
