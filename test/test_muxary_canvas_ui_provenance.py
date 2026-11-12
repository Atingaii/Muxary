from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'web/src/vendor/shadcn'
COMMIT = 'dd41d19e2f80ff6891951f7ced74c2c9a650b065'


@pytest.mark.parametrize('manifest', ['SOURCE-card.json', 'SOURCE-command-resizable.json'])
def test_selected_prototype_and_adapted_public_source_are_distinguished(manifest):
    source = json.loads((VENDOR / manifest).read_text())
    assert source['repository'] == 'https://github.com/shadcn-ui/ui'
    assert source['commit'] == COMMIT
    prototypes = source.get('prototypes') or [source['prototype']]
    assert all(item['url'].startswith('https://21st.dev/@') for item in prototypes)
    boundary = source.get('source_boundary') or source['prototype']['source_boundary']
    assert 'unverified' in boundary
    assert source['license']['spdx'] == 'MIT'
    license_bytes = (VENDOR / source['license']['path']).read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == source['license']['sha256']
    assert b'Copyright (c) 2023 shadcn' in license_bytes
    for name, record in source['files'].items():
        path = (VENDOR / name).resolve()
        assert path.is_relative_to(VENDOR.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['vendored_sha256']
        assert record['upstream_sha256'] != record['vendored_sha256']
        assert f'/{COMMIT}/' in record['upstream_source_url']
        assert record['local_modifications']


def test_behavior_engines_are_pinned_and_no_second_execution_sdk_is_added():
    package = json.loads((ROOT / 'web/package.json').read_text())
    assert package['dependencies']['@xyflow/react'] == '12.12.1'
    assert package['dependencies']['cmdk'] == '1.1.1'
    assert package['dependencies']['react-resizable-panels'] == '4.21.0'
    # The original agent-elements dependency remains; presentation additions do
    # not introduce a separate provider client or execution/scheduling SDK.
    assert set(package['dependencies']) == {'@tabler/icons-react', '@xterm/addon-fit', '@xterm/xterm', '@xyflow/react', 'ai', 'clsx', 'cmdk', 'react', 'react-dom', 'react-resizable-panels', 'streamdown', 'tailwind-merge'}
