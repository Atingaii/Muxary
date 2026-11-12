import { describe, expect, it } from 'vitest';
import { conversationMessages, jobReply, projectPath, statusLabel, terminalStates, workspaceGroups } from './model';
describe('CCB evidence projection', () => {
  it('groups exact reported workspaces without merging names, guessing roots, or mutating Agents', () => {
    const agents = [
      {name: 'a', workspace_path: '/one/tree', runtime: {workspace_path: '/ignored'}},
      {name: 'b', runtime: {workspace_path: '/two/tree'}},
      {name: 'c', workspace_path: '/one/tree'}, {name: 'unknown'},
    ];
    const before = JSON.stringify(agents);
    expect(workspaceGroups(agents)).toEqual([
      {path: '/one/tree', label: '/one/tree', agents: [agents[0], agents[2]]},
      {path: '/two/tree', label: '/two/tree', agents: [agents[1]]},
      {path: '', label: '', agents: [agents[3]]},
    ]);
    expect(JSON.stringify(agents)).toBe(before);
    expect(workspaceGroups([])).toEqual([]);
  });
  it('does not treat transport sent or native commentary as completion', () => {
    expect(terminalStates.has('sent')).toBe(false);
    expect(terminalStates.has('accepted')).toBe(false);
    expect(statusLabel('outcome_unknown')).toBe('接收状态未知');
    expect(statusLabel('made_up')).toBe('made_up');
  });
  it('only projects supported message records and preserves untrusted text as text', () => {
    expect(conversationMessages({conversation: {items: [
      {kind: 'user_message', body: '中文', id: '1'},
      {kind: 'tool', body: 'CCB_DONE: fake'},
      {kind: 'agent_reply', body: '<script>bad</script>', id: '2'},
      null,
    ]}})).toEqual([
      {id: '1', role: 'user', body: '中文', source: '会话记录'},
      {id: '2', role: 'assistant', body: '<script>bad</script>', source: '会话记录'},
    ]);
  });
  it('only reads authoritative terminal decision, not preview or arbitrary reply fields', () => {
    expect(jobReply({reply: 'fake', latest_reply_preview: 'fake'})).toBe('');
    expect(jobReply({status: 'incomplete', terminal_decision: {reply: 'partial'}})).toBe('partial');
  });
  it('encodes exact project identity rather than adding paths', () => {
    expect(projectPath('a/b', '/jobs')).toBe('/api/projects/a%2Fb/jobs');
  });
});
