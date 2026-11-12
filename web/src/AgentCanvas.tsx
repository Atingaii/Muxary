import { memo, useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Background, BackgroundVariant, ReactFlow, type Edge, type Node, type NodeChange, type NodeProps, type ReactFlowInstance, type Viewport, type XYPosition } from '@xyflow/react';
import { IconArrowsMaximize, IconFocus2, IconLayoutGrid, IconList, IconSearch, IconTerminal2, IconZoomIn, IconZoomOut } from '@tabler/icons-react';
import { Card, CardContent, CardFooter, CardHeader } from './vendor/shadcn/card';
import { row, statusLabel, text, type Row } from './model';
import '@xyflow/react/dist/style.css';
import './canvas.css';

export type AgentCanvasProps = {
  projectId: string;
  agents: Row[];
  selectedAgent: string;
  onSelect: (agent: string) => void;
  onFocus: (agent: string) => void;
  onTerminal: (agent: string) => void;
};

const MAX_AGENTS = 100;
const MAX_PROJECTS = 20;
const MAX_STORAGE_BYTES = 256 * 1024;
const STORAGE_KEY = 'muxary.canvas.layout.v1';
const CARD_WIDTH = 264;
const CARD_HEIGHT = 186;
const COMPACT_ZOOM = 0.5;
const DEFAULT_VIEWPORT: Viewport = {x: 36, y: 36, zoom: 0.9};
const NO_EDGES: Edge[] = [];
const ARIA_LABELS = {
  'node.a11yDescription.default': '按 Enter 或空格选择 Agent，使用方向键移动卡片。也可切换到列表操作。',
  'node.a11yDescription.keyboardDisabled': '按 Enter 或空格选择 Agent。也可切换到列表操作。',
};
// A build-time, opt-in performance ablation. No URL/query or persisted setting
// can enable it in a normal production build. Default remains false.
const ONLY_RENDER_VISIBLE_ELEMENTS = import.meta.env.MODE === 'canvas-perf-culling';

type AgentSummary = {name: string; provider: string; state: string; workspace: string; queued: number};
type AgentNodeData = AgentSummary & {
  onSelect: (name: string) => void;
  onFocus: (name: string) => void;
  onTerminal: (name: string) => void;
};
type AgentNode = Node<AgentNodeData, 'agent'>;
type SavedProject = {projectId: string; positions: {id: string; x: number; y: number}[]; viewport?: Viewport};

