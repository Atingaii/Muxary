import 'package:ccb_mobile/features/project_home/project_home_terminal_navigation.dart';
import 'package:ccb_mobile/fixtures/project_view_fixture.dart';
import 'package:ccb_mobile/models/ccb_project_view.dart';
import 'package:test/test.dart';

void main() {
  test('fake open spec uses original project id and agent', () {
    final view = _viewWithProjectId('proj-original');

    final outcome = projectHomeFakeTerminalNavigation(
      view: view,
      agentName: 'lead',
    );

    expect(outcome.kind, ProjectHomeTerminalNavigationKind.open);
    expect(outcome.spec?.projectId, 'proj-original');
    expect(outcome.spec?.agentName, 'lead');
    expect(outcome.spec?.gatewayTerminal, isFalse);
    expect(outcome.snackMessage, isNull);
  });

  test('paired null view does not navigate', () {
    final outcome = projectHomeGatewayTerminalNavigation(
      view: null,
      agentName: 'lead',
      hasTerminalTransport: true,
    );

    expect(outcome.kind, ProjectHomeTerminalNavigationKind.none);
    expect(outcome.spec, isNull);
    expect(outcome.snackMessage, isNull);
  });

  test('paired view without transport returns exact snack', () {
    final outcome = projectHomeGatewayTerminalNavigation(
      view: _viewWithProjectId('proj-focused'),
      agentName: 'lead',
      hasTerminalTransport: false,
    );

    expect(outcome.kind, ProjectHomeTerminalNavigationKind.noTransport);
    expect(outcome.spec, isNull);
    expect(outcome.snackMessage, 'Gateway terminal transport is not ready');
  });

  test('paired view with transport retains agent pane identity', () {
    final outcome = projectHomeGatewayTerminalNavigation(
      view: _viewWithProjectId('proj-focused'),
      agentName: 'mobile',
      hasTerminalTransport: true,
    );

    expect(outcome.kind, ProjectHomeTerminalNavigationKind.open);
    expect(outcome.spec?.projectId, 'proj-focused');
    expect(outcome.spec?.agentName, 'mobile');
    expect(outcome.spec?.gatewayTerminal, isTrue);
    expect(outcome.spec?.namespaceEpoch, 4);
    expect(outcome.spec?.windowName, 'main');
    expect(outcome.spec?.paneId, '%2');
    expect(outcome.snackMessage, isNull);
  });

  test('paired decision uses bool instead of owning transport object', () {
    final outcome = projectHomeGatewayTerminalNavigation(
      view: _viewWithProjectId('proj-focused'),
      agentName: 'lead',
      hasTerminalTransport: true,
    );

    expect(outcome.spec?.gatewayTerminal, isTrue);
  });
}

CcbProjectView _viewWithProjectId(String projectId) {
  return CcbProjectView.fromProjectViewPayload({
    ...demoProjectViewFixture,
    'view': {
      ...(demoProjectViewFixture['view']! as Map<String, Object?>),
      'project': {
        ...((demoProjectViewFixture['view']!
                as Map<String, Object?>)['project']!
            as Map<String, Object?>),
        'id': projectId,
      },
    },
  });
}
