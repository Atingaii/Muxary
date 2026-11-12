import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_home_shell_state.dart';
import 'package:test/test.dart';

void main() {
  group('project home shell state', () {
    test('collapse mobile agents transitions from expanded only', () {
      final expanded = collapseProjectHomeMobileAgents(false);

      expect(expanded.collapsed, isTrue);
      expect(expanded.shouldUpdate, isTrue);

      final alreadyCollapsed = collapseProjectHomeMobileAgents(true);

      expect(alreadyCollapsed.collapsed, isTrue);
      expect(alreadyCollapsed.shouldUpdate, isFalse);
    });

    test('expand mobile agents transitions from collapsed only', () {
      final collapsed = expandProjectHomeMobileAgents(true);

      expect(collapsed.collapsed, isFalse);
      expect(collapsed.shouldUpdate, isTrue);

      final alreadyExpanded = expandProjectHomeMobileAgents(false);

      expect(alreadyExpanded.collapsed, isFalse);
      expect(alreadyExpanded.shouldUpdate, isFalse);
    });

    test('open project uses current view project id', () {
      final outcome = openProjectHomeProject(_view(projectId: 'proj-current'));

      expect(outcome.openedProjectId, 'proj-current');
    });

    test('close project clears opened project', () {
      final outcome = closeProjectHomeProject();

      expect(outcome.openedProjectId, isNull);
    });

    test('select agent passes through requested name without validation', () {
      final outcome = selectProjectHomeAgent('stale-agent');

      expect(outcome.selectedAgentName, 'stale-agent');
      expect(outcome.shouldUpdate, isTrue);
    });

    test('local window selects first agent for requested window', () {
      final outcome = selectProjectHomeLocalWindow(_view(), 'review');

      expect(outcome.selectedAgentName, 'reviewer');
      expect(outcome.shouldUpdate, isTrue);
    });

    test('local window unknown is a no-op', () {
      final outcome = selectProjectHomeLocalWindow(_view(), 'missing');

      expect(outcome.selectedAgentName, isNull);
      expect(outcome.shouldUpdate, isFalse);
    });

    test('local window empty name preserves main fallback behavior', () {
      final outcome = selectProjectHomeLocalWindow(_view(), '');

      expect(outcome.selectedAgentName, 'lead');
      expect(outcome.shouldUpdate, isTrue);
    });

    test('local window empty view remains a no-op', () {
      final outcome = selectProjectHomeLocalWindow(
        _view(agents: const [], windows: const []),
        '',
      );

      expect(outcome.selectedAgentName, isNull);
      expect(outcome.shouldUpdate, isFalse);
    });
  });
}

CcbProjectView _view({
  String projectId = 'proj-demo',
  List<CcbAgent> agents = _agents,
  List<CcbWindow> windows = _windows,
}) {
  return CcbProjectView(
    project: CcbProject(
      id: projectId,
      displayName: 'demo',
      root: '/srv/ccb/demo',
    ),
    namespaceEpoch: 4,
    tmuxSocketPath: '/tmp/ccb-demo/tmux.sock',
    tmuxSessionName: 'ccb-demo',
    activeWindow: 'main',
    activePaneId: '%2',
    windows: windows,
    agents: agents,
    contentItems: const [],
    notifications: const [],
    terminalHistories: const {},
  );
}

const _windows = [
  CcbWindow(
    name: 'main',
    label: 'main',
    kind: 'agents',
    order: 0,
    active: true,
    agents: ['lead', 'mobile'],
  ),
  CcbWindow(
    name: 'review',
    label: 'review',
    kind: 'agents',
    order: 1,
    active: false,
    agents: ['reviewer'],
  ),
];

const _agents = [
  CcbAgent(
    name: 'lead',
    provider: 'codex',
    window: 'main',
    order: 0,
    active: false,
    queueDepth: 0,
  ),
  CcbAgent(
    name: 'mobile',
    provider: 'codex',
    window: 'main',
    order: 1,
    active: true,
    queueDepth: 1,
  ),
  CcbAgent(
    name: 'reviewer',
    provider: 'codex',
    window: 'review',
    order: 0,
    active: false,
    queueDepth: 0,
  ),
];
