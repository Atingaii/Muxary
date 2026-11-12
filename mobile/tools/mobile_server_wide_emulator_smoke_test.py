#!/usr/bin/env python3
"""Self-tests for server-wide Android Emulator smoke helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name('mobile_server_wide_emulator_smoke.py')
SPEC = importlib.util.spec_from_file_location(
    'mobile_server_wide_emulator_smoke',
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f'could not load {MODULE_PATH}')
SMOKE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SMOKE
SPEC.loader.exec_module(SMOKE)


class MobileServerWideEmulatorSmokeTest(unittest.TestCase):
    def test_idle_request_totals_counts_conversation_and_terminal_routes(self) -> None:
        totals = SMOKE.idle_request_totals(
            {
                'total_requests': 4,
                'counts_by_route': {
                    '/v1/projects/{project}/agents/{agent}/conversation': 2,
                    '/v1/projects/{project}/agents/{agent}/terminal-history': 1,
                    '/v1/projects': 1,
                },
            },
            idle_seconds=120,
        )

        self.assertEqual(totals['total_requests'], 4)
        self.assertEqual(totals['conversation_requests'], 2)
        self.assertEqual(totals['terminal_history_requests'], 1)
        self.assertEqual(totals['conversation_terminal_requests'], 3)
        self.assertEqual(totals['conversation_terminal_requests_per_minute'], 1.5)

    def test_summarize_idle_device_metrics_extracts_release_gate_fields(self) -> None:
        summary = SMOKE.summarize_idle_device_metrics(
            samples=[
                {
                    'label': 'start',
                    'elapsed_s': 0.0,
                    'total_pss_kb': 1000,
                    'total_rss_kb': 4000,
                },
                {
                    'label': 'end',
                    'elapsed_s': 180.0,
                    'total_pss_kb': 1100,
                    'total_rss_kb': 4200,
                },
            ],
            power_text='''
              mWakefulness=Awake
              mWakeLockSummary=0x0
              mHoldingWakeLockSuspendBlocker=false
            Wake Locks: size=0
            ''',
            batterystats_text='Uid u0a123: cpu=1 wake=0 Network=0',
            gfxinfo_text='''
            Total frames rendered: 120
            Janky frames: 1 (0.8%)
            ''',
            logcat_text='I/ccb_mobile: frame stable\n',
            errors=[],
        )

        self.assertEqual(summary['sample_count'], 2)
        self.assertEqual(summary['sample_labels'], ['start', 'end'])
        self.assertEqual(summary['memory']['pss_growth_ratio'], 0.1)
        self.assertEqual(summary['power']['wake_locks'], 'Wake Locks: size=0')
        self.assertEqual(summary['gfxinfo']['total_frames_rendered'], 'Total frames rendered: 120')
        self.assertFalse(summary['logcat']['fatal_anr_oom'])
        self.assertEqual(summary['errors'], [])
        self.assertEqual(summary['warnings'], [])

    def test_summarize_idle_device_metrics_warns_on_global_wake_locks(self) -> None:
        summary = SMOKE.summarize_idle_device_metrics(
            samples=[{'label': 'start', 'total_pss_kb': 100}],
            power_text='Wake Locks: size=1\nmWakeLockSummary=0x1',
            batterystats_text='',
            gfxinfo_text='',
            logcat_text='',
            errors=[],
        )

        self.assertEqual(summary['errors'], [])
        self.assertGreaterEqual(len(summary['warnings']), 2)
        SMOKE.validate_idle_device_metrics(summary)

    def test_validate_idle_device_metrics_rejects_fatal_logcat(self) -> None:
        with self.assertRaisesRegex(RuntimeError, 'FATAL'):
            SMOKE.validate_idle_device_metrics(
                {
                    'memory': {'pss_growth_ratio': 0.0},
                    'power': {'wake_locks': 'Wake Locks: size=0'},
                    'logcat': {'fatal_anr_oom': True},
                }
            )

    def test_android_main_activity_uses_package_relative_main_activity(self) -> None:
        self.assertEqual(
            SMOKE.android_main_activity('io.ccb.mobile.ccb_mobile'),
            'io.ccb.mobile.ccb_mobile/.MainActivity',
        )

    def test_parse_args_accepts_background_reverse_recovery_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--background-reverse-recovery-smoke', '--background-resume-seconds', '7']
        )

        self.assertTrue(args.background_reverse_recovery_smoke)
        self.assertEqual(args.background_resume_seconds, 7)

    def test_parse_args_accepts_background_file_download_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--background-file-download-smoke', '--background-file-download-bytes', '4096']
        )

        self.assertTrue(args.background_file_download_smoke)
        self.assertEqual(args.background_file_download_bytes, 4096)

    def test_parse_args_accepts_upload_stress_bytes(self) -> None:
        args = SMOKE.parse_args(['--upload-stress-bytes', '4096'])

        self.assertEqual(args.upload_stress_bytes, 4096)

    def test_parse_args_accepts_flutter_profile_build_mode(self) -> None:
        args = SMOKE.parse_args(['--flutter-build-mode', 'profile'])

        self.assertEqual(args.flutter_build_mode, 'profile')

    def test_parse_args_accepts_release_project_list_smoke(self) -> None:
        args = SMOKE.parse_args(['--release-project-list-smoke'])

        self.assertTrue(args.release_project_list_smoke)

    def test_parse_args_accepts_release_idle_request_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--release-idle-request-smoke', '--idle-request-seconds', '30']
        )

        self.assertTrue(args.release_idle_request_smoke)
        self.assertEqual(args.idle_request_seconds, 30)

    def test_parse_args_accepts_release_long_history_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--release-long-history-smoke', '--backfill-turns', '200']
        )

        self.assertTrue(args.release_long_history_smoke)
        self.assertEqual(args.backfill_turns, 200)

    def test_parse_args_accepts_release_file_download_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--release-file-download-smoke', '--background-file-download-bytes', '8192']
        )

        self.assertTrue(args.release_file_download_smoke)
        self.assertEqual(args.background_file_download_bytes, 8192)

    def test_parse_args_accepts_release_upload_smoke(self) -> None:
        args = SMOKE.parse_args(
            ['--release-upload-smoke', '--upload-stress-bytes', '8192']
        )

        self.assertTrue(args.release_upload_smoke)
        self.assertEqual(args.upload_stress_bytes, 8192)

    def test_gateway_reverse_host_ports_include_gateway_when_proxy_is_enabled(self) -> None:
        self.assertEqual(
            SMOKE.gateway_reverse_host_ports(
                gateway_port=19228,
                idle_proxy_enabled=False,
                request_proxy_listen=None,
            ),
            [19228],
        )
        self.assertEqual(
            SMOKE.gateway_reverse_host_ports(
                gateway_port=19228,
                idle_proxy_enabled=True,
                request_proxy_listen='127.0.0.1:19229',
            ),
            [19229, 19228],
        )
        self.assertEqual(
            SMOKE.gateway_reverse_host_ports(
                gateway_port=19228,
                idle_proxy_enabled=True,
                request_proxy_listen=None,
            ),
            [19229, 19228],
        )

    def test_wait_for_server_projects_polls_during_health_warming(self) -> None:
        original_get = SMOKE.http_get_json
        original_sleep = SMOKE.time.sleep
        calls: list[str] = []

        def fake_get(url: str) -> dict[str, object]:
            calls.append(url)
            if len(calls) == 1:
                return {
                    'health_warming': True,
                    'projects': [],
                    'registry_project_count': 2,
                }
            return {'projects': [{'id': 'one'}, {'id': 'two'}]}

        try:
            SMOKE.http_get_json = fake_get
            SMOKE.time.sleep = lambda _seconds: None
            payload = SMOKE.wait_for_server_projects(
                'http://127.0.0.1:18891/v1/projects',
                minimum=2,
                timeout_s=1,
            )
        finally:
            SMOKE.http_get_json = original_get
            SMOKE.time.sleep = original_sleep

        self.assertEqual(payload['projects'], [{'id': 'one'}, {'id': 'two'}])
        self.assertEqual(calls, ['http://127.0.0.1:18891/v1/projects'] * 2)

    def test_parse_args_accepts_release_reverse_recovery_smoke(self) -> None:
        args = SMOKE.parse_args(['--release-reverse-recovery-smoke'])

        self.assertTrue(args.release_reverse_recovery_smoke)

    def test_extract_native_timing_reads_structured_stdout_payload(self) -> None:
        timing = SMOKE.extract_native_timing(
            '\n'.join(
                [
                    'flutter noise',
                    (
                        'CCB_MOBILE_NATIVE_TIMING_JSON '
                        '{"send_to_local_bubble_ms":42,'
                        '"send_to_working_ms":55,'
                        '"send_to_expected_reply_ms":900}'
                    ),
                ]
            )
        )

        self.assertEqual(timing['send_to_local_bubble_ms'], 42)
        self.assertEqual(timing['send_to_working_ms'], 55)
        self.assertEqual(timing['send_to_expected_reply_ms'], 900)

    def test_extract_native_timings_reads_all_structured_stdout_payloads(self) -> None:
        timings = SMOKE.extract_native_timings(
            '\n'.join(
                [
                    'CCB_MOBILE_NATIVE_TIMING_JSON {"send_to_local_bubble_ms":10}',
                    'flutter noise',
                    'CCB_MOBILE_NATIVE_TIMING_JSON {"send_to_local_bubble_ms":20}',
                ]
            )
        )

        self.assertEqual(
            [timing['send_to_local_bubble_ms'] for timing in timings],
            [10, 20],
        )

    def test_extract_recovery_timing_reads_structured_stdout_payload(self) -> None:
        timing = SMOKE.extract_recovery_timing(
            '\n'.join(
                [
                    'flutter noise',
                    (
                        'CCB_RECOVERY_TIMING_JSON '
                        '{"project_list_refresh_to_error_ms":120,'
                        '"project_list_retry_to_recovered_ms":240,'
                        '"conversation_refresh_to_error_ms":360,'
                        '"conversation_retry_to_recovered_ms":480}'
                    ),
                ]
            )
        )

        assert timing is not None
        self.assertEqual(timing['project_list_refresh_to_error_ms'], 120)
        self.assertEqual(timing['project_list_retry_to_recovered_ms'], 240)
        self.assertEqual(timing['conversation_refresh_to_error_ms'], 360)
        self.assertEqual(timing['conversation_retry_to_recovered_ms'], 480)

    def test_summarize_native_timing_cases_reports_percentiles_and_missing(self) -> None:
        summary = SMOKE.summarize_native_timing_cases(
            [
                {
                    'send_to_local_bubble_ms': 80,
                    'send_to_working_ms': 120,
                    'send_to_first_feedback_ms': 120,
                    'send_to_expected_reply_ms': 900,
                    'first_feedback_kind': 'working',
                },
                {
                    'send_to_local_bubble_ms': 40,
                    'send_to_working_ms': None,
                    'send_to_first_feedback_ms': 500,
                    'send_to_expected_reply_ms': 1400,
                    'first_feedback_kind': 'expected_reply',
                },
                None,
            ]
        )

        self.assertEqual(summary['case_count'], 3)
        self.assertEqual(summary['timing_payload_count'], 2)
        self.assertEqual(summary['working_captured_count'], 1)
        self.assertEqual(
            summary['first_feedback_kinds'],
            {'working': 1, 'expected_reply': 1},
        )
        self.assertEqual(
            summary['fields']['send_to_local_bubble_ms'],
            {
                'count': 2,
                'missing': 1,
                'min_ms': 40.0,
                'p50_ms': 40.0,
                'p95_ms': 80.0,
                'max_ms': 80.0,
            },
        )
        self.assertEqual(
            summary['fields']['send_to_working_ms'],
            {
                'count': 1,
                'missing': 2,
                'min_ms': 120.0,
                'p50_ms': 120.0,
                'p95_ms': 120.0,
                'max_ms': 120.0,
            },
        )

    def test_parse_args_accepts_native_pane_repeat(self) -> None:
        args = SMOKE.parse_args(['--native-pane-smoke', '--native-pane-repeat', '3'])

        self.assertTrue(args.native_pane_smoke)
        self.assertEqual(args.native_pane_repeat, 3)

    def test_parse_args_accepts_native_command_smoke(self) -> None:
        args = SMOKE.parse_args(
            [
                '--native-command-smoke',
                '--native-command',
                '/status',
                '--native-command-marker',
                'Weekly limit:',
            ]
        )

        self.assertTrue(args.native_command_smoke)
        self.assertEqual(args.native_command, '/status')
        self.assertEqual(args.native_command_marker, 'Weekly limit:')
        self.assertFalse(args.native_command_device_metrics)

    def test_parse_args_accepts_native_command_device_metrics(self) -> None:
        args = SMOKE.parse_args(
            [
                '--native-command-smoke',
                '--native-command-device-metrics',
            ]
        )

        self.assertTrue(args.native_command_smoke)
        self.assertTrue(args.native_command_device_metrics)

    def test_parse_args_accepts_native_command_live_terminal_marker_gate(self) -> None:
        args = SMOKE.parse_args(
            [
                '--native-command-smoke',
                '--native-command-require-live-terminal-marker',
            ]
        )

        self.assertTrue(args.native_command_smoke)
        self.assertTrue(args.native_command_require_live_terminal_marker)

    def test_parse_args_accepts_native_command_high_volume_gates(self) -> None:
        args = SMOKE.parse_args(
            [
                '--native-command-smoke',
                '--native-command-line-prefix',
                'CCB_MOBILE_STREAM_LINE_',
                '--native-command-min-line-prefix-count',
                '1000',
                '--native-command-max-non-local-items',
                '3',
            ]
        )

        self.assertTrue(args.native_command_smoke)
        self.assertEqual(args.native_command_line_prefix, 'CCB_MOBILE_STREAM_LINE_')
        self.assertEqual(args.native_command_min_line_prefix_count, 1000)
        self.assertEqual(args.native_command_max_non_local_items, 3)

    def test_flutter_integration_args_debug_uses_flutter_test(self) -> None:
        args = SMOKE.flutter_integration_args(
            test_target='integration_test/example_test.dart',
            device_id='emulator-5554',
            dart_defines=['A=B'],
            build_mode='debug',
        )

        self.assertEqual(
            args,
            [
                'flutter',
                'test',
                'integration_test/example_test.dart',
                '-d',
                'emulator-5554',
                '-D',
                'A=B',
            ],
        )

    def test_flutter_integration_args_profile_uses_drive_and_test_seed(self) -> None:
        args = SMOKE.flutter_integration_args(
            test_target='integration_test/example_test.dart',
            device_id='emulator-5554',
            dart_defines=['A=B'],
            build_mode='profile',
        )

        self.assertEqual(args[:8], [
            'flutter',
            'drive',
            '--profile',
            '--driver',
            'test_driver/integration_test.dart',
            '--target',
            'integration_test/example_test.dart',
            '-d',
        ])
        self.assertIn('emulator-5554', args)
        self.assertIn('CCB_MOBILE_TEST_PROFILE_SEED=true', args)

    def test_seeded_release_apk_args_enable_test_profile_seed(self) -> None:
        args = SMOKE.seeded_apk_build_args(
            build_mode='release',
            debug_profile='encoded-profile',
        )

        self.assertEqual(args[:4], ['flutter', 'build', 'apk', '--release'])
        self.assertIn(
            'CCB_MOBILE_DEBUG_PAIRED_HOST_BASE64=encoded-profile',
            args,
        )
        self.assertIn('CCB_MOBILE_DEBUG_AUTO_ACTIVATE=true', args)
        self.assertIn('CCB_MOBILE_TEST_PROFILE_SEED=true', args)

    def test_seeded_debug_apk_args_do_not_enable_test_profile_seed(self) -> None:
        args = SMOKE.seeded_apk_build_args(
            build_mode='debug',
            debug_profile='encoded-profile',
        )

        self.assertEqual(args[:4], ['flutter', 'build', 'apk', '--debug'])
        self.assertNotIn('CCB_MOBILE_TEST_PROFILE_SEED=true', args)

    def test_parse_android_bounds_reads_uiautomator_bounds(self) -> None:
        self.assertEqual(
            SMOKE.parse_android_bounds('[12,34][56,78]'),
            (12, 34, 56, 78),
        )
        self.assertIsNone(SMOKE.parse_android_bounds('[12,34][12,78]'))

    def test_ui_texts_and_bounds_read_uiautomator_xml(self) -> None:
        ui_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy>
  <node text="test_ccb2_alpha" bounds="[10,20][210,90]" />
  <node text="mobile_probe" bounds="[15,100][220,160]" />
</hierarchy>'''

        self.assertEqual(
            SMOKE.ui_texts(ui_xml),
            ['test_ccb2_alpha', 'mobile_probe'],
        )
        self.assertEqual(
            SMOKE.ui_node_bounds_for_text(ui_xml, 'test_ccb2_alpha'),
            (10, 20, 210, 90),
        )
        self.assertIsNone(SMOKE.ui_node_bounds_for_text(ui_xml, 'missing'))

    def test_ui_texts_and_bounds_read_flutter_release_content_desc(self) -> None:
        ui_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy>
  <node text="" content-desc="test_ccb2_alpha&#10;/tmp/project&#10;healthy" bounds="[10,20][210,90]" />
</hierarchy>'''

        self.assertEqual(
            SMOKE.ui_texts(ui_xml),
            ['test_ccb2_alpha', '/tmp/project', 'healthy'],
        )
        self.assertEqual(
            SMOKE.ui_node_bounds_for_text(ui_xml, 'test_ccb2_alpha'),
            (10, 20, 210, 90),
        )
        self.assertEqual(
            SMOKE.ui_node_bounds_containing_text(ui_xml, 'test_ccb2'),
            (10, 20, 210, 90),
        )

    def test_ui_texts_contain_matches_release_content_fragments(self) -> None:
        self.assertTrue(
            SMOKE.ui_texts_contain(
                ['Native backfill answer backfill-run-199 extra text'],
                'Native backfill answer backfill-run-199',
            )
        )
        self.assertFalse(SMOKE.ui_texts_contain(['other text'], 'missing'))

    def test_gateway_file_download_record_matches_expected_size_and_hash(self) -> None:
        snapshot = {
            'records': [
                {
                    'route': '/v1/projects/{project}/agents/{agent}/conversation',
                    'status': 200,
                    'response_bytes': 10,
                    'response_sha256': 'nope',
                },
                {
                    'route': '/v1/projects/{project}/files/{id}',
                    'status': 200,
                    'response_bytes': 4096,
                    'response_sha256': 'abc123',
                    'elapsed_ms': 12.5,
                },
            ],
        }

        record = SMOKE.require_gateway_file_download_record(
            snapshot,
            expected_size_bytes=4096,
            expected_sha256='abc123',
        )

        self.assertEqual(record['elapsed_ms'], 12.5)
        with self.assertRaisesRegex(RuntimeError, 'expected bytes/hash'):
            SMOKE.require_gateway_file_download_record(
                snapshot,
                expected_size_bytes=4096,
                expected_sha256='missing',
            )

    def test_flutter_attachment_size_label_matches_ui_format(self) -> None:
        self.assertEqual(SMOKE.flutter_attachment_size_label(67), '67 B')
        self.assertEqual(SMOKE.flutter_attachment_size_label(4096), '4.0 KB')
        self.assertEqual(SMOKE.flutter_attachment_size_label(8 * 1024 * 1024), '8.0 MB')

    def test_parse_args_accepts_file_restart_smoke(self) -> None:
        args = SMOKE.parse_args(['--file-restart-smoke'])

        self.assertTrue(args.file_restart_smoke)

    def test_parse_args_accepts_live_artifact_smoke(self) -> None:
        args = SMOKE.parse_args(['--live-artifact-smoke'])

        self.assertTrue(args.live_artifact_smoke)

    def test_extract_live_artifact_done_reads_json_marker(self) -> None:
        marker = (
            'I/flutter: CCB_LIVE_ARTIFACT_SMOKE_DONE '
            '{"file_name":"result.txt","sha256":"abc"}'
        )

        self.assertEqual(
            SMOKE.extract_live_artifact_done(marker),
            {'file_name': 'result.txt', 'sha256': 'abc'},
        )

    def test_extract_upload_stress_result_reads_json_marker(self) -> None:
        marker = (
            'I/flutter: CCB_UPLOAD_STRESS_RESULT '
            '{"file_name":"large.txt","size_bytes":4096,"sha256":"abc"}'
        )

        self.assertEqual(
            SMOKE.extract_upload_stress_result(marker),
            {'file_name': 'large.txt', 'size_bytes': 4096, 'sha256': 'abc'},
        )

    def test_parse_args_accepts_replay_guard_smoke(self) -> None:
        args = SMOKE.parse_args(['--replay-guard-smoke'])

        self.assertTrue(args.replay_guard_smoke)

    def test_parse_args_accepts_attachment_rejection_smoke(self) -> None:
        args = SMOKE.parse_args(['--attachment-rejection-smoke'])

        self.assertTrue(args.attachment_rejection_smoke)

    def test_parse_args_accepts_replay_restart_smoke(self) -> None:
        args = SMOKE.parse_args(['--replay-restart-smoke'])

        self.assertTrue(args.replay_restart_smoke)

    def test_parse_args_accepts_replay_gateway_restart_smoke(self) -> None:
        args = SMOKE.parse_args(['--replay-gateway-restart-smoke'])

        self.assertTrue(args.replay_gateway_restart_smoke)

    def test_parse_args_accepts_revoke_repair_smoke(self) -> None:
        args = SMOKE.parse_args(['--revoke-repair-smoke'])

        self.assertTrue(args.revoke_repair_smoke)

    def test_native_artifact_text_body_can_be_sized_for_slow_download(self) -> None:
        body = SMOKE.native_artifact_text_body(
            run_id='unit-test',
            min_size_bytes=4096,
        )

        self.assertEqual(len(body), 4096)
        self.assertTrue(body.startswith(b'Generated native artifact text for unit-test'))

    def test_long_history_rollout_contains_mixed_markdown_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_home = root / '.ccb' / 'ccbd' / 'mobile'
            metadata = SMOKE.write_codex_long_history_rollout(
                project_root=root,
                state_home=state_home,
                project_id='project-alpha',
                agent='mobile_probe',
                run_id='unit-test',
                markers=[f'marker-{index:02d}' for index in range(56)],
            )

            rollout_path = Path(metadata['rollout_path'])
            self.assertTrue(rollout_path.is_file())
            text = rollout_path.read_text(encoding='utf-8')
            self.assertIn('## Mixed Markdown Section', text)
            self.assertIn('| field | value |', text)
            self.assertIn('```text', text)
            self.assertIn('ccb-artifact://mobile-long-history-doc-unit-test', text)
            self.assertIn('ccb-artifact://mobile-long-history-image-unit-test', text)

            records = [
                json.loads(line)
                for line in text.splitlines()
                if line.strip()
            ]
            messages = [
                record['payload']['message']
                for record in records
                if record.get('type') == 'event_msg'
            ]
            self.assertTrue(any(message.startswith('hi') for message in messages))
            self.assertEqual(len(metadata['artifact_files']), 2)
            for artifact in metadata['artifact_files']:
                file_id = artifact['file_id']
                metadata_path = (
                    state_home
                    / 'files'
                    / 'project-alpha'
                    / 'mobile_probe'
                    / file_id
                    / 'metadata.json'
                )
                self.assertTrue(metadata_path.is_file())


if __name__ == '__main__':
    unittest.main()
