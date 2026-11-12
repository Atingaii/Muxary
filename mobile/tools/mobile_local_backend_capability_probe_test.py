#!/usr/bin/env python3
"""Self-tests for the local real-backend capability probe."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name('mobile_local_backend_capability_probe.py')
SPEC = importlib.util.spec_from_file_location(
    'mobile_local_backend_capability_probe',
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f'could not load {MODULE_PATH}')
PROBE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROBE
SPEC.loader.exec_module(PROBE)


class ManualClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        current = self.value
        self.value += 0.001
        return current

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeClient:
    def __init__(
        self,
        *,
        conversations: list[dict[str, object]] | None = None,
        file_routes: bool = True,
        nested_claim: bool = False,
        revoke_enforced: bool = True,
    ) -> None:
        self.calls: list[tuple[str, str, object | None, str | None]] = []
        self.conversations = list(conversations or [conversation_with_reply('reply-1')])
        self.file_routes = file_routes
        self.nested_claim = nested_claim
        self.revoke_enforced = revoke_enforced
        self.revoked = False
        self.artifact_run_id = ''

    def json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, object]]:
        self.calls.append((method, path, payload, token))
        if path == '/v1/devices/dev-1/revoke':
            self.revoked = True
            return 200, {'device': {'device_id': 'dev-1', 'revoked': True}}
        if self.revoked and self.revoke_enforced and token == 'token-1':
            raise PROBE.ProbeHttpError(
                method=method,
                path=path,
                status=401,
                body='device token revoked',
            )
        if path == '/v1/health':
            return 200, {'status': 'ok', 'capabilities': ['view', 'message_submit']}
        if path == '/v1/devices/me':
            return 200, {'device': {'device_id': 'dev-1', 'revoked': self.revoked}}
        if path == '/v1/pairing/claim':
            if self.nested_claim:
                return 201, {
                    'device': {'device_id': 'dev-1', 'project_id': 'proj-real'},
                    'device_token': 'token-1',
                    'host_profile': {
                        'device_id': 'dev-1',
                        'project_id': 'proj-real',
                        'scopes': ['view', 'file_upload', 'file_download'],
                    },
                }
            return 201, {
                'project_id': 'proj-real',
                'device_id': 'dev-1',
                'device_token': 'token-1',
                'scopes': ['view', 'message_submit'],
            }
        if path == '/v1/projects/proj-real/view':
            return 200, {
                'view': {
                    'project': {'id': 'proj-real'},
                    'namespace': {'epoch': 7},
                    'agents': [{'name': 'mobile_probe'}],
                }
            }
        if path == '/v1/projects/proj-real/terminals':
            return 201, {
                'terminal_id': 'term-1',
                'terminal_token': 'terminal-token-1',
            }
        if path == '/v1/projects/proj-real/agents/mobile_probe/messages':
            body = str((payload or {}).get('body') or '')
            if body.startswith('ccb-local-artifact:'):
                self.artifact_run_id = body.split(':', 1)[1]
            return 202, {
                'message_submit': {
                    'accepted': True,
                    'message_id': 'job-1',
                    'job_id': 'job-1',
                    'state': 'queued',
                }
            }
        if path.startswith('/v1/projects/proj-real/agents/mobile_probe/conversation?'):
            if self.artifact_run_id:
                return 200, conversation_with_artifact(self.artifact_run_id)
            if len(self.conversations) > 1:
                return 200, self.conversations.pop(0)
            return 200, self.conversations[0]
        raise AssertionError(f'unexpected JSON request: {method} {path}')

    def bytes(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
    ) -> tuple[int, bytes]:
        self.calls.append((method, path, data, token))
        if self.revoked and self.revoke_enforced and token == 'token-1':
            raise PROBE.ProbeHttpError(
                method=method,
                path=path,
                status=401,
                body='device token revoked',
            )
        if not self.file_routes:
            raise PROBE.ProbeHttpError(
                method=method,
                path=path,
                status=404,
                body='not found',
            )
        if method == 'POST' and path == '/v1/projects/proj-real/agents/mobile_probe/files':
            return 201, json.dumps(
                {
                    'file_id': 'file-1',
                    'file_name': 'local-backend-probe.txt',
                    'size_bytes': len(data or b''),
                }
            ).encode('utf-8')
        if method == 'GET' and path == '/v1/projects/proj-real/agents/mobile_probe/files/file-1':
            return 200, b'ccb mobile local backend file probe\n'
        if (
            method == 'GET'
            and self.artifact_run_id
            and path
            == (
                '/v1/projects/proj-real/agents/mobile_probe/files/'
                f'artifact-file-{self.artifact_run_id}'
            )
        ):
            return 200, f'Generated text artifact for {self.artifact_run_id}'.encode(
                'utf-8'
            )
        raise AssertionError(f'unexpected bytes request: {method} {path}')


def conversation_with_reply(marker: str) -> dict[str, object]:
    return {
        'conversation': {
            'items': [
                {'kind': 'status_event', 'body': 'ready'},
                {'kind': 'agent_reply', 'body': f'agent says {marker}'},
            ]
        }
    }


def conversation_without_reply() -> dict[str, object]:
    return {
        'conversation': {
            'items': [
                {'kind': 'user_message', 'body': 'ccb-local-echo:blocked'},
                {'kind': 'comms_item', 'body': 'ccb-local-reply:blocked'},
            ]
        }
    }


def conversation_with_artifact(run_id: str) -> dict[str, object]:
    return {
        'conversation': {
            'items': [
                {
                    'kind': 'agent_reply',
                    'body': f'CCB Local Artifacts {run_id}',
                    'attachments': [
                        {
                            'file_id': f'artifact-file-{run_id}',
                            'file_name': f'artifact-{run_id}.txt',
                            'mime_type': 'text/plain',
                            'size_bytes': len(f'Generated text artifact for {run_id}'),
                            'kind': 'document',
                        }
                    ],
                }
            ]
        }
    }


class LocalBackendCapabilityProbeTest(unittest.TestCase):
    def test_conversation_marker_requires_agent_reply_kind(self) -> None:
        self.assertTrue(
            PROBE.conversation_has_agent_reply_marker(
                conversation_with_reply('ccb-local-reply:1'),
                'ccb-local-reply:1',
            )
        )
        self.assertFalse(
            PROBE.conversation_has_agent_reply_marker(
                conversation_without_reply(),
                'ccb-local-reply:blocked',
            )
        )

    def test_run_probe_success_records_all_gates(self) -> None:
        clock = ManualClock()
        result = PROBE.run_probe(
            PROBE.ProbeConfig(
                gateway_url='http://127.0.0.1:8787',
                pairing_code='pair-1',
                project_id=None,
                agent='mobile_probe',
                send_body='ccb-local-echo:1',
                reply_marker='reply-1',
                reply_timeout_seconds=1,
                poll_interval_seconds=0.01,
            ),
            client=FakeClient(),
            clock=clock,
            sleep=clock.sleep,
        )

        self.assertEqual(result['status'], 'ok')
        statuses = {step['name']: step['status'] for step in result['steps']}
        self.assertEqual(statuses['health'], 'pass')
        self.assertEqual(statuses['pairing_claim'], 'pass')
        self.assertEqual(statuses['project_view'], 'pass')
        self.assertEqual(statuses['message_submit'], 'pass')
        self.assertEqual(statuses['agent_reply_marker'], 'pass')
        self.assertEqual(statuses['file_upload_route'], 'pass')
        self.assertEqual(statuses['file_download_route'], 'pass')
        self.assertEqual(result['timing']['samples'], 8)

    def test_run_probe_accepts_source_nested_claim_payload(self) -> None:
        clock = ManualClock()
        result = PROBE.run_probe(
            PROBE.ProbeConfig(
                gateway_url='http://127.0.0.1:8787',
                pairing_code='pair-1',
                project_id=None,
                agent='mobile_probe',
                send_body='ccb-local-echo:1',
                reply_marker='reply-1',
                reply_timeout_seconds=1,
                poll_interval_seconds=0.01,
            ),
            client=FakeClient(nested_claim=True),
            clock=clock,
            sleep=clock.sleep,
        )

        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['project_id'], 'proj-real')

    def test_run_probe_revoke_gate_proves_routes_fail_closed(self) -> None:
        clock = ManualClock()
        client = FakeClient()
        result = PROBE.run_probe(
            PROBE.ProbeConfig(
                gateway_url='http://127.0.0.1:8787',
                pairing_code='pair-1',
                project_id=None,
                agent='mobile_probe',
                send_body='ccb-local-echo:1',
                reply_marker='reply-1',
                reply_timeout_seconds=1,
                poll_interval_seconds=0.01,
                include_revoke_gate=True,
            ),
            client=client,
            clock=clock,
            sleep=clock.sleep,
        )

        self.assertEqual(result['status'], 'ok')
        statuses = {step['name']: step['status'] for step in result['steps']}
        self.assertEqual(statuses['revoke_fail_closed'], 'pass')
        revoke = next(
            step for step in result['steps'] if step['name'] == 'revoke_fail_closed'
        )
        details = revoke['details']
        self.assertEqual(details['device_id'], 'dev-1')
        denied_paths = {
            route['path'] for route in details['denied_routes']
        }
        self.assertIn('/v1/devices/me', denied_paths)
        self.assertIn('/v1/projects/proj-real/view', denied_paths)
        self.assertIn('/v1/projects/proj-real/agents/mobile_probe/messages', denied_paths)
        self.assertIn('/v1/projects/proj-real/terminals', denied_paths)
        self.assertIn(
            '/v1/projects/proj-real/agents/mobile_probe/files/file-1',
            denied_paths,
        )

    def test_run_probe_revoke_gate_fails_if_routes_still_work(self) -> None:
        clock = ManualClock()
        result = PROBE.run_probe(
            PROBE.ProbeConfig(
                gateway_url='http://127.0.0.1:8787',
                pairing_code='pair-1',
                project_id=None,
                agent='mobile_probe',
                send_body='ccb-local-echo:1',
                reply_marker='reply-1',
                reply_timeout_seconds=1,
                poll_interval_seconds=0.01,
                include_revoke_gate=True,
            ),
            client=FakeClient(revoke_enforced=False),
            clock=clock,
            sleep=clock.sleep,
        )

        self.assertEqual(result['status'], 'fail')
        statuses = {step['name']: step['status'] for step in result['steps']}
        self.assertEqual(statuses['revoke_fail_closed'], 'fail')

    def test_run_probe_blocks_on_missing_reply_and_file_routes(self) -> None:
        clock = ManualClock()
        result = PROBE.run_probe(
            PROBE.ProbeConfig(
                gateway_url='http://127.0.0.1:8787',
                pairing_code='pair-1',
                project_id=None,
                agent='mobile_probe',
                send_body='ccb-local-echo:blocked',
                reply_marker='ccb-local-reply:blocked',
                reply_timeout_seconds=0.03,
                poll_interval_seconds=0.01,
            ),
            client=FakeClient(
                conversations=[conversation_without_reply()],
                file_routes=False,
            ),
            clock=clock,
            sleep=clock.sleep,
        )

        self.assertEqual(result['status'], 'blocked')
        statuses = {step['name']: step['status'] for step in result['steps']}
        self.assertEqual(statuses['agent_reply_marker'], 'blocked')
        self.assertEqual(statuses['file_upload_route'], 'blocked')
        self.assertEqual(statuses['file_download_route'], 'blocked')
        self.assertIn('deterministic local backend fixture', result['next_actions'][0])
        self.assertTrue(
            any('/files upload' in action for action in result['next_actions']),
            result['next_actions'],
        )

    def test_overall_status_precedence(self) -> None:
        self.assertEqual(PROBE.overall_status([]), 'blocked')
        self.assertEqual(
            PROBE.overall_status([{'status': 'pass'}, {'status': 'blocked'}]),
            'blocked',
        )
        self.assertEqual(
            PROBE.overall_status([{'status': 'blocked'}, {'status': 'fail'}]),
            'fail',
        )
        self.assertEqual(PROBE.overall_status([{'status': 'pass'}]), 'ok')

    def test_percentile_interpolates(self) -> None:
        self.assertEqual(PROBE.percentile([1.0], 95), 1.0)
        self.assertEqual(PROBE.percentile([1.0, 2.0, 3.0], 50), 2.0)
        self.assertEqual(PROBE.percentile([10.0, 20.0, 30.0, 40.0], 95), 38.5)


if __name__ == '__main__':
    unittest.main()
