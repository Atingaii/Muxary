import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_view_selection.dart';
import 'package:test/test.dart';

void main() {
  group('selectedProjectHomeAgent', () {
    test('valid selected name wins', () {
      final selected = selectedProjectHomeAgent(_view(), 'lead');

      expect(selected?.name, 'lead');
    });

    test('stale selected name falls back to active', () {
      final selected = selectedProjectHomeAgent(_view(), 'ghost');

      expect(selected?.name, 'mobile');
    });

    test('no active falls back to first agent', () {
      final selected = selectedProjectHomeAgent(
        _view(
          agents: const [
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
              active: false,
              queueDepth: 0,
            ),
          ],
        ),
        null,
      );

      expect(selected?.name, 'lead');
    });

    test('empty agent list returns null', () {
      final selected = selectedProjectHomeAgent(
        _view(agents: const [], windows: const []),
        null,
      );

      expect(selected, isNull);
    });
  });

  group('projectHomeLocalWindowSelectionAgentName', () {
    test('returns first agent for window', () {
      final agentName = projectHomeLocalWindowSelectionAgentName(
        _view(),
        'review',
      );

      expect(agentName, 'reviewer');
    });

    test('unknown window returns null', () {
      final agentName = projectHomeLocalWindowSelectionAgentName(
        _view(),
        'missing',
      );

      expect(agentName, isNull);
    });

    test('empty window selects main window first agent', () {
      final agentName = projectHomeLocalWindowSelectionAgentName(_view(), '');

      expect(agentName, 'lead');
    });

    test('empty view returns null for empty window', () {
      final agentName = projectHomeLocalWindowSelectionAgentName(
        _view(agents: const [], windows: const []),
        '',
      );

      expect(agentName, isNull);
    });
  });
}

CcbProjectView _view({
  List<CcbAgent> agents = _agents,
  List<CcbWindow> windows = _windows,
}) {
  return CcbProjectView(
    project: const CcbProject(
      id: 'proj-demo',
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
