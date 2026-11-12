from __future__ import annotations

import json

from ccbd.startup_fence import KeeperStartupCheckpoint
from runtime_observability.startup_readiness import StartupReadinessRecorder


def _payload(**overrides):
    value = {
        'schema_version': 1,
        'trace_id': 'trace_' + 'a' * 32,
        'origin_monotonic_ns': 1_000_000,
        'attach_mode': 'no_attach',
        'expected_daemon_generation': 7,
        'keeper_startup_id': 'keeper-7',
        'T1_lifecycle_intent': {
            'status': 'not_required_already_mounted',
            'elapsed_ms': None,
            'source': 'cli_existing_mounted_generation',
        },
        'T2_control_plane_ready': {
            'status': 'reached',
            'elapsed_ms': 2.0,
            'source': 'cli_compatible_daemon_handle',
        },
    }
    value.update(overrides)
    return value


def test_readiness_recorder_emits_relative_complete_no_attach_timeline() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(_payload(), now_ns=4_000_000)
    assert recorder is not None
    recorder.mark('rpc_accepted', source='daemon_start_handler', now_ns=5_000_000)
    recorder.mark('T3_namespace_attachable', source='daemon_namespace', now_ns=6_000_000)
    recorder.set_agent_scopes(('bench_a', 'bench_b'), ('bench_a', 'bench_b'))
    recorder.mark(
        'T4_requested_agents_ready',
        source='daemon_start_flow',
        agents=('bench_a', 'bench_b'),
        now_ns=7_000_000,
    )
    recorder.mark(
        'T6_fully_warm',
        source='daemon_start_flow',
        agents=('bench_a', 'bench_b'),
        now_ns=7_000_000,
    )

    record = recorder.to_record(startup_run_id='start_' + 'b' * 32, daemon_generation=7)
    encoded = json.dumps(record, sort_keys=True)

    assert record['timeline_complete'] is True
    assert record['rpc_accepted_ms'] == 4.0
    assert record['points']['T0_cli_entry']['elapsed_ms'] == 0.0
    assert record['points']['T5_foreground_attached']['status'] == 'not_applicable_no_attach'
    assert record['effective_requested_agents'] == ['bench_a', 'bench_b']
    assert 'origin_monotonic_ns' not in encoded
    assert '1000000' not in encoded


def test_readiness_recorder_upgrades_matching_keeper_checkpoint_to_exact_t1() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(
        _payload(
            T1_lifecycle_intent={
                'status': 'observed_upper_bound',
                'elapsed_ms': 2.0,
                'source': 'cli_compatible_daemon_observation',
            }
        ),
        now_ns=4_000_000,
        trusted_keeper_checkpoint=KeeperStartupCheckpoint(
            startup_id='keeper-7',
            generation=7,
            accepted_perf_counter_ns=1_500_000,
        ),
    )

    assert recorder is not None
    record = recorder.to_record(
        startup_run_id='start_' + '9' * 32,
        daemon_generation=7,
    )
    assert record['points']['T1_lifecycle_intent'] == {
        'status': 'reached',
        'elapsed_ms': 0.5,
        'source': 'keeper_lifecycle_starting_committed',
        'agents': [],
    }
    assert '1500000' not in json.dumps(record, sort_keys=True)


def test_readiness_recorder_checkpoint_mismatch_keeps_honest_upper_bound() -> None:
    cold_payload = _payload(
        T1_lifecycle_intent={
            'status': 'observed_upper_bound',
            'elapsed_ms': 2.0,
            'source': 'cli_compatible_daemon_observation',
        }
    )
    for checkpoint in (
        KeeperStartupCheckpoint('other-startup', 7, 1_500_000),
        KeeperStartupCheckpoint('keeper-7', 8, 1_500_000),
        KeeperStartupCheckpoint('keeper-7', 7, 999_999),
        KeeperStartupCheckpoint('keeper-7', 7, 3_100_000),
    ):
        recorder = StartupReadinessRecorder.from_rpc_payload(
            cold_payload,
            now_ns=4_000_000,
            trusted_keeper_checkpoint=checkpoint,
        )
        assert recorder is not None
        record = recorder.to_record(startup_run_id=None, daemon_generation=7)
        assert record['points']['T1_lifecycle_intent']['status'] == 'observed_upper_bound'


