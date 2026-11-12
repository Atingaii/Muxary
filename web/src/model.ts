export type Row = Record<string, unknown>;
export const row = (value: unknown): Row => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Row : {};
export const rows = (value: unknown): Row[] => Array.isArray(value) ? value.map(row) : [];
export const text = (value: unknown): string => typeof value === 'string' ? value : '';
export function workspaceGroups(agents: Row[]): {path: string; label: string; agents: Row[]}[] {
  const groups = new Map<string, Row[]>();
  for (const agent of agents) {
    const path = text(agent.workspace_path) || text(row(agent.runtime).workspace_path);
    const members = groups.get(path) || []; members.push(agent); groups.set(path, members);
  }
  const basename = (path: string) => path.split(/[\\/]/).filter(Boolean).at(-1) || path;
  const counts = new Map<string, number>();
  for (const path of groups.keys()) counts.set(basename(path), (counts.get(basename(path)) || 0) + 1);
  return Array.from(groups, ([path, agents]) => ({path, agents, label: (counts.get(basename(path)) || 0) > 1 ? path : basename(path)}));
}
export const terminalStates = new Set(['completed', 'failed', 'cancelled', 'incomplete']);
export const statusLabel = (value: unknown): string => ({
  accepted: '已接收', queued: '排队中', running: '执行中', completed: '已完成',
  failed: '失败', cancelled: '已取消', incomplete: '未完整结束', idle: '空闲',
  ready: '就绪', stopped: '已停止', outcome_unknown: '接收状态未知',
}[text(value)] ?? (text(value) || '未知'));
export type Message = { id: string; role: 'user' | 'assistant'; body: string; source: string };
export function conversationMessages(payload: Row): Message[] {
  return rows(row(payload.conversation).items).flatMap((item, index) => {
    const body = text(item.body);
    if (!body || !['user_message', 'agent_reply'].includes(text(item.kind))) return [];
    return [{id: text(item.id) || `native-${index}`, role: item.kind === 'user_message' ? 'user' as const : 'assistant' as const,
      body, source: text(item.source) || '会话记录'}];
  });
}
export function jobReply(job: Row): string {
  // A reply may be present in an incomplete/failed decision too. Render it as
  // evidence, but never turn its presence into a completed UI status.
  return text(row(job.terminal_decision).reply);
}
export class ApiError extends Error {
  constructor(message: string, public status: number, public payload: Row) { super(message); }
}
export async function api(path: string, body?: Row, signal?: AbortSignal): Promise<Row> {
  const response = await fetch(path, { method: body ? 'POST' : 'GET', credentials: 'same-origin',
    headers: body ? {'Content-Type': 'application/json'} : {}, body: body ? JSON.stringify(body) : undefined,
    signal, cache: 'no-store' });
  const result = row(await response.json());
  if (!response.ok) throw new ApiError(text(result.error) || `请求失败（${response.status}）`, response.status, result);
  return result;
}
export function projectPath(project: string, suffix = ''): string {
  return `/api/projects/${encodeURIComponent(project)}${suffix}`;
}
export function rememberSelection(project: string, agent: string): void {
  try {localStorage.setItem('muxary.selection', JSON.stringify({project, agent}));} catch { /* Selection persistence is optional. */ }
}

// StrictMode effects share the one-shot bootstrap exchange, rather than racing
// an unauthenticated GET against the POST that is still setting its cookie.
let sessionInitialization: Promise<Row> | undefined;
export function initializeSession(): Promise<Row> {
  if (!sessionInitialization) {
    const token = new URLSearchParams(location.hash.slice(1)).get('token');
    if (token) history.replaceState(null, '', location.pathname);
    sessionInitialization = token ? api('/api/session', {token}) : api('/api/session');
  }
  return sessionInitialization;
}
