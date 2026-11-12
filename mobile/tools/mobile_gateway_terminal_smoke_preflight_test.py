#!/usr/bin/env python3
"""Self-tests for Cloudflare named-tunnel preflight checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


MODULE_PATH = Path(__file__).with_name('mobile_gateway_terminal_smoke.py')
SPEC = importlib.util.spec_from_file_location('mobile_gateway_terminal_smoke', MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f'could not load {MODULE_PATH}')
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


class NamedTunnelPreflightTest(unittest.TestCase):
    def test_missing_config_blocks_before_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=root / 'missing.yml',
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertFalse(result['config_exists'])
        self.assertIn('cloudflared config not found', '\n'.join(result['missing']))
        self.assertIn('Run cloudflared tunnel login.', result['next_actions'])
        self.assertIn(
            'Run cloudflared tunnel route dns ccb-mobile mobile.example.com.',
            result['next_actions'],
        )
        self.assertIn('hostname: mobile.example.com', result['config_template'])
        self.assertIn('service: http://127.0.0.1:8787', result['config_template'])
        self.assertIn('credentials-file:', result['config_template'])

    def test_config_template_round_trips_to_ok_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'config.yml'
            blocked = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
            credentials = root / '<tunnel-uuid>.json'
            config.write_text(blocked['config_template'], encoding='utf-8')
            credentials.write_text('{}\n', encoding='utf-8')

            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )

        self.assertTrue(result['ok'], result)
        self.assertEqual(result['credentials_file'], str(credentials))
        self.assertEqual(result['origin_service'], 'http://127.0.0.1:8787')
        self.assertTrue(result['origin_matches_gateway_listen'])

    def test_dynamic_gateway_listen_blocks_with_fixed_port_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=root / 'missing.yml',
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:0',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertEqual(result['suggested_gateway_listen'], '127.0.0.1:8787')
        self.assertIn('fixed TCP port', '\n'.join(result['missing']))
        self.assertIn(
            'Pass --gateway-listen 127.0.0.1:8787',
            '\n'.join(result['next_actions']),
        )
        self.assertIn(
            '--gateway-listen 127.0.0.1:8787',
            result['named_tunnel_smoke_command'],
        )
        self.assertNotIn('127.0.0.1:0', result['named_tunnel_smoke_command'])
        self.assertIn('service: http://127.0.0.1:8787', result['config_template'])
        self.assertNotIn('service: http://127.0.0.1:0', result['config_template'])

    def test_non_loopback_gateway_listen_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: mobile.example.com
                    service: http://127.0.0.1:8787
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com',
                gateway_listen='0.0.0.0:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertIn('must be loopback', '\n'.join(result['missing']))
        self.assertEqual(result['suggested_gateway_listen'], '127.0.0.1:8787')

    def test_missing_config_uses_requested_tunnel_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / 'missing.yml'
            cloudflared = fake_cloudflared(root)
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(cloudflared),
                config_path=config,
                tunnel_name='team-mobile',
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertEqual(result['cloudflared_tunnel_name'], 'team-mobile')
        self.assertEqual(result['setup_tunnel_name'], 'team-mobile')
        self.assertIn('Run cloudflared tunnel create team-mobile.', result['next_actions'])
        self.assertIn(
            'Run cloudflared tunnel route dns team-mobile mobile.example.com.',
            result['next_actions'],
        )
        self.assertNotIn(
            'Run cloudflared tunnel route dns ccb-mobile mobile.example.com.',
            result['next_actions'],
        )
        smoke_command = result['named_tunnel_smoke_command']
        self.assertIn(f'--cloudflared-bin {cloudflared}', smoke_command)
        self.assertIn(f'--cloudflared-config {config}', smoke_command)
        self.assertIn('--cloudflared-tunnel-name team-mobile', smoke_command)
        self.assertIn('--gateway-listen 127.0.0.1:8787', smoke_command)
        self.assertIn('--gateway-public-url https://mobile.example.com', smoke_command)
        self.assertEqual(
            result['cloudflared_run_command'],
            f'{cloudflared} tunnel --config {config} run team-mobile',
        )
        self.assertNotIn(
            '--cloudflared-named-tunnel',
            result['existing_tunnel_smoke_command'],
        )
        self.assertIn(
            '--gateway-public-url https://mobile.example.com',
            result['existing_tunnel_smoke_command'],
        )

    def test_public_url_path_query_fragment_blocks_with_origin_suggestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: mobile.example.com
                    service: http://127.0.0.1:8787
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com/mobile?debug=1#pair',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertEqual(result['suggested_gateway_public_url'], 'https://mobile.example.com')
        self.assertIn('without a path', '\n'.join(result['missing']))
        self.assertIn('query', '\n'.join(result['missing']))
        self.assertIn(
            'Use --gateway-public-url https://mobile.example.com.',
            result['next_actions'],
        )
        self.assertIn(
            '--gateway-public-url https://mobile.example.com',
            result['named_tunnel_smoke_command'],
        )
        self.assertNotIn('/mobile?debug=1', result['named_tunnel_smoke_command'])
        self.assertIn(
            '--gateway-public-url https://mobile.example.com',
            result['existing_tunnel_smoke_command'],
        )
        self.assertNotIn('/mobile?debug=1', result['existing_tunnel_smoke_command'])

    def test_public_url_trailing_slash_keeps_preflight_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: mobile.example.com
                    service: http://127.0.0.1:8787
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com/',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['suggested_gateway_public_url'], 'https://mobile.example.com')
        self.assertIn(
            '--gateway-public-url https://mobile.example.com',
            result['named_tunnel_smoke_command'],
        )
        self.assertNotIn('https://mobile.example.com/', result['named_tunnel_smoke_command'])

    def test_matching_hostname_origin_passes_local_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: other.example.com
                    service: http://127.0.0.1:9999
                  - hostname: mobile.example.com
                    service: http://localhost:8787
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                tunnel_name='team-mobile',
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['origin_service'], 'http://localhost:8787')
        self.assertEqual(result['origin_selection'], 'matched_hostname')
        self.assertTrue(result['origin_matches_gateway_listen'])
        self.assertEqual(result['missing'], [])
        self.assertIn('Preflight passed; run', result['next_actions'][0])
        self.assertIn('--cloudflared-tunnel-name team-mobile', result['next_actions'][0])
        self.assertEqual(
            result['named_tunnel_smoke_command'] + '.',
            result['next_actions'][0].removeprefix('Preflight passed; run '),
        )

    def test_matching_hostname_wrong_port_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: mobile.example.com
                    service: http://127.0.0.1:9999
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertIn('does not match gateway listen', '\n'.join(result['missing']))
        self.assertIn(
            'Change the matched ingress service to http://127.0.0.1:8787.',
            result['next_actions'],
        )
        self.assertIn('hostname: mobile.example.com', result['config_template'])
        self.assertIn('service: http://127.0.0.1:8787', result['config_template'])

    def test_missing_hostname_in_multi_origin_config_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            creds = root / 'tunnel-uuid.json'
            creds.write_text('{}\n', encoding='utf-8')
            config = write_config(
                root,
                """
                tunnel: tunnel-uuid
                credentials-file: tunnel-uuid.json

                ingress:
                  - hostname: other.example.com
                    service: http://127.0.0.1:8787
                  - hostname: admin.example.com
                    service: http://127.0.0.1:8788
                  - service: http_status:404
                """,
            )
            result = SMOKE.cloudflared_named_tunnel_preflight(
                cloudflared_bin=str(fake_cloudflared(root)),
                config_path=config,
                gateway_public_url='https://mobile.example.com',
                gateway_listen='127.0.0.1:8787',
                route_provider='cloudflare_tunnel',
            )
        self.assertFalse(result['ok'])
        self.assertEqual(result['origin_selection'], 'none')
        self.assertIn('no HTTP ingress service for hostname', '\n'.join(result['missing']))
        self.assertIn(
            'Add an ingress rule with hostname mobile.example.com and service '
            'http://127.0.0.1:8787.',
            result['next_actions'],
        )

    def test_start_named_tunnel_waits_for_registered_connection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            process = None
            try:
                result = SMOKE.start_cloudflared_named_tunnel(
                    cloudflared_bin=str(fake_named_cloudflared(root)),
                    config_path=root / 'config.yml',
                    tunnel_name='ccb-mobile',
                    timeout_s=2,
                )
                process = result['process']
                self.assertEqual(result['mode'], 'named')
                self.assertEqual(result['tunnel_name'], 'ccb-mobile')
                self.assertIn('Registered tunnel connection', result['stderr'])
                self.assertIsNone(process.poll())
            finally:
                if process is not None and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)
                if process is not None:
                    SMOKE.close_process_pipes(process)

    def test_start_named_tunnel_reports_startup_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(RuntimeError, 'exited during startup'):
                SMOKE.start_cloudflared_named_tunnel(
                    cloudflared_bin=str(fake_failing_cloudflared(root)),
                    config_path=root / 'config.yml',
                    tunnel_name=None,
                    timeout_s=2,
                )

    def test_named_tunnel_cli_preflight_failure_does_not_create_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / 'project'
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    '--project-root',
                    str(project_root),
                    '--source-ccb',
                    str(root / 'missing-ccb'),
                    '--cloudflared-named-tunnel',
                    '--cloudflared-bin',
                    str(fake_cloudflared(root)),
                    '--cloudflared-config',
                    str(root / 'missing-config.yml'),
                    '--gateway-listen',
                    '127.0.0.1:8787',
                    '--gateway-public-url',
                    'https://mobile.example.com',
                    '--route-provider',
                    'cloudflare_tunnel',
                    '--gateway-timeout',
                    '1',
                    '--cloudflared-timeout',
                    '1',
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(payload['status'], 'error')
        self.assertEqual(payload['cleanup'], {'keep_running': False, 'runtime_started': False})
        self.assertEqual(payload['named_tunnel_preflight']['status'], 'blocked')
        self.assertIn(
            'hostname: mobile.example.com',
            payload['named_tunnel_preflight']['named_tunnel_preflight']['config_template'],
        )
        self.assertFalse(project_root.exists())


def fake_cloudflared(root: Path) -> Path:
    binary = root / 'cloudflared'
    binary.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = "--version" ]; then\n'
        '  echo "cloudflared version test"\n'
        '  exit 0\n'
        'fi\n'
        'exit 0\n',
        encoding='utf-8',
    )
    binary.chmod(0o755)
    return binary


def fake_named_cloudflared(root: Path) -> Path:
    binary = root / 'cloudflared-named'
    binary.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = "--version" ]; then\n'
        '  echo "cloudflared version test"\n'
        '  exit 0\n'
        'fi\n'
        'echo "INF Registered tunnel connection" >&2\n'
        'exec sleep 30\n',
        encoding='utf-8',
    )
    binary.chmod(0o755)
    return binary


def fake_failing_cloudflared(root: Path) -> Path:
    binary = root / 'cloudflared-failing'
    binary.write_text(
        '#!/bin/sh\n'
        'echo "ERR credentials file not found" >&2\n'
        'exit 1\n',
        encoding='utf-8',
    )
    binary.chmod(0o755)
    return binary


def write_config(root: Path, text: str) -> Path:
    config = root / 'config.yml'
    config.write_text(textwrap.dedent(text).lstrip(), encoding='utf-8')
    return config


if __name__ == '__main__':
    unittest.main()
