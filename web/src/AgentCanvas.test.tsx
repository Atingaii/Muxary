// @vitest-environment jsdom
// The engine is mocked to test the adapter's resource/ownership contracts, not
// pointer geometry, browser frame time, or React Flow's own implementation.
import React from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Node, NodeProps, ReactFlowProps } from '@xyflow/react';
import { AgentCanvas, type AgentCanvasProps } from './AgentCanvas';

const engine = vi.hoisted(() => ({props: undefined as ReactFlowProps | undefined}));
vi.mock('@xyflow/react', () => ({
  BackgroundVariant: {Dots: 'dots'}, Background: () => null,
  ReactFlow: (props: ReactFlowProps) => {
    engine.props = props;
    return <div data-testid="flow-engine">{props.nodes?.filter(node => !node.hidden).map(node => {
      const Component = props.nodeTypes?.[node.type ?? ''];
      const nodeProps: NodeProps = {id: node.id, data: node.data, type: node.type ?? '', selected: Boolean(node.selected),
        positionAbsoluteX: node.position.x, positionAbsoluteY: node.position.y, dragging: false, zIndex: 0,
        draggable: true, selectable: true, deletable: false, isConnectable: false};
      return Component ? <Component key={node.id} {...nodeProps}/> : null;
    })}</div>;
  },
}));

const STORAGE_KEY = 'muxary.canvas.layout.v1';
const agents = [
  {name: 'buddy', provider: 'codebuddy', activity_state: 'active', queue_depth: 2, workspace_path: '/private/dev/first-project', runtime: {workspace_path: '/wrong/ignored'}},
  {name: 'reviewer', provider: 'claude', state: 'idle', runtime: {workspace_path: 'C:\\private\\second-project'}},
];
function props(overrides: Partial<AgentCanvasProps> = {}): AgentCanvasProps {
  return {projectId: 'project-a', agents, selectedAgent: 'buddy', onSelect: vi.fn(), onFocus: vi.fn(), onTerminal: vi.fn(), ...overrides};
}
function flow(): ReactFlowProps {
  if (!engine.props) throw new Error('Expected mounted React Flow adapter');
  return engine.props;
}
function firstNode(): Node {
  const node = flow().nodes?.[0];
  if (!node) throw new Error('Expected first Agent node');
  return node;
}
function dragFirst(x: number, y: number): void {
  const node = {...firstNode(), position: {x, y}};
  act(() => flow().onNodesChange?.([{type: 'position', id: node.id, position: node.position, dragging: true}]));
  act(() => flow().onNodesChange?.([{type: 'position', id: node.id, position: node.position, dragging: false}]));
}
beforeEach(() => {
  localStorage.clear(); engine.props = undefined;
  vi.stubGlobal('matchMedia', () => ({matches: false}));
  vi.stubGlobal('fetch', vi.fn()); vi.stubGlobal('WebSocket', vi.fn());
});
afterEach(() => {cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals();});

