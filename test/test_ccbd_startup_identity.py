from __future__ import annotations

from ccbd.models import CcbdStartupReport
from ccbd.startup_identity import new_startup_run_id, resolve_startup_run_id


def _report() -> CcbdStartupReport:
    return CcbdStartupReport(
        project_id='project-1',
        generated_at='2026-07-16T00:00:00Z',
        trigger='start_command',
        status='ok',
        requested_agents=(),
        desired_agents=(),
        restore_requested=False,
        auto_permission=False,
        startup_run_id='start_' + 'a' * 32,
    )


def test_startup_run_ids_are_unique_and_round_trip() -> None:
    identities = {new_startup_run_id() for _ in range(64)}

    assert len(identities) == 64
    assert all(resolve_startup_run_id(value, generate_if_missing=False) == value for value in identities)


def test_startup_report_reader_accepts_legacy_record_without_run_id() -> None:
    record = _report().to_record()
    record.pop('startup_run_id')

    restored = CcbdStartupReport.from_record(record)

    assert restored.startup_run_id is None


def test_startup_report_round_trips_optional_readiness_timeline() -> None:
    report = CcbdStartupReport(
        **{
            **_report().__dict__,
            'readiness_timeline': {
                'schema_version': 1,
                'trace_id': 'trace_' + 'b' * 32,
                'points': {'T0_cli_entry': {'status': 'reached', 'elapsed_ms': 0.0}},
            },
        }
    )

    restored = CcbdStartupReport.from_record(report.to_record())

    assert restored.readiness_timeline == report.readiness_timeline
    assert restored.summary_fields()['startup_last_readiness_timeline'] == report.readiness_timeline