def test_readiness_recorder_never_upgrades_warm_not_required_t1() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(
        _payload(),
        now_ns=4_000_000,
        trusted_keeper_checkpoint=KeeperStartupCheckpoint(
            startup_id='keeper-7',
            generation=7,
            accepted_perf_counter_ns=1_500_000,
        ),
    )

    assert recorder is not None
    record = recorder.to_record(startup_run_id=None, daemon_generation=7)
    assert record['points']['T1_lifecycle_intent']['status'] == 'not_required_already_mounted'


def test_readiness_recorder_rejects_invalid_envelopes_without_raising() -> None:
    assert StartupReadinessRecorder.from_rpc_payload(None, now_ns=4_000_000) is None
    assert StartupReadinessRecorder.from_rpc_payload(
        _payload(trace_id='trace_bad'), now_ns=4_000_000
    ) is None
    assert StartupReadinessRecorder.from_rpc_payload(
        _payload(origin_monotonic_ns=5_000_000), now_ns=4_000_000
    ) is None
    assert StartupReadinessRecorder.from_rpc_payload(
        _payload(T2_control_plane_ready={'status': 'reached', 'elapsed_ms': float('nan')}),
        now_ns=4_000_000,
    ) is None
    assert StartupReadinessRecorder.from_rpc_payload(
        _payload(expected_daemon_generation='7.0'), now_ns=4_000_000
    ) is None
    for invalid_generation in (None, 0, '7', -1, True):
        assert StartupReadinessRecorder.from_rpc_payload(
            _payload(expected_daemon_generation=invalid_generation), now_ns=4_000_000
        ) is None
    assert StartupReadinessRecorder.from_rpc_payload(
        _payload(), now_ns=3_600_001_000_001
    ) is None


def test_readiness_recorder_keeps_first_observation_for_each_point() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(_payload(), now_ns=4_000_000)
    assert recorder is not None

    recorder.mark('rpc_accepted', source='first', now_ns=5_000_000)
    recorder.mark('rpc_accepted', source='later', now_ns=9_000_000)
    recorder.mark('T3_namespace_attachable', source='first', now_ns=6_000_000)
    recorder.mark(
        'T3_namespace_attachable',
        status='failed_before_ready',
        source='later',
        now_ns=9_000_000,
    )

    record = recorder.to_record(startup_run_id='start_' + 'd' * 32, daemon_generation=7)
    assert record['rpc_accepted_ms'] == 4.0
    assert record['points']['T3_namespace_attachable'] == {
        'status': 'reached',
        'elapsed_ms': 5.0,
        'source': 'first',
        'agents': [],
    }


def test_readiness_recorder_ignores_pre_origin_observation_without_occupying_point() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(_payload(), now_ns=4_000_000)
    assert recorder is not None

    recorder.mark('T3_namespace_attachable', source='invalid', now_ns=999_999)
    recorder.mark('T3_namespace_attachable', source='valid', now_ns=6_000_000)

    record = recorder.to_record(startup_run_id='start_' + 'e' * 32, daemon_generation=7)
    assert record['points']['T3_namespace_attachable']['source'] == 'valid'
    assert record['points']['T3_namespace_attachable']['elapsed_ms'] == 5.0


def test_readiness_recorder_does_not_declare_out_of_order_timeline_complete() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(_payload(), now_ns=4_000_000)
    assert recorder is not None
    recorder.mark('rpc_accepted', source='daemon_start_handler', now_ns=5_000_000)
    recorder.mark('T3_namespace_attachable', source='daemon_namespace', now_ns=8_000_000)
    recorder.set_agent_scopes(('bench_a',), ('bench_a',))
    recorder.mark(
        'T4_requested_agents_ready',
        source='daemon_start_flow',
        agents=('bench_a',),
        now_ns=7_000_000,
    )
    recorder.mark(
        'T6_fully_warm',
        source='daemon_start_flow',
        agents=('bench_a',),
        now_ns=6_000_000,
    )

    record = recorder.to_record(startup_run_id='start_' + 'f' * 32, daemon_generation=7)
    assert record['timeline_complete'] is False


def test_readiness_generation_mismatch_is_explicit_and_incomplete() -> None:
    recorder = StartupReadinessRecorder.from_rpc_payload(_payload(), now_ns=4_000_000)
    assert recorder is not None
    record = recorder.to_record(startup_run_id='start_' + 'c' * 32, daemon_generation=8)

    assert record['generation_correlation'] == 'mismatch'
    assert record['timeline_complete'] is False
    assert record['points']['T3_namespace_attachable']['status'] == 'not_observed'