describe('Agent canvas adapter', () => {
  it('prefers canonical project-view workspace_path over a conflicting legacy runtime field', () => {
    render(<AgentCanvas {...props({agents: [{name: 'buddy', workspace_path: '/canonical/current-worktree', runtime: {workspace_path: '/legacy/stale-worktree'}}]})}/>);
    expect(screen.getByText('current-worktree')).toBeTruthy();
    expect(screen.queryByText('stale-worktree')).toBeNull();
    expect(document.body.textContent).not.toContain('/canonical/');
  });
  it('renders bounded runtime summaries, not transcripts or full workspace paths', () => {
    render(<AgentCanvas {...props({agents: [{...agents[0], transcript: 'PRIVATE_TRANSCRIPT', request: {body: 'PRIVATE_TASK'}}]})}/>);
    expect(screen.getByText('执行中')).toBeTruthy();
    expect(screen.getByText('first-project')).toBeTruthy();
    expect(screen.getByText(/2 项活动或排队任务/)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/PRIVATE_TRANSCRIPT|PRIVATE_TASK|\/private\/dev|ignored/);
    expect(fetch).not.toHaveBeenCalled(); expect(WebSocket).not.toHaveBeenCalled();
  });
  it('shares controlled selection and delegates focus/terminal actions by Agent name', () => {
    const value = props(); const mounted = render(<AgentCanvas {...value}/>);
    fireEvent.click(screen.getByRole('button', {name: '选择 reviewer'}));
    expect(value.onSelect).toHaveBeenCalledExactlyOnceWith('reviewer');
    expect(screen.getByRole('button', {name: '选择 buddy'}).getAttribute('aria-pressed')).toBe('true');
    mounted.rerender(<AgentCanvas {...value} selectedAgent="reviewer"/>);
    expect(screen.getByRole('button', {name: '选择 reviewer'}).getAttribute('aria-pressed')).toBe('true');
    fireEvent.click(screen.getByRole('button', {name: '专注 reviewer'}));
    expect(value.onFocus).toHaveBeenCalledExactlyOnceWith('reviewer');
    fireEvent.click(screen.getByRole('button', {name: '打开 buddy 的终端'}));
    expect(value.onTerminal).toHaveBeenCalledExactlyOnceWith('buddy');
    expect(value.onSelect).toHaveBeenLastCalledWith('buddy');
    expect(fetch).not.toHaveBeenCalled(); expect(WebSocket).not.toHaveBeenCalled();
  });
  it('has a keyboard-operable native-button list fallback without a second mounted canvas', () => {
    const value = props(); render(<AgentCanvas {...value}/>);
    fireEvent.click(screen.getByRole('button', {name: '列表'}));
    expect(screen.queryByTestId('flow-engine')).toBeNull();
    expect(screen.getByRole('list', {name: 'Agent 列表'})).toBeTruthy();
    const choice = screen.getByRole('button', {name: '选择 reviewer'});
    choice.focus(); expect(document.activeElement).toBe(choice);
    fireEvent.click(choice); expect(value.onSelect).toHaveBeenCalledWith('reviewer');
    expect(screen.getAllByRole('button', {name: /^选择 /})).toHaveLength(2);
  });
  it('starts with the simpler list fallback on narrow screens', () => {
    vi.stubGlobal('matchMedia', () => ({matches: true}));
    render(<AgentCanvas {...props()}/>);
    expect(screen.getByRole('list', {name: 'Agent 列表'})).toBeTruthy();
    expect(screen.queryByTestId('flow-engine')).toBeNull();
    fireEvent.click(screen.getByRole('button', {name: '画布'}));
    expect(screen.getByTestId('flow-engine')).toBeTruthy();
  });
  it('filters name/provider/basename without changing selection or positions', () => {
    const value = props(); render(<AgentCanvas {...value}/>);
    dragFirst(441, 228);
    fireEvent.change(screen.getByRole('textbox', {name: '筛选画布 Agent'}), {target: {value: 'SECOND-PROJECT'}});
    expect(screen.queryByRole('button', {name: '选择 buddy'})).toBeNull();
    expect(screen.getByRole('button', {name: '选择 reviewer'})).toBeTruthy();
    expect(firstNode().position).toEqual({x: 441, y: 228});
    expect(value.onSelect).not.toHaveBeenCalled();
    fireEvent.change(screen.getByRole('textbox', {name: '筛选画布 Agent'}), {target: {value: 'codebuddy'}});
    expect(screen.getByRole('button', {name: '选择 buddy'})).toBeTruthy();
    expect(screen.queryByRole('button', {name: '选择 reviewer'})).toBeNull();
  });
  it('provides honest empty and no-match states', () => {
    const mounted = render(<AgentCanvas {...props({agents: []})}/>);
    expect(screen.getByText('这里是项目的 Agent 全景')).toBeTruthy();
    expect(screen.queryByTestId('flow-engine')).toBeNull();
    mounted.rerender(<AgentCanvas {...props()}/>);
    fireEvent.change(screen.getByRole('textbox', {name: '筛选画布 Agent'}), {target: {value: 'missing'}});
    expect(screen.getByText('没有匹配的 Agent')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', {name: '清除筛选'}));
    expect(screen.getByRole('button', {name: '选择 buddy'})).toBeTruthy();
  });
  it('retains manual positions and viewport across unmount without auto-fit', () => {
    const value = props(); const mounted = render(<AgentCanvas {...value}/>);
    dragFirst(513, -42);
    act(() => flow().onMoveEnd?.(null, {x: -36, y: 77, zoom: 0.65}));
    mounted.unmount(); render(<AgentCanvas {...value}/>);
    expect(firstNode().position).toEqual({x: 513, y: -42});
    expect(flow().defaultViewport).toEqual({x: -36, y: 77, zoom: 0.65});
    expect(flow().fitView).toBeUndefined();
    const stored = localStorage.getItem(STORAGE_KEY) ?? '';
    expect(stored).not.toMatch(/provider|workspace_path|transcript|codebuddy/);
  });
  it('scopes saved positions to project identity, even when Agent names match', () => {
    const value = props(); const mounted = render(<AgentCanvas {...value}/>);
    dragFirst(600, 700);
    mounted.rerender(<AgentCanvas {...value} projectId="project-b"/>);
    expect(firstNode().position).toEqual({x: 0, y: 0});
    mounted.rerender(<AgentCanvas {...value}/>);
    expect(firstNode().position).toEqual({x: 600, y: 700});
  });
  it('does not reposition or rebuild node data on unchanged poll responses', () => {
    const value = props(); const mounted = render(<AgentCanvas {...value}/>);
    dragFirst(345, 123);
    const data = firstNode().data;
    mounted.rerender(<AgentCanvas {...value} agents={agents.map(agent => ({...agent, irrelevant_large_body: 'ignored'.repeat(1000)}))}/>);
    expect(firstNode().position).toEqual({x: 345, y: 123});
    expect(firstNode().data).toBe(data);
    mounted.rerender(<AgentCanvas {...value} agents={[agents[1], {...agents[0], activity_state: 'idle'}]}/>);
    expect(flow().nodes?.find(node => node.id === 'buddy')?.position).toEqual({x: 345, y: 123});
  });
  it('keeps drag updates in memory until completion and explicitly arranges on request', () => {
    render(<AgentCanvas {...props()}/>);
    const writes = vi.spyOn(Storage.prototype, 'setItem');
    act(() => flow().onNodesChange?.([{type: 'position', id: 'buddy', position: {x: 300, y: 40}, dragging: true}]));
    expect(writes).not.toHaveBeenCalled();
    dragFirst(800, 500); expect(writes).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole('button', {name: '自动排列'}));
    expect(firstNode().position).toEqual({x: 0, y: 0});
    expect(writes).toHaveBeenCalledTimes(2);
  });
  it('does not create edges, a scheduler, or configurable production culling', () => {
    render(<AgentCanvas {...props()}/>);
    expect(flow().edges).toEqual([]);
    expect(flow().nodesConnectable).toBe(false);
    expect(flow().deleteKeyCode).toBeNull();
    expect(flow().onlyRenderVisibleElements).toBe(false);
    expect(firstNode().deletable).toBe(false);
    expect(firstNode().connectable).toBe(false);
    expect(fetch).not.toHaveBeenCalled(); expect(WebSocket).not.toHaveBeenCalled();
  });
  it('bounds summary nodes and makes the capacity boundary visible', () => {
    const many = Array.from({length: 105}, (_, index) => ({name: `agent-${index}`, provider: 'codebuddy'}));
    render(<AgentCanvas {...props({agents: many})}/>);
    expect(flow().nodes).toHaveLength(100);
    expect(screen.getByRole('status').textContent).toContain('前 100 个 Agent');
    expect(screen.getAllByRole('button', {name: /^选择 /})).toHaveLength(100);
  });
  it('ignores malformed, oversized and out-of-range optional preferences', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({version: 1, projects: [{projectId: 'project-a', positions: [{id: 'buddy', x: 'bad', y: 1}], viewport: {x: 0, y: 0, zoom: 99}}]}));
    const value = props(); let mounted = render(<AgentCanvas {...value}/>);
    expect(firstNode().position).toEqual({x: 0, y: 0});
    expect(flow().defaultViewport).toEqual({x: 36, y: 36, zoom: 0.9});
    mounted.unmount(); localStorage.setItem(STORAGE_KEY, '{bad json');
    mounted = render(<AgentCanvas {...value}/>); expect(firstNode().position).toEqual({x: 0, y: 0});
    mounted.unmount(); localStorage.setItem(STORAGE_KEY, 'x'.repeat(256 * 1024 + 1));
    render(<AgentCanvas {...value}/>); expect(firstNode().position).toEqual({x: 0, y: 0});
  });
  it('bounds saved projects and remains usable when browser storage is blocked', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({version: 1, projects: Array.from({length: 25}, (_, index) => ({projectId: `old-${index}`, positions: []}))}));
    const value = props(); render(<AgentCanvas {...value}/>);
    fireEvent.click(screen.getByRole('button', {name: '自动排列'}));
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '{}');
    expect(stored.projects).toHaveLength(20); expect(stored.projects[0].projectId).toBe('project-a');
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {throw new DOMException('blocked');});
    fireEvent.click(screen.getByRole('button', {name: '自动排列'}));
    fireEvent.click(screen.getByRole('button', {name: '选择 reviewer'}));
    expect(value.onSelect).toHaveBeenCalledWith('reviewer');
  });
  it('does not fabricate ready status or duplicate unnamed/duplicate Agents', () => {
    render(<AgentCanvas {...props({agents: [{name: 'buddy'}, {name: 'buddy'}, {provider: 'codebuddy'}]})}/>);
    expect(flow().nodes).toHaveLength(1);
    expect(screen.getByText('状态未知')).toBeTruthy();
    expect(screen.queryByText('就绪')).toBeNull();
  });
  it('keeps selecting Agents when browser preference reads are blocked', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {throw new DOMException('blocked');});
    const value = props(); render(<AgentCanvas {...value}/>);
    fireEvent.click(screen.getByRole('button', {name: '选择 buddy'}));
    expect(value.onSelect).toHaveBeenCalledWith('buddy');
  });
  it('persists completed keyboard moves without relying on pointer drag callbacks', () => {
    const value = props(); const mounted = render(<AgentCanvas {...value}/>);
    act(() => flow().onNodesChange?.([{type: 'position', id: 'buddy', position: {x: 15, y: 5}, dragging: false}]));
    mounted.unmount(); render(<AgentCanvas {...value}/>);
    expect(firstNode().position).toEqual({x: 15, y: 5});
  });
  it('changes semantic zoom only at its threshold while retaining node data and geometry', () => {
    const mounted = render(<AgentCanvas {...props()}/>);
    const nodes = flow().nodes;
    act(() => flow().onMove?.(null, {x: 0, y: 0, zoom: 0.4}));
    expect(mounted.container.querySelector('.canvas-surface.is-compact')).toBeTruthy();
    expect(flow().nodes).toBe(nodes);
    act(() => flow().onMove?.(null, {x: -100, y: 100, zoom: 0.3}));
    expect(flow().nodes).toBe(nodes);
    act(() => flow().onMove?.(null, {x: -100, y: 100, zoom: 0.6}));
    expect(mounted.container.querySelector('.canvas-surface.is-compact')).toBeNull();
    expect(flow().nodes).toBe(nodes);
  });
});
