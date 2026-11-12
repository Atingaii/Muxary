import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { IconArrowDown, IconArrowUpRight, IconBolt, IconCheck, IconChevronDown, IconChevronRight, IconCircle, IconCode, IconCommand, IconCopy, IconFolder, IconGitBranch, IconHistory, IconLayoutSidebar, IconLayoutSidebarRight, IconLoader2, IconMessage, IconMoon, IconPlayerStop, IconRefresh, IconSearch, IconSettings, IconSun, IconTerminal2, IconX } from '@tabler/icons-react';
import { InputBar } from './vendor/agent-elements/input-bar';
import { Suggestions } from './vendor/agent-elements/input/suggestions';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './vendor/shadcn/command';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from './vendor/shadcn/resizable';
import { MessageContent } from './MessageContent';
import { useSerialPoll } from './polling';
import { useConversationScroll } from './useConversationScroll';
import { api, ApiError, initializeSession, conversationMessages, jobReply, projectPath, rememberSelection, row, rows, statusLabel, terminalStates, text, workspaceGroups, type Row } from './model';

const AgentCanvas = lazy(() => import('./AgentCanvas').then(module => ({default: module.AgentCanvas})));
const AgentTerminal = lazy(() => import('./Terminal').then(module => ({default: module.AgentTerminal})));

function Button({label, children, onClick, active = false, buttonRef}: {label: string; children: React.ReactNode; onClick: () => void; active?: boolean; buttonRef?: React.Ref<HTMLButtonElement>}) {
  return <button ref={buttonRef} type="button" className={`icon-button ${active ? 'active' : ''}`} title={label} aria-label={label} aria-pressed={active} onClick={onClick}>{children}</button>;
}
function Status({status}: {status: unknown}) {return <span className={`status status-${text(status)}`}><i />{statusLabel(status)}</span>;}
const errorText = (error: unknown) => error instanceof Error ? error.message : '请求失败';
function readStorage(storage: Storage, key: string): string {try {return storage.getItem(key) || '';} catch {return '';}}
function initialSelection(): Row {try {return row(JSON.parse(readStorage(localStorage, 'muxary.selection') || '{}'));} catch {return {};}}
function pendingKey(project: string, agent: string) { return `muxary.pending.${project}.${agent}`; }

