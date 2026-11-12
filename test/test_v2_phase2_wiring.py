from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

import cli.phase2 as phase2_module
from cli.phase2_runtime.handlers_ops import handle_frontdesk
from cli.phase2_services import build_phase2_dispatch_services


def test_phase2_dispatch_builders_expose_auto_runner_and_frontdesk_command() -> None:
    default_services = build_phase2_dispatch_services()
    phase2_services = phase2_module._dispatch_services()

    assert default_services.loop_runner_auto is phase2_module.loop_runner_auto
    assert default_services.frontdesk_intake_command is phase2_module.frontdesk_intake_command
    assert phase2_services.loop_runner_auto is phase2_module.loop_runner_auto
    assert phase2_services.frontdesk_intake_command is phase2_module.frontdesk_intake_command


def test_phase2_loop_runner_auto_dispatches_to_wired_service(monkeypatch, tmp_path) -> None:
    context = SimpleNamespace(project=SimpleNamespace(project_root=tmp_path, project_id='proj-wiring'))
    seen: list[tuple[object, object, object]] = []

    def fake_auto(received_context, command, services):
        seen.append((received_context, command, services))
        return {'loop_runner_status': 'idle', 'action': 'none'}

    monkeypatch.setattr(phase2_module, '_build_context', lambda command, cwd, out: context)
    monkeypatch.setattr(phase2_module, 'loop_runner_auto', fake_auto)

    stdout = StringIO()
    stderr = StringIO()
    code = phase2_module.maybe_handle_phase2(
        ['loop', 'runner', '--auto', '--max-steps', '1', '--json'],
        cwd=tmp_path,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert len(seen) == 1
    assert '"loop_runner_status": "idle"' in stdout.getvalue()
    assert stderr.getvalue() == ''


def test_frontdesk_handler_uses_command_service_without_legacy_dependency() -> None:
    seen: list[tuple[object, object, object]] = []

    def frontdesk_intake_command(context, command, services):
        seen.append((context, command, services))
        return {'frontdesk_intake_status': 'ok'}

    services = SimpleNamespace(
        frontdesk_intake_command=frontdesk_intake_command,
        render_mapping=lambda payload: ('frontdesk_status: ok',),
        write_lines=lambda out, lines: out.write('\n'.join(lines) + '\n'),
    )
    out = StringIO()
    context = object()
    command = SimpleNamespace(json_output=False)

    assert handle_frontdesk(context, command, out, services) == 0
    assert len(seen) == 1
    assert out.getvalue() == 'frontdesk_status: ok\n'