function isCoordinate(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= 100_000;
}
function readProjects(): SavedProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw || raw.length > MAX_STORAGE_BYTES) return [];
    const stored = row(JSON.parse(raw));
    if (stored.version !== 1 || !Array.isArray(stored.projects)) return [];
    return stored.projects.slice(0, MAX_PROJECTS).flatMap(value => {
      const item = row(value);
      if (typeof item.projectId !== 'string' || item.projectId.length > 1024 || !Array.isArray(item.positions)) return [];
      const positions = item.positions.slice(0, MAX_AGENTS).flatMap(value => {
        const point = row(value);
        return typeof point.id === 'string' && point.id.length <= 256 && isCoordinate(point.x) && isCoordinate(point.y)
          ? [{id: point.id, x: point.x, y: point.y}] : [];
      });
      const view = row(item.viewport);
      const viewport = isCoordinate(view.x) && isCoordinate(view.y) && typeof view.zoom === 'number' && view.zoom >= 0.1 && view.zoom <= 1.5
        ? {x: view.x, y: view.y, zoom: view.zoom} : undefined;
      return [{projectId: item.projectId, positions, viewport}];
    });
  } catch {return []; /* Browser layout preferences never gate CCB use. */}
}
function saveProject(projectId: string, positions: Map<string, XYPosition>, viewport: Viewport): void {
  if (!projectId || projectId.length > 1024) return;
  const entry: SavedProject = {projectId, positions: Array.from(positions, ([id, point]) => ({id, ...point})).filter(point => point.id.length <= 256).slice(0, MAX_AGENTS), viewport};
  const projects = [entry, ...readProjects().filter(item => item.projectId !== projectId)].slice(0, MAX_PROJECTS);
  let payload = JSON.stringify({version: 1, projects});
  while (payload.length > MAX_STORAGE_BYTES && projects.length > 1) {
    projects.pop(); payload = JSON.stringify({version: 1, projects});
  }
  if (payload.length > MAX_STORAGE_BYTES) return;
  try {localStorage.setItem(STORAGE_KEY, payload);} catch { /* Optional, local-only preference. */ }
}
function defaultPosition(index: number, count: number): XYPosition {
  const columns = Math.max(1, Math.ceil(Math.sqrt(count)));
  return {x: (index % columns) * (CARD_WIDTH + 32), y: Math.floor(index / columns) * (CARD_HEIGHT + 30)};
}
function summarize(agents: Row[]): AgentSummary[] {
  const names = new Set<string>();
  return agents.slice(0, MAX_AGENTS).flatMap(agent => {
    const name = text(agent.name);
    if (!name || names.has(name)) return [];
    names.add(name);
    const workspace = (text(agent.workspace_path) || text(row(agent.runtime).workspace_path)).replace(/\\/g, '/').replace(/\/+$/, '').split('/').pop() || text(row(agent.workspace).basename);
    return [{name, provider: text(agent.provider).slice(0, 80) || '未知 Provider',
      state: (text(agent.activity_state) || text(agent.state) || text(agent.status) || 'unknown').slice(0, 64),
      workspace: workspace.slice(0, 120), queued: typeof agent.queue_depth === 'number' && Number.isFinite(agent.queue_depth) ? Math.max(0, Math.floor(agent.queue_depth)) : 0}];
  });
}
function activityLabel(state: string): string {
  return ({active: '执行中', working: '执行中', pending: '待处理', unknown: '状态未知'}[state] ?? statusLabel(state));
}
function AgentCard({data, selected}: {data: AgentNodeData; selected: boolean}) {
  return <Card className={`canvas-agent-card ${selected ? 'is-selected' : ''}`}>
    <CardHeader className="canvas-agent-header">
      <span className="canvas-agent-avatar" aria-hidden="true">{data.name.slice(0, 1).toUpperCase()}</span>
      <div className="canvas-agent-identity"><button type="button" className="canvas-agent-select nodrag nopan" aria-label={`选择 ${data.name}`} aria-pressed={selected} onClick={event => {event.stopPropagation(); data.onSelect(data.name);}}>{data.name}</button><span>{data.provider}</span></div>
      <span className={`canvas-agent-state ${['active', 'working', 'running'].includes(data.state) ? 'is-working' : ''}`}><i aria-hidden="true"/>{activityLabel(data.state)}</span>
    </CardHeader>
    <CardContent className="canvas-agent-content"><span>运行摘要</span><p>{data.queued ? `${data.queued} 项活动或排队任务` : '使用原 CCB 会话'}{data.workspace && <><span aria-hidden="true"> · </span><span className="canvas-workspace">{data.workspace}</span></>}</p></CardContent>
    <CardFooter className="canvas-agent-footer"><button type="button" className="nodrag nopan" aria-label={`专注 ${data.name}`} onClick={event => {event.stopPropagation(); data.onFocus(data.name);}}><IconFocus2 size={14}/>专注</button><button type="button" className="nodrag nopan" aria-label={`打开 ${data.name} 的终端`} onClick={event => {event.stopPropagation(); data.onTerminal(data.name);}}><IconTerminal2 size={14}/>终端</button></CardFooter>
  </Card>;
}
const AgentFlowNode = memo(function AgentFlowNode({data, selected}: NodeProps<AgentNode>) {
  return <AgentCard data={data} selected={Boolean(selected)}/>;
}, (before, after) => before.selected === after.selected && before.data.name === after.data.name && before.data.provider === after.data.provider
  && before.data.state === after.data.state && before.data.workspace === after.data.workspace && before.data.queued === after.data.queued
  && before.data.onSelect === after.data.onSelect && before.data.onFocus === after.data.onFocus && before.data.onTerminal === after.data.onTerminal);
const NODE_TYPES = {agent: AgentFlowNode};