export function App() {
  const [auth, setAuth] = useState<'loading' | 'ready' | 'locked'>('loading');
  const [authToken, setAuthToken] = useState('');
  const [projects, setProjects] = useState<Row[]>([]);
  const [project, setProject] = useState(text(initialSelection().project));
  const [agent, setAgent] = useState(text(initialSelection().agent));
  const [view, setView] = useState<Row>({});
  const [viewProject, setViewProject] = useState('');
  const [jobs, setJobs] = useState<Row[]>([]);
  const [conversation, setConversation] = useState<Row>({});
  const [conversationError, setConversationError] = useState('');
  const [conversationSource, setConversationSource] = useState<'tasks' | 'native'>('tasks');
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [error, setError] = useState('');
  const [network, setNetwork] = useState<'loading' | 'ok' | 'offline'>('loading');
  const [sidebar, setSidebar] = useState(() => !matchMedia('(max-width: 680px)').matches);
  const [context, setContext] = useState(false);
  const [breakpoints, setBreakpoints] = useState(() => ({narrow: matchMedia('(max-width: 680px)').matches, compact: matchMedia('(max-width: 980px)').matches}));
  const [presentation, setPresentation] = useState<'focus' | 'canvas'>('focus');
  const [palette, setPalette] = useState(false);
  const [projectDialog, setProjectDialog] = useState(false);
  const [projectDirectory, setProjectDirectory] = useState('');
  const [openingProject, setOpeningProject] = useState(false);
  const [projectOpenError, setProjectOpenError] = useState('');
  const [uncertainDirectory, setUncertainDirectory] = useState('');
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [workspace, setWorkspace] = useState<Row>({});
  const [visibleCount, setVisibleCount] = useState(20);
  const [terminalIdentity, setTerminalIdentity] = useState<{project: string; agent: string; epoch: number} | null>(null);
  const [tab, setTab] = useState<'tasks' | 'changes'>('tasks');
  const [taskFilter, setTaskFilter] = useState<'all' | 'active'>('all');
  const [diff, setDiff] = useState<Row>({});
  const [filter, setFilter] = useState('');
  const [dark, setDark] = useState(readStorage(localStorage, 'muxary.theme') === 'dark');
  const [help, setHelp] = useState(false);
  const [copied, setCopied] = useState('');
  const sidebarElement = useRef<HTMLElement>(null), contextElement = useRef<HTMLElement>(null);
  const sidebarOpener = useRef<HTMLButtonElement>(null);
  const diffRequest = useRef<AbortController | null>(null), diffSequence = useRef(0);
  const sending = useRef(false);
  const actionLocks = useRef(new Set<string>());
  const [actionBusy, setActionBusy] = useState<Record<string, boolean>>({});
  const helpDialog = useRef<HTMLDialogElement>(null);
  const paletteDialog = useRef<HTMLDialogElement>(null);
  const openProjectDialog = useRef<HTMLDialogElement>(null);
  const projectOpening = useRef(false), projectsRevision = useRef(0);
  const viewRequests = useRef(new Map<string, {promise: Promise<void>; controller: AbortController}>());
  const viewSequence = useRef(0);
  const selected = useRef({project, agent}), selectionRevision = useRef(0);
  if (selected.current.project !== project || selected.current.agent !== agent) selectionRevision.current++;
  selected.current = {project, agent};
  const projectRecord = projects.find(item => item.id === project);
  const agents = viewProject === project ? rows(view.agents) : [];
  const agentRecord = agents.find(item => item.name === agent);
  const epoch = viewProject === project ? row(view.namespace).epoch : undefined;
  const {viewportRef, contentRef, following, pause, jumpToLatest} = useConversationScroll({scopeKey: JSON.stringify([project, agent, epoch, conversationSource]), enabled: presentation === 'focus'});
  const targetReady = Boolean(project && agentRecord && typeof epoch === 'number');
  const terminal = targetReady && terminalIdentity?.project === project && terminalIdentity.agent === agent && terminalIdentity.epoch === epoch;
  function setTerminal(open: boolean) {setTerminalIdentity(open && targetReady ? {project, agent, epoch: epoch as number} : null);}
  const draftKey = `${project}/${agent}`, draft = drafts[draftKey] || '';
  const activeJobs = jobs.filter(item => !terminalStates.has(text(item.status)));
  const selectedJobs = jobs.filter(item => item.agent_name === agent);
  const contextJobs = taskFilter === 'active' ? activeJobs : jobs;
  const matchingProjects = projects.filter(item => `${text(item.display_name)} ${text(item.root)}`.toLocaleLowerCase().includes(filter.toLocaleLowerCase()));
  const nativeMessages = conversationMessages(conversation);
  const workspacePath = text(agentRecord?.workspace_path) || text(row(agentRecord?.runtime).workspace_path);
  const currentDiffScope = `${project}/${agent}/${epoch}/${workspacePath}`;
  const diffScope = useRef(currentDiffScope); diffScope.current = currentDiffScope;
  const drawer = sidebar && breakpoints.narrow ? 'sidebar' : context && breakpoints.compact ? 'context' : null;
  const workspaceName = workspacePath.split(/[\\/]/).filter(Boolean).at(-1) || '目录待确认';
  const chooseAgent = useCallback((name: string) => {setAgent(name); if (matchMedia('(max-width: 680px)').matches) setSidebar(false);}, []);
  const focusAgent = useCallback((name: string) => {setAgent(name); setPresentation('focus'); if (matchMedia('(max-width: 980px)').matches) setContext(false); if (matchMedia('(max-width: 680px)').matches) setSidebar(false);}, []);
  const terminalCandidates = useRef({project, epoch, agents}); terminalCandidates.current = {project, epoch, agents};
  const terminalAgent = useCallback((name: string) => {const target = terminalCandidates.current; if (typeof target.epoch !== 'number' || !target.agents.some(item => item.name === name)) return; setAgent(name); setTerminalIdentity({project: target.project, agent: name, epoch: target.epoch});}, []);
  function toggleSidebar() {setSidebar(value => !value); if (matchMedia('(max-width: 680px)').matches) setContext(false);}
  function toggleContext() {setContext(value => !value); if (matchMedia('(max-width: 680px)').matches) setSidebar(false);}
  function showChanges() {setTab('changes'); setContext(true); if (matchMedia('(max-width: 680px)').matches) setSidebar(false);}

  useEffect(() => {document.documentElement.classList.toggle('dark', dark); try {localStorage.setItem('muxary.theme', dark ? 'dark' : 'light');} catch { /* Preferences are optional. */ }}, [dark]);
  useEffect(() => {
    initializeSession().then(() => setAuth('ready')).catch(() => setAuth('locked'));
  }, []);
  useEffect(() => {
    const dialog = helpDialog.current;
    if (help) dialog?.showModal(); else if (dialog?.open) dialog.close();
  }, [help]);
  useEffect(() => {
    const dialog = paletteDialog.current;
    if (palette) dialog?.showModal(); else if (dialog?.open) dialog.close();
  }, [palette]);
  useEffect(() => {
    const dialog = openProjectDialog.current;
    if (projectDialog) dialog?.showModal(); else if (dialog?.open) dialog.close();
  }, [projectDialog]);
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.isComposing || event.keyCode === 229) return;
      if (event.key === 'Tab' && drawer && !palette && !help && !projectDialog) {
        const element = drawer === 'sidebar' ? sidebarElement.current : contextElement.current;
        const targets = Array.from(element?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), a[href], [tabindex="0"]') || []).filter(item => item.offsetParent !== null);
        const first = targets[0], last = targets.at(-1);
        if (!first) {event.preventDefault(); element?.focus();}
        else if (event.shiftKey && (document.activeElement === first || !element?.contains(document.activeElement))) {event.preventDefault(); last?.focus();}
        else if (!event.shiftKey && (document.activeElement === last || !element?.contains(document.activeElement))) {event.preventDefault(); first.focus();}
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {event.preventDefault(); if (!projectDialog && !help) setPalette(value => !value);}
      if (event.key === 'Escape') {event.preventDefault(); if (projectDialog) setProjectDialog(false); else if (help) setHelp(false); else if (palette) setPalette(false); else {setSidebar(value => matchMedia('(max-width: 680px)').matches ? false : value); setContext(value => matchMedia('(max-width: 980px)').matches ? false : value);}}
    };
    window.addEventListener('keydown', keydown); return () => window.removeEventListener('keydown', keydown);
  }, [drawer, palette, help, projectDialog]);
  useEffect(() => {
    if (!drawer) return;
    const previous = document.activeElement as HTMLElement | null;
    const element = drawer === 'sidebar' ? sidebarElement.current : contextElement.current;
    const frame = requestAnimationFrame(() => (element?.querySelector<HTMLElement>('button:not(:disabled), input:not(:disabled)') || element)?.focus());
    return () => {
      cancelAnimationFrame(frame);
      // The sidebar opener is conditionally unmounted while the drawer is open.
      const target = drawer === 'sidebar' ? sidebarOpener.current : previous?.isConnected ? previous : null;
      target?.focus();
    };
  }, [drawer]);
  useEffect(() => {
    // Crossing a breakpoint must not leave two overlapping mobile drawers.
    const narrow = matchMedia('(max-width: 680px)'), compact = matchMedia('(max-width: 980px)');
    const resize = () => {setBreakpoints({narrow: narrow.matches, compact: compact.matches}); if (narrow.matches) setSidebar(false); if (compact.matches) setContext(false);};
    narrow.addEventListener?.('change', resize); compact.addEventListener?.('change', resize);
    return () => {narrow.removeEventListener?.('change', resize); compact.removeEventListener?.('change', resize);};
  }, []);
  const refreshProjects = useCallback(async (signal: AbortSignal) => {
      const revision = projectsRevision.current;
      try {
        const payload = await api('/api/projects', undefined, signal);
        if (signal.aborted || revision !== projectsRevision.current) return;
        const next = rows(payload.projects); setProjects(next);
        setProject(current => next.some(item => item.id === current) ? current : text(next[0]?.id));
        setNetwork('ok');
      } catch (err) {if (!signal.aborted) {setNetwork('offline'); if (err instanceof ApiError && err.status === 401) setAuth('locked');}}
  }, []);
  useSerialPoll(refreshProjects, 5000, auth === 'ready');
  const hydrateJobs = presentation === 'focus' || context;
  const refreshView = useCallback((signal?: AbortSignal): Promise<void> => {
    if (!project || document.visibilityState === 'hidden') return Promise.resolve();
    // Presentation only changes the next round's hydration. It cannot create
    // a second /view read while a manual refresh is already in flight.
    const scope = project;
    const previous = viewRequests.current.get(scope);
    if (previous) {
      if (!previous.controller.signal.aborted) return previous.promise;
      return previous.promise.catch(() => {}).then(() => {if (!signal?.aborted && selected.current.project === project) return refreshView(signal);});
    }
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort(); else signal?.addEventListener('abort', abort, {once: true});
    const readSignal = controller.signal;
    const promise = (async () => {
    if (!project || readSignal.aborted) return;
    const sequence = ++viewSequence.current;
    // Wait for both reads even when one fails, so a failed sibling cannot
    // release the per-project gate while the other resource is still in flight.
    const [viewResult, jobResult] = await Promise.allSettled([
      api(projectPath(project, '/view'), undefined, readSignal), hydrateJobs ? api(projectPath(project, '/jobs'), undefined, readSignal) : Promise.resolve(null),
    ]);
    if (readSignal.aborted || selected.current.project !== project || sequence !== viewSequence.current) return;
    if (viewResult.status === 'rejected') throw viewResult.reason;
    if (jobResult.status === 'rejected') throw jobResult.reason;
    const viewPayload = viewResult.value, jobPayload = jobResult.value;
    const nextView = row(viewPayload.view ?? viewPayload);
    setView(nextView); setViewProject(project); if (jobPayload) setJobs(rows(jobPayload.jobs).sort((left, right) => text(left.created_at).localeCompare(text(right.created_at)))); setNetwork('ok');
    setAgent(current => rows(nextView.agents).some(item => item.name === current) ? current : text(rows(nextView.agents)[0]?.name));
    })();
    viewRequests.current.set(scope, {promise, controller});
    void promise.finally(() => {signal?.removeEventListener('abort', abort); if (viewRequests.current.get(scope)?.promise === promise) viewRequests.current.delete(scope);}).catch(() => {});
    return promise;
  }, [project, hydrateJobs]);
  useEffect(() => {
    setView({}); setJobs([]); setConversation({}); setTerminal(false);
    return () => {viewRequests.current.get(project)?.controller.abort();};
  }, [project]);
  const pollView = useCallback((signal: AbortSignal) => refreshView(signal).catch(err => {if (!signal.aborted) {setNetwork('offline'); setError(errorText(err));}}), [refreshView]);
  useSerialPoll(pollView, 1800, auth === 'ready' && Boolean(project));
  useEffect(() => {
    setTerminalIdentity(previous => previous?.project === project && previous.agent === agent && previous.epoch === epoch ? previous : null);
    if (auth !== 'ready' || !project || !agent || typeof epoch !== 'number') return;
    rememberSelection(project, agent); setConversation({}); setConversationError(''); setError('');
    setUncertain(Boolean(readStorage(sessionStorage, pendingKey(project, agent))));
    setWorkspace({}); setWorkspaceOpen(false); setVisibleCount(20);
  }, [auth, project, agent, epoch]);
  const refreshConversation = useCallback(async (signal: AbortSignal) => {
      try {
        const payload = await api(projectPath(project, `/agents/${encodeURIComponent(agent)}/conversation?limit=100&namespace_epoch=${epoch}`), undefined, signal);
        if (!signal.aborted) {setConversation(payload); setConversationError('');}
      } catch (err) {if (!signal.aborted) setConversationError(`原生会话暂不可用：${errorText(err)}。CCB 任务与原生终端仍可单独查看。`);}
  }, [project, agent, epoch]);
  useSerialPoll(refreshConversation, 2200, auth === 'ready' && targetReady && presentation === 'focus' && conversationSource === 'native');
  useEffect(() => {setVisibleCount(20);}, [conversationSource]);
  useEffect(() => {
    if (!workspaceOpen || !targetReady) return;
    const controller = new AbortController(); setWorkspace({});
    api(projectPath(project, `/agents/${encodeURIComponent(agent)}/workspace`), undefined, controller.signal).then(value => {if (!controller.signal.aborted) setWorkspace(value);}).catch(err => {if (!controller.signal.aborted) setWorkspace({error: errorText(err)});});
    return () => controller.abort();
  }, [workspaceOpen, project, agent, epoch, workspacePath, targetReady]);
  const refreshDiff = useCallback(async () => {
    if (!targetReady) return;
    diffRequest.current?.abort();
    const controller = new AbortController(); diffRequest.current = controller;
    const sequence = ++diffSequence.current, scope = currentDiffScope;
    const current = () => !controller.signal.aborted && sequence === diffSequence.current && diffScope.current === scope;
    setDiff({});
    try {const value = await api(projectPath(project, `/diff?agent=${encodeURIComponent(agent)}`), undefined, controller.signal); if (current()) setDiff(value);}
    catch (err) {if (current()) setDiff({error: errorText(err)});}
  }, [project, agent, currentDiffScope, targetReady]);
  useEffect(() => {
    if (context && tab === 'changes') void refreshDiff();
    return () => {diffRequest.current?.abort(); diffSequence.current++;};
  }, [tab, context, refreshDiff]);

  async function submit(content: string) {
    if (!content.trim() || !targetReady || network !== 'ok' || sending.current || uncertain) return;
    const target = {project, agent}; const key = crypto.randomUUID();
    let attempted = false;
    sending.current = true; setBusy(true); setError('');
    try {
      sessionStorage.setItem(pendingKey(project, agent), key);
      attempted = true;
      await api(projectPath(project, '/jobs'), {agent, body: content, idempotency_key: key, namespace_epoch: epoch});
      attempted = false; // Receipt is authoritative even if local cleanup fails.
      try {sessionStorage.removeItem(pendingKey(target.project, target.agent));} catch { /* Keep acknowledged state, not unknown. */ }
      setDrafts(previous => {const key = `${target.project}/${target.agent}`; return previous[key]?.trim() === content.trim() ? {...previous, [key]: ''} : previous;});
      // A failed read after the acknowledged submit must not invite resending.
      if (selected.current.project === target.project) void refreshView().catch(err => {if (selected.current.project === target.project && !(err instanceof DOMException && err.name === 'AbortError')) setError(`任务已接收，状态刷新失败：${errorText(err)}`);});
    } catch (err) {
      const unknown = attempted && (!(err instanceof ApiError) || err.status >= 500 || text(err.payload.code) === 'outcome_unknown');
      if (!unknown) {try {sessionStorage.removeItem(pendingKey(target.project, target.agent));} catch { /* No request was sent. */ }}
      if (selected.current.project === target.project && selected.current.agent === target.agent) {setUncertain(unknown); setError(unknown ? '接收状态未知。没有自动重发；请先核对任务列表或原生终端。' : !attempted ? '浏览器存储不可用，任务尚未发送。请启用此站点的会话存储。' : errorText(err));}
    } finally {sending.current = false; setBusy(false);}
  }
  async function jobAction(job: Row, action: 'cancel' | 'retry') {
    const targetProject = project, id = text(job.job_id);
    const scope = `muxary.action.${targetProject}.${id}.${action}`;
    if (actionLocks.current.has(scope)) return;
    actionLocks.current.add(scope); setActionBusy(previous => ({...previous, [id]: true}));
    // Stable across clicks/reloads/timeouts: retry the new child, not this old
    // failed task, if another attempt is wanted after a retry was acknowledged.
    try {
      const key = readStorage(sessionStorage, scope) || crypto.randomUUID();
      sessionStorage.setItem(scope, key);
      setError('');
      await api(projectPath(targetProject, `/jobs/${encodeURIComponent(id)}/${action}`), {idempotency_key: key});
      if (selected.current.project === targetProject) void refreshView().catch(err => {if (selected.current.project === targetProject && !(err instanceof DOMException && err.name === 'AbortError')) setError(`操作已接收，状态刷新失败：${errorText(err)}`);});
    } catch (err) {
      if (selected.current.project === targetProject) setError(errorText(err));
    } finally {
      actionLocks.current.delete(scope); setActionBusy(previous => ({...previous, [id]: false}));
    }
  }
  async function openProject() {
    if (projectOpening.current || !projectDirectory.trim() || uncertainDirectory === projectDirectory) return;
    projectOpening.current = true; setOpeningProject(true); setProjectOpenError('');
    const revision = selectionRevision.current;
    try {
      const result = await api('/api/projects/open', {path: projectDirectory});
      const id = text(result.project_id), root = text(result.root);
      if (!id || !root) throw new Error('CCB 未返回项目身份');
      // Ignore any projects snapshot that started before this new registration.
      projectsRevision.current++;
      setProjects(previous => previous.some(item => item.id === id) ? previous : [...previous, {id, root, display_name: text(result.display_name) || root.split(/[\\/]/).filter(Boolean).at(-1) || id}]);
      if (selectionRevision.current === revision) {
        setProject(id); setAgent(''); setPresentation('focus'); setContext(false);
        if (matchMedia('(max-width: 680px)').matches) setSidebar(false);
      }
      setProjectDialog(false);
    } catch (err) {
      const unknown = !(err instanceof ApiError) || err.payload.retry_safe === false || (err.status >= 500 && err.payload.retry_safe !== true);
      if (unknown) setUncertainDirectory(projectDirectory);
      setProjectOpenError(unknown ? `${errorText(err)}。打开结果未确认，请刷新项目列表检查；不会自动再次启动。若仍不可见，请在终端检查 CCB 状态。` : errorText(err));
    } finally {projectOpening.current = false; setOpeningProject(false);}
  }
  async function openSettings() {
    // Open the window synchronously so popup policy doesn't discard the
    // user-initiated action while the existing config server is prepared.
    const page = window.open('about:blank', '_blank');
    if (page) page.opener = null;
    try {
      const result = await api(projectPath(project, '/config/open'), {});
      const url = new URL(text(result.url));
      if (!['http:', 'https:'].includes(url.protocol) || !['127.0.0.1', 'localhost'].includes(url.hostname)) throw new Error('配置页返回了非本机地址');
      if (page) page.location.href = url.href; else setError('浏览器拦截了设置窗口，请允许本机弹窗后重试。');
    } catch (err) {page?.close(); setError(errorText(err));}
  }
  async function copy(value: string) {try {await navigator.clipboard.writeText(value); setCopied(value); setTimeout(() => setCopied(''), 1500);} catch {setError('复制失败，请手动选择文本。');}}

  if (auth !== 'ready') return <main className="auth-page"><div className="auth-card"><IconCommand size={30}/><h1>Muxary</h1><p>{auth === 'loading' ? '正在连接本机工作台…' : '连接你的本机工作台'}</p>{auth === 'locked' && <form onSubmit={event => {event.preventDefault(); api('/api/session', {token: authToken}).then(() => {setAuthToken(''); setAuth('ready');}).catch(err => setError(errorText(err)));}}><label htmlFor="token">启动令牌</label><input id="token" type="password" value={authToken} onChange={event => setAuthToken(event.target.value)} autoComplete="off"/><button className="primary" type="submit">连接工作台</button><small>在终端运行 muxary，使用启动时提供的本机地址。</small></form>}{error && <p role="alert">{error}</p>}</div></main>;

  return <div className={`workbench ${sidebar ? '' : 'sidebar-hidden'} ${context ? '' : 'context-hidden'}`}>
    <aside ref={sidebarElement} className="sidebar" aria-label="项目与 Agent" tabIndex={-1} role={drawer === 'sidebar' ? 'dialog' : undefined} aria-modal={drawer === 'sidebar' || undefined} inert={!sidebar || drawer === 'context'}>
      <div className="brand"><span className="brand-mark"><IconCommand size={20}/></span><strong>Muxary</strong><span className="local-tag">LOCAL</span><Button label="收起项目栏" onClick={() => setSidebar(false)}><IconLayoutSidebar size={17}/></Button></div>
      <button className="new-task" onClick={() => {setPresentation('focus'); if (matchMedia('(max-width: 680px)').matches) setSidebar(false); requestAnimationFrame(() => document.querySelector<HTMLTextAreaElement>('.composer textarea')?.focus());}}><IconMessage size={17}/>给当前 Agent 派活</button>
      <div className="search-box"><IconSearch size={15}/><input id="project-search" aria-label="搜索项目" placeholder="搜索项目…" value={filter} onChange={event => setFilter(event.target.value)}/><button className="palette-trigger" aria-label="打开快速切换" onClick={() => setPalette(true)}><kbd>⌘ K</kbd></button></div>
      <div className="section-label">项目<span>{projects.length}<button className="open-project-trigger" aria-label="打开项目" title="打开本机项目目录" onClick={() => setProjectDialog(true)}>{openingProject ? <IconLoader2 size={14} className="spin"/> : <IconFolder size={14}/>}</button></span></div>
      <nav className="projects">{matchingProjects.map(item => <div className="project-group" key={text(item.id)}>
        <button className={`project-button ${project === item.id ? 'selected' : ''}`} onClick={() => {setProject(text(item.id)); setFilter(''); if (matchMedia('(max-width: 680px)').matches) setSidebar(false);}} title={text(item.root)}><IconChevronRight className={project === item.id ? 'project-expanded' : ''} size={13}/><IconFolder size={16}/><span>{text(item.display_name) || text(item.id)}</span></button>
        {project === item.id && <>{workspaceGroups(agents).map(group => <div className="workspace-group" role="group" aria-label={`工作目录 ${group.path || '待确认'}`} key={group.path}>
          <div className="workspace-group-label" title={group.path || 'CCB 尚未报告工作目录'}><IconGitBranch size={12}/><span>{group.label || '目录待确认'}</span>{group.path && group.agents.length > 1 && <small>共享</small>}</div>
          <div className="agents">{group.agents.map(member => <button key={text(member.name)} className={`agent-button ${agent === member.name ? 'selected' : ''}`} onClick={() => chooseAgent(text(member.name))}><span className={`agent-dot ${jobs.some(job => job.agent_name === member.name && !terminalStates.has(text(job.status))) ? 'running' : ''}`} aria-hidden="true"/><span>{text(member.name)}</span><small>{text(member.provider)}</small></button>)}</div>
        </div>)}{!agents.length && <p className="sidebar-empty">当前项目没有运行中的 Agent</p>}</>}

      </div>)}{Boolean(projects.length && !matchingProjects.length) && <div className="sidebar-empty search-empty"><IconSearch size={20}/><p>没有匹配的项目</p><button onClick={() => setFilter('')} aria-label="清除项目搜索">清除搜索</button></div>}{!projects.length && <div className="sidebar-empty">暂无已挂载项目<br/><small>使用“打开项目”，或在项目目录运行 muxary tui 启动 CCB。</small></div>}</nav>
      <div className="sidebar-footer"><button onClick={openSettings} disabled={!project}><IconSettings size={17}/>项目设置<IconArrowUpRight size={14}/></button><button onClick={() => setHelp(true)}><IconCommand size={17}/>快捷键与使用说明</button><div className="runtime-badge"><i className={network === 'ok' ? 'connected' : ''}/><span>{network === 'ok' ? '本机工作台已连接' : network === 'loading' ? '正在连接本机工作台…' : '连接中断 · 正在重连'}</span><Button label={dark ? '切换浅色模式' : '切换深色模式'} onClick={() => setDark(!dark)}>{dark ? <IconSun size={15}/> : <IconMoon size={15}/>}</Button></div></div>
    </aside>
    <main className="main-panel" inert={Boolean(drawer)}>
      <header className="topbar">
        <div className="breadcrumbs">{!sidebar && <Button label="展开项目栏" buttonRef={sidebarOpener} onClick={toggleSidebar}><IconLayoutSidebar size={18}/></Button>}<IconFolder size={15}/><span>{text(projectRecord?.display_name) || '工作空间'}</span><IconChevronRight size={13}/><strong>{agent || '选择 Agent'}</strong></div>
        <div className="header-actions">
          <div className="view-switch" aria-label="工作视图"><button aria-pressed={presentation === 'focus'} onClick={() => setPresentation('focus')}>专注</button><button aria-pressed={presentation === 'canvas'} onClick={() => setPresentation('canvas')}>画布 <small>{agents.length}</small></button></div>
          <span className="toolbar-divider"/>
          <button className="toolbar-action changes-trigger" aria-label="查看代码变更" aria-expanded={context && tab === 'changes'} aria-controls="context-panel" onClick={showChanges}><IconCode size={16}/><span>变更</span></button>
          <Button label="原生终端" active={terminal} onClick={() => setTerminal(!terminal)}><IconTerminal2 size={18}/></Button>
          <Button label="任务与上下文" active={context} onClick={toggleContext}><IconLayoutSidebarRight size={18}/></Button>
          <span className="refresh-action"><Button label="刷新状态" onClick={() => {void refreshView().catch(err => {if (selected.current.project === project && !(err instanceof DOMException && err.name === 'AbortError')) setError(errorText(err));});}}><IconRefresh size={16}/></Button></span>
        </div>
      </header>
      <ResizablePanelGroup orientation="vertical" id="agent-surface" className="agent-surface"><ResizablePanel id="work" minSize="25%"><div className="work-content">
      <h1 className="sr-only">{presentation === 'canvas' ? '你的并行工作现场' : agent ? `与 ${agent} 一起构建` : '选择项目与 Agent'}</h1>
      <div className="surface-bar">
        <div className="workspace-strip"><button className={workspaceOpen ? 'selected' : ''} aria-expanded={workspaceOpen} onClick={() => setWorkspaceOpen(value => !value)} disabled={!targetReady} title={workspacePath || 'CCB 尚未报告工作目录'}><IconGitBranch size={14}/><span>{workspaceName}</span><IconChevronDown size={12}/></button><span className="workspace-scope">Agent 绑定目录</span></div>
        {presentation === 'focus' ? <div className="conversation-sources" aria-label="对话来源"><button aria-pressed={conversationSource === 'tasks'} onClick={() => setConversationSource('tasks')}>工作台任务 <small>{selectedJobs.length}</small></button><button aria-pressed={conversationSource === 'native'} onClick={() => setConversationSource('native')}>原生会话{Boolean(nativeMessages.length) && <small>{nativeMessages.length}</small>}</button></div> : <span className="canvas-caption">{agents.length} 个 Agent · 同一 CCB 现场</span>}
      </div>
      {workspaceOpen && <section className="workspace-details" aria-label="当前 Agent 工作目录">{text(workspace.error) ? <p role="alert">{text(workspace.error)}</p> : <><code>{text(row(workspace.workspace).path) || '正在核对运行目录…'}</code><p>{text(row(workspace.workspace).branch) || (row(workspace.workspace).git_state === 'detached' ? 'Detached HEAD' : row(workspace.workspace).git_state === 'not_git' ? '非 Git 工作目录' : '分支待确认')}{Array.isArray(row(workspace.workspace).shared_agents) && (row(workspace.workspace).shared_agents as unknown[]).length > 1 ? ' · 多个 Agent 共享此目录，无写锁保证' : ''}</p><small>CCB 声明/启动绑定目录，不是写入隔离保证。变更属于目录，不等同某个 Agent 的产出。</small></>}<button onClick={openSettings}>在原 CCB 设置中配置 worktree <IconArrowUpRight size={13}/></button></section>}
      {error && <div className="error-banner" role="alert"><span>{error}</span><button aria-label="关闭提示" onClick={() => setError('')}><IconX size={16}/></button></div>}
      {presentation === 'canvas' ? <Suspense fallback={<div className="surface-loading" role="status">正在载入画布…</div>}><AgentCanvas key={project} projectId={project} agents={agents} selectedAgent={agent} onSelect={chooseAgent} onFocus={focusAgent} onTerminal={terminalAgent}/></Suspense> : <>
      <section ref={viewportRef} className="conversation" aria-label="Agent 对话" tabIndex={0}><div ref={contentRef} className="conversation-content">
        {(conversationSource === 'native' ? nativeMessages.length : selectedJobs.length) > visibleCount && <button className="load-earlier" onClick={() => {pause(); setVisibleCount(value => value + 20);}}>显示更早的记录（当前显示最近 {visibleCount} 条）</button>}
        {conversationSource === 'native' && conversationError && <p className="muted small" role="status">{conversationError}</p>}
        {!(conversationSource === 'native' ? nativeMessages.length : selectedJobs.length) && <div className="welcome"><span className="welcome-icon"><IconBolt size={25} stroke={1.6}/></span><span className="welcome-kicker">{text(projectRecord?.display_name) || 'MUXARY WORKSPACE'}</span><h2>{targetReady ? '下一步，想构建什么？' : '先选择项目与 Agent'}</h2><p>{targetReady ? `和 ${agent} 从一个清晰的任务开始。` : project ? '从左侧选择运行中的 Agent，开始工作。' : '打开本机项目，连接你的 Agent 工作现场。'}<br/>计划、执行、检查，在这里接续。</p><Suggestions className="suggestion-grid" items={[
          {id: 'understand', icon: <IconCode size={18}/>, label: '理解这个项目', value: '请分析这个项目的结构和核心模块，先总结，不修改文件。'},
          {id: 'review', icon: <IconGitBranch size={18}/>, label: '检查当前变更', value: '请审查当前代码变更，指出潜在问题，暂不修改文件。'},
          {id: 'plan', icon: <IconMessage size={18}/>, label: '一起制定计划', value: '先了解当前项目，再和我一起制定下一步开发计划。'},
        ]} onSelect={item => {setDrafts(previous => ({...previous, [draftKey]: item.value || item.label})); document.querySelector<HTMLTextAreaElement>('.composer textarea')?.focus();}} disabled={!targetReady || uncertain || busy}/><span className="template-note">快捷任务模板 · 选择后编辑，不会直接发送</span><span className="welcome-note">基于 CCB 原生运行时 · 不改变你的 Agent 工作方式</span></div>}
        {conversationSource === 'native' && nativeMessages.slice(-visibleCount).map(message => <article key={message.id} className={`message ${message.role}`}><div className="message-label">{message.role === 'user' ? '你' : agent}<span>{message.source.startsWith('provider_native') ? '原生会话' : '会话记录'}</span></div><MessageContent id={message.id} content={message.body} user={message.role === 'user'}/></article>)}
        {conversationSource === 'tasks' && selectedJobs.slice(-visibleCount).map(job => {
          const body = text(row(job.request).body), reply = jobReply(job);
          return <div key={text(job.job_id)} className="job-turn">{body && <article className="message user"><div className="message-label">你<span>CCB 任务</span></div><MessageContent id={text(job.job_id)} content={body} user/></article>}
            <article className="message assistant"><div className="message-label"><span className="mini-agent"><IconCommand size={12}/></span>{agent}<Status status={job.status}/><span className="job-id">{text(job.job_id).slice(-10)}</span></div>{reply && <MessageContent id={text(job.job_id)} content={reply}/>}{!reply && !terminalStates.has(text(job.status)) && <div className="working"><IconLoader2 size={15} className="spin"/>等待原生 Agent 的完成证据…<button onClick={() => setTerminal(true)}>查看终端</button></div>}{!reply && terminalStates.has(text(job.status)) && <p className="muted">{text(row(job.terminal_decision).reason) || '此任务没有可展示的文本结果。'}</p>}{reply && <button className="copy-reply" onClick={() => copy(reply)}>{copied === reply ? <IconCheck size={14}/> : <IconCopy size={14}/>}复制结果</button>}</article>
          </div>;
        })}</div>
      </section>
      {!following && <button className="follow-latest" onClick={jumpToLatest}><IconArrowDown size={13}/>回到最新</button>}
      <div className="composer">
        <InputBar key={draftKey} value={draft} onChange={value => setDrafts(previous => ({...previous, [draftKey]: value}))} onSend={message => {void submit(message.content);}} status="ready" onStop={() => {}} disabled={!targetReady || network !== 'ok' || uncertain || busy} placeholder={uncertain ? '请先核对上一条请求是否已接收' : `给 ${agent || 'Agent'} 一个任务，或一起讨论…`}
          leftActions={<div className="composer-target"><span className="agent-dot"/><strong>{agent ? `发送给 ${agent}` : '未选择 Agent'}</strong><span>{text(agentRecord?.provider) || 'CCB'}</span><span className="composer-mode">CCB 任务</span></div>}/>
        <div className="composer-footnote"><span>{busy ? '正在确认任务接收，请勿重复发送…' : !targetReady ? '选择项目与 Agent 后即可派活' : conversationSource === 'native' ? '当前发送仍创建 CCB 任务，不写入原生会话' : 'Enter 发送 · Shift + Enter 换行 · 中文输入法确认不发送'}</span><span><span className={`health-dot ${network === 'ok' ? 'connected' : ''}`}/>{network === 'ok' ? 'CCB 已连接' : network === 'loading' ? '正在连接' : '连接中断'}</span></div>
        {uncertain && <div className="uncertain"><span>上一条请求状态未知，未自动重发。先核对任务与终端。</span><button onClick={() => {if (confirm('确认已在任务列表或原生终端核对，且理解新发送会创建新任务？')) {sessionStorage.removeItem(pendingKey(project, agent)); setUncertain(false);}}}>已核对，恢复编辑</button></div>}
      </div>
      </>}</div></ResizablePanel>{terminal && agent && <><ResizableHandle aria-label="调整终端高度" withHandle/><ResizablePanel id="terminal" defaultSize="32%" minSize={140} maxSize="65%"><Suspense fallback={<div className="surface-loading" role="status">正在载入终端…</div>}><AgentTerminal project={project} agent={agent} epoch={epoch}/></Suspense></ResizablePanel></>}</ResizablePanelGroup>
      <footer className="statusbar"><span><IconCircle size={10}/>CCB 原生运行时</span><span>{presentation === 'canvas' && !context ? `${agents.length} 个 Agent · 概览视图` : activeJobs.length ? `${activeJobs.length} 个任务进行中` : '没有进行中的任务'}<span className="status-divider"/>Muxary 0.1</span></footer>
    </main>
    <aside id="context-panel" ref={contextElement} className="context-panel" aria-label="任务与上下文" tabIndex={-1} role={drawer === 'context' ? 'dialog' : undefined} aria-modal={drawer === 'context' || undefined} inert={!context || drawer === 'sidebar'}><div className="context-tabs"><button className={tab === 'tasks' ? 'selected' : ''} aria-pressed={tab === 'tasks'} onClick={() => setTab('tasks')}>任务<span>{jobs.length}</span></button><button className={tab === 'changes' ? 'selected' : ''} aria-pressed={tab === 'changes'} onClick={() => setTab('changes')}>代码变更</button><Button label="收起上下文" onClick={() => setContext(false)}><IconX size={15}/></Button></div>
      {tab === 'tasks' ? <div className="context-content"><div className="activity-heading"><div><h2>任务动态</h2><p>当前项目 · {activeJobs.length} 个进行中</p></div><IconHistory size={19}/></div><div className="task-filters" role="group" aria-label="项目任务筛选"><button aria-label="查看全部任务" aria-pressed={taskFilter === 'all'} onClick={() => setTaskFilter('all')}>全部 <span>{jobs.length}</span></button><button aria-label="仅看进行中任务" aria-pressed={taskFilter === 'active'} onClick={() => setTaskFilter('active')}>进行中 <span>{activeJobs.length}</span></button></div>{!contextJobs.length && <div className="tasks-empty"><IconHistory size={24} stroke={1.3}/><h3>{taskFilter === 'active' ? '暂无进行中的任务' : '任务会在这里接续'}</h3><p>{taskFilter === 'active' ? '切回“全部”查看已结束和失败的记录。' : '向当前 Agent 派活，进度和结果随时可见。切换 Agent 不会中断执行。'}</p></div>}{[...contextJobs].reverse().map(job => <article className={`task-card ${job.agent_name === agent ? '' : 'other-agent'}`} key={text(job.job_id)}><div><span>{text(job.agent_name)}</span><Status status={job.status}/></div><button className="task-body" title={`切换至 ${text(job.agent_name)}，不会发送消息`} onClick={() => focusAgent(text(job.agent_name))}>{text(row(job.request).body).slice(0, 130) || text(job.job_id)}</button><div className="task-footer"><button className="job-copy" title="复制完整任务 ID" onClick={() => copy(text(job.job_id))}><code>{text(job.job_id).slice(-10)}</code></button>{!terminalStates.has(text(job.status)) ? <button disabled={actionBusy[text(job.job_id)]} onClick={() => {void jobAction(job, 'cancel');}}><IconPlayerStop size={12}/>取消</button> : ['failed', 'incomplete', 'cancelled'].includes(text(job.status)) && <button disabled={actionBusy[text(job.job_id)]} onClick={() => {void jobAction(job, 'retry');}}><IconRefresh size={12}/>重试</button>}</div></article>)}<div className="context-note"><IconTerminal2 size={17}/><div><strong>需要接管？</strong><p>原生 CLI 的确认、审批和交互可在终端完成。不同 Agent 能力保持原样。</p><button onClick={() => setTerminal(true)}>打开原生终端<IconArrowUpRight size={13}/></button></div></div><div className="project-info"><div className="section-label">项目上下文</div><label>路径</label><code>{text(projectRecord?.root) || '未选择项目'}</code><label>当前 Provider</label><span>{text(agentRecord?.provider) || '—'}</span><label>运行边界</label><span>单机 · 原 CCB 编排</span></div></div> : <div className="diff-panel"><div className="diff-caption">目录的未暂存差异 · 非 Agent 产出归因<button onClick={() => {void refreshDiff();}} aria-label="刷新代码变更"><IconRefresh size={14}/></button></div>{text(diff.error) ? <p className="muted">{text(diff.error)}</p> : <><p className="diff-scope">{text(diff.workspace_path) || workspacePath}<br/>不含暂存或未跟踪文件</p><pre className="diff-stat">{text(diff.stat) || '暂无已跟踪文件变更'}</pre><pre className="diff-code">{text(diff.patch) || text(diff.diff)}</pre>{Boolean(diff.patch_truncated || diff.stat_truncated) && <p>差异过大，已截断；请在本机 Git 中查看完整内容。</p>}</>}</div>}
    </aside>
    <button className={`drawer-scrim ${sidebar ? 'for-sidebar' : ''} ${context ? 'for-context' : ''}`} tabIndex={-1} aria-label="关闭侧栏" onClick={() => {setSidebar(false); setContext(false);}}/>
    <dialog ref={openProjectDialog} className="project-dialog" aria-labelledby="open-project-title" aria-describedby="open-project-description" onCancel={() => setProjectDialog(false)} onClose={() => setProjectDialog(false)}>
      <form onSubmit={event => {event.preventDefault(); void openProject();}}>
        <div className="project-dialog-heading"><IconFolder size={20}/><h2 id="open-project-title">打开项目</h2><Button label="关闭打开项目" onClick={() => setProjectDialog(false)}><IconX size={17}/></Button></div>
        <p id="open-project-description">输入运行 Muxary 的这台电脑上的项目目录。已运行项目直接进入；其他目录通过原 CCB 安全启动配置中的 Agent，不自动重启已有 Agent。</p>
        <label htmlFor="project-directory">本机项目目录</label><input id="project-directory" autoFocus required maxLength={4096} placeholder="/home/me/my-project" value={projectDirectory} disabled={openingProject} onChange={event => setProjectDirectory(event.target.value)}/>
        <div className="project-open-boundary"><IconGitBranch size={15}/><span>工作树仍绑定于 Agent。在原 CCB 设置中配置、创建，按原流程确认重启后生效；不会静默切换运行目录。</span></div>
        {projectOpenError && <p role="alert">{projectOpenError}</p>}
        {uncertainDirectory && <button type="button" onClick={() => {setProjectDialog(false); setSidebar(true); setContext(false);}}>查看已挂载项目（列表自动只读刷新）</button>}
        {openingProject && <p role="status">正在通过 CCB 打开…关闭窗口不会取消已开始的启动。</p>}
        <div className="project-dialog-actions"><button type="button" onClick={() => setProjectDialog(false)}>关闭</button><button type="submit" disabled={openingProject || !projectDirectory.trim() || uncertainDirectory === projectDirectory}>{openingProject ? '正在打开…' : '通过 CCB 打开'}</button></div>
      </form>
    </dialog>
    <dialog ref={paletteDialog} className="command-dialog" aria-labelledby="command-title" onCancel={() => setPalette(false)} onClose={() => setPalette(false)}><h2 id="command-title" className="sr-only">跳转与操作</h2>{palette && <Command label="跳转与操作" filter={(value, search) => value.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()) ? 1 : 0}><CommandInput autoFocus placeholder="跳转项目、Agent 或视图…" aria-label="快速切换搜索"/><CommandList><CommandEmpty>没有匹配的项目或操作</CommandEmpty><CommandGroup heading="已挂载项目">{projects.map(item => <CommandItem key={text(item.id)} value={`project ${text(item.id)} ${text(item.display_name)} ${text(item.root)}`} onSelect={() => {setProject(text(item.id)); setPalette(false);}}><IconFolder size={16}/>{text(item.display_name) || text(item.id)}<small>{text(item.root)}</small></CommandItem>)}</CommandGroup><CommandGroup heading="当前项目 Agent">{agents.map(item => <CommandItem key={text(item.name)} value={`agent ${text(item.name)} ${text(item.provider)}`} onSelect={() => {chooseAgent(text(item.name)); setPalette(false);}}><IconCommand size={16}/>{text(item.name)}<small>{text(item.provider)}</small></CommandItem>)}</CommandGroup><CommandGroup heading="操作"><CommandItem onSelect={() => {setPalette(false); setProjectDialog(true);}}>打开本机项目目录</CommandItem><CommandItem onSelect={() => {setPresentation('focus'); setPalette(false);}}>专注视图</CommandItem><CommandItem onSelect={() => {setPresentation('canvas'); setPalette(false);}}>并行画布</CommandItem><CommandItem disabled={!targetReady} onSelect={() => {terminalAgent(agent); setPalette(false);}}>接管当前 Agent 终端</CommandItem><CommandItem disabled={!project} onSelect={() => {void openSettings(); setPalette(false);}}>原 CCB 项目设置</CommandItem></CommandGroup></CommandList></Command>}<div className="command-footer">↑↓ 选择 · Enter 跳转<button onClick={() => setPalette(false)}>Esc 关闭</button></div></dialog>
    <dialog ref={helpDialog} className="help-dialog" aria-labelledby="help-title" onCancel={() => setHelp(false)} onClose={() => setHelp(false)}><Button label="关闭说明" onClick={() => setHelp(false)}><IconX size={18}/></Button><h2 id="help-title">保持专注，顺手就好。</h2><p>选择项目和 Agent，输入任务。任务通过原 CCB dispatcher 执行；刷新页面不会重新提交任务。</p><dl><dt>Enter</dt><dd>发送任务（中文输入法确认除外）</dd><dt>Shift + Enter</dt><dd>换行</dd><dt>⌘ / Ctrl + K</dt><dd>快速切换项目、Agent 和视图</dd></dl><p>终端直连原生 CLI；审批能力以实际 CLI 为准。设置仍使用原 CCB 配置与激活流程。</p><button className="primary" onClick={() => setHelp(false)}>开始工作</button></dialog>
  </div>;
}