function ProjectCanvas({projectId, agents, selectedAgent, onSelect, onFocus, onTerminal}: AgentCanvasProps) {
  const [saved] = useState(() => readProjects().find(item => item.projectId === projectId));
  const [positions, setPositions] = useState(() => new Map(saved?.positions.map(point => [point.id, {x: point.x, y: point.y}])));
  const [filter, setFilter] = useState('');
  const [presentation, setPresentation] = useState<'canvas' | 'list'>(() => typeof matchMedia === 'function' && matchMedia('(max-width: 680px)').matches ? 'list' : 'canvas');
  const [compact, setCompact] = useState((saved?.viewport?.zoom ?? DEFAULT_VIEWPORT.zoom) < COMPACT_ZOOM);
  const flow = useRef<ReactFlowInstance<AgentNode> | null>(null);
  const viewport = useRef(saved?.viewport ?? DEFAULT_VIEWPORT);
  const compactRef = useRef(compact);
  const positionsRef = useRef(positions);
  useLayoutEffect(() => {positionsRef.current = positions;}, [positions]);
  const callbacks = useRef({onSelect, onFocus, onTerminal});
  useLayoutEffect(() => {callbacks.current = {onSelect, onFocus, onTerminal};}, [onSelect, onFocus, onTerminal]);
  const selectAgent = useCallback((name: string) => callbacks.current.onSelect(name), []);
  const focusAgent = useCallback((name: string) => {callbacks.current.onSelect(name); callbacks.current.onFocus(name);}, []);
  const terminalAgent = useCallback((name: string) => {callbacks.current.onSelect(name); callbacks.current.onTerminal(name);}, []);
  // Poll responses may contain fresh Row objects or large irrelevant fields.
  // Keep only bounded summaries, and retain their identity when unchanged.
  const summaryJSON = JSON.stringify(summarize(agents));
  const summaries = useMemo<AgentSummary[]>(() => JSON.parse(summaryJSON), [summaryJSON]);
  const visible = useMemo(() => summaries.filter(item => `${item.name} ${item.provider} ${item.workspace}`.toLocaleLowerCase().includes(filter.trim().toLocaleLowerCase())), [summaries, filter]);
  const visibleNames = useMemo(() => new Set(visible.map(item => item.name)), [visible]);
  const nodeData = useMemo(() => new Map(summaries.map(item => [item.name, {...item, onSelect: selectAgent, onFocus: focusAgent, onTerminal: terminalAgent}])), [summaries, selectAgent, focusAgent, terminalAgent]);
  useLayoutEffect(() => {
    setPositions(previous => {
      const next = new Map<string, XYPosition>();
      summaries.forEach((item, index) => next.set(item.name, previous.get(item.name) ?? defaultPosition(index, summaries.length)));
      return next.size === previous.size && Array.from(next).every(([name, point]) => previous.get(name) === point) ? previous : next;
    });
  }, [summaries]);
  const nodes = useMemo<AgentNode[]>(() => summaries.map((item, index) => ({id: item.name, type: 'agent',
    data: nodeData.get(item.name)!, position: positions.get(item.name) ?? defaultPosition(index, summaries.length),
    selected: item.name === selectedAgent, hidden: !visibleNames.has(item.name),
    width: CARD_WIDTH, height: CARD_HEIGHT, deletable: false, connectable: false,
    ariaLabel: `${item.name}，${item.provider}，${activityLabel(item.state)}`})), [summaries, nodeData, positions, selectedAgent, visibleNames]);
  const onNodesChange = useCallback((changes: NodeChange<AgentNode>[]) => {
    const moves = changes.filter(change => change.type === 'position' && change.position);
    if (moves.length) {
      const next = new Map(positionsRef.current);
      for (const move of moves) if (move.type === 'position' && move.position && isCoordinate(move.position.x) && isCoordinate(move.position.y)) next.set(move.id, move.position);
      positionsRef.current = next; setPositions(next);
      // In pinned React Flow 12.12.1, both pointer-drag completion and
      // keyboard movement emit position changes with dragging=false.
      // Persist this boundary, never every pointer-move frame.
      if (moves.some(move => move.type === 'position' && move.dragging === false)) saveProject(projectId, next, viewport.current);
    }
    const selection = changes.find(change => change.type === 'select' && change.selected);
    if (selection?.type === 'select') selectAgent(selection.id);
  }, [selectAgent, projectId]);
  const onInit = useCallback((instance: ReactFlowInstance<AgentNode>) => {flow.current = instance;}, []);
  const onNodeClick = useCallback((_event: React.MouseEvent, node: AgentNode) => selectAgent(node.id), [selectAgent]);
  const onNodeDoubleClick = useCallback((_event: React.MouseEvent, node: AgentNode) => focusAgent(node.id), [focusAgent]);
  const onMove = useCallback((_event: MouseEvent | TouchEvent | null, next: Viewport) => {
    viewport.current = next;
    const nextCompact = next.zoom < COMPACT_ZOOM;
    if (nextCompact !== compactRef.current) {compactRef.current = nextCompact; setCompact(nextCompact);}
  }, []);
  const onMoveEnd = useCallback((_event: MouseEvent | TouchEvent | null, next: Viewport) => {
    viewport.current = next; saveProject(projectId, positionsRef.current, next);
  }, [projectId]);
  const arrange = () => {
    const next = new Map(summaries.map((item, index) => [item.name, defaultPosition(index, summaries.length)]));
    positionsRef.current = next; setPositions(next); saveProject(projectId, next, viewport.current);
  };
  const fit = () => {void flow.current?.fitView({padding: 0.2, maxZoom: 1, duration: 0});};

  return <section className="agent-canvas" aria-label="多 Agent 画布">
    <header className="canvas-toolbar"><div className="canvas-title"><IconLayoutGrid size={17}/><strong>Agent 全景</strong><span>{visible.length} / {summaries.length}</span></div><div className="canvas-presentation" role="group" aria-label="Agent 展示方式"><button type="button" aria-pressed={presentation === 'canvas'} onClick={() => setPresentation('canvas')}><IconLayoutGrid size={14}/>画布</button><button type="button" aria-pressed={presentation === 'list'} onClick={() => setPresentation('list')}><IconList size={14}/>列表</button></div></header>
    <div className="canvas-actions"><label className="canvas-filter"><IconSearch size={15}/><input aria-label="筛选画布 Agent" placeholder="搜索 Agent、Provider 或目录" maxLength={128} value={filter} onChange={event => setFilter(event.target.value)}/></label>{presentation === 'canvas' && <div className="canvas-view-actions"><button type="button" onClick={arrange} disabled={!summaries.length}><IconLayoutGrid size={14}/>自动排列</button><button type="button" onClick={fit} disabled={!visible.length}><IconArrowsMaximize size={14}/>适应视图</button></div>}</div>
    {agents.length > MAX_AGENTS && <p className="canvas-limit" role="status">当前画布最多展示前 {MAX_AGENTS} 个 Agent；其余 Agent 请从项目栏选择。</p>}
    {!visible.length ? <div className="canvas-empty"><IconLayoutGrid size={30} stroke={1.2}/><h2>{summaries.length ? '没有匹配的 Agent' : '这里是项目的 Agent 全景'}</h2><p>{summaries.length ? '试试其他名称、Provider 或目录。' : '启动项目中的 CCB Agent 后，它们会出现在这里。'}</p>{filter && <button type="button" onClick={() => setFilter('')}>清除筛选</button>}</div>
      : presentation === 'list' ? <ul className="canvas-agent-list" aria-label="Agent 列表">{visible.map(item => <li key={item.name}><AgentCard data={nodeData.get(item.name)!} selected={item.name === selectedAgent}/></li>)}</ul>
      : <div className={`canvas-surface ${compact ? 'is-compact' : ''}`}><ReactFlow<AgentNode> nodes={nodes} edges={NO_EDGES} nodeTypes={NODE_TYPES} onInit={onInit} onNodesChange={onNodesChange} onNodeClick={onNodeClick} onNodeDoubleClick={onNodeDoubleClick} onMove={onMove} onMoveEnd={onMoveEnd}
        defaultViewport={viewport.current} minZoom={0.1} maxZoom={1.5} nodesConnectable={false} edgesFocusable={false} deleteKeyCode={null} multiSelectionKeyCode={null} selectionKeyCode={null} selectNodesOnDrag={false}
        zoomOnDoubleClick={false} onlyRenderVisibleElements={ONLY_RENDER_VISIBLE_ELEMENTS} ariaLabelConfig={ARIA_LABELS} aria-label="可平移缩放的 Agent 画布">
        <Background variant={BackgroundVariant.Dots} gap={22} size={1}/>
      </ReactFlow><div className="canvas-zoom" role="group" aria-label="画布缩放"><button type="button" aria-label="缩小画布" onClick={() => {void flow.current?.zoomOut({duration: 0});}}><IconZoomOut size={17}/></button><button type="button" aria-label="放大画布" onClick={() => {void flow.current?.zoomIn({duration: 0});}}><IconZoomIn size={17}/></button></div></div>}
    <footer className="canvas-hint">{presentation === 'canvas' ? '拖动卡片整理布局 · 拖动空白处平移 · 滚轮缩放' : 'Tab 选择操作 · Enter 执行 · 与专注视图使用同一 Agent'}<span>仅展示摘要，不额外订阅终端或会话</span></footer>
  </section>;
}

export function AgentCanvas(props: AgentCanvasProps) {
  // Project-scoped UI preferences never replace CCB sessions or runtime state.
  return <ProjectCanvas key={props.projectId} {...props}/>;
}
