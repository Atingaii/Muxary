from __future__ import annotations

import hashlib
import hmac
from contextlib import contextmanager
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import selectors
import sqlite3
import stat
import subprocess
import threading
import time
from typing import Callable
from urllib.parse import parse_qs, unquote, urlsplit

from ccbd.api_models import DeliveryScope, MessageEnvelope
from ccbd.socket_client import CcbdClientError
from mobile_gateway import MobileGatewayError, MobileGatewayProjectRegistry, MobileGatewayService
from mobile_gateway.pairing import MobileGatewayPairingStore
from mobile_gateway.websocket import accept_websocket, is_websocket_upgrade
from project.identity import resolve_project_root
from project.ids import compute_project_id
from workspace.binding import WorkspaceBindingStore
from workbench.workspaces import git_environment, inspect_workspace

_COOKIE = 'muxary_session'
_TERMINAL = frozenset({'completed', 'failed', 'incomplete', 'cancelled'})
_SCOPES = ('view', 'content', 'terminal_input', 'lifecycle', 'provider_settings', 'message_submit')
_JOB_ID = re.compile(r'^job_[a-zA-Z0-9_-]+$')
_HTTP_READ_TIMEOUT = 10.0


def _error(code: str, **details) -> dict:
    return {'schema_version': 1, 'error': code, **details}


def _project_open_root(value: object) -> Path:
    """Read CCB's existing project identity; never bootstrap or change a cwd."""
    if (not isinstance(value, str) or not value or len(value) > 4096 or
            any(character in value for character in ('\x00', '\r', '\n'))):
        raise ValueError('absolute project directory is required (1..4096 characters)')
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('absolute project directory is required')
    path = path.resolve(strict=True)
    if not path.is_dir():
        raise ValueError('project path must be a directory')
    # Resolve worktree aliases exactly as CCB does, but reject malformed,
    # oversized, or special-file bindings before the existing JSON reader.
    marker = None
    for parent in (path, *path.parents):
        candidate = parent / '.ccb-workspace.json'
        if candidate.exists() or candidate.is_symlink():
            info = candidate.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
                raise ValueError('workspace binding must be a bounded regular file')
            marker = candidate
            break
    owner = resolve_project_root(path).resolve(strict=True)
    if not owner.is_dir():
        raise ValueError('workspace owner project directory is unavailable')
    if marker is not None:
        binding = WorkspaceBindingStore().load(marker)
        if (not (owner / '.ccb').is_dir() or binding.project_id != compute_project_id(owner) or
                not Path(binding.target_project).is_absolute() or
                not Path(binding.workspace_path).is_absolute() or
                Path(binding.workspace_path).resolve(strict=True) != marker.parent):
            raise ValueError(f'workspace binding cannot be confirmed; open its project root: {owner}')
    return owner


class WorkbenchService:
    """A transport adapter, not a job scheduler or completion authority.

    The receipt ledger records whether one HTTP mutation was sent; only ccbd
    owns jobs. An ambiguous mutation is never resent, even after a restart.
    """

    def __init__(self, *, project_registry: MobileGatewayProjectRegistry,
                 assets_dir: Path, state_dir: Path | None = None,
                 config_opener: Callable[[object], str] | None = None,
                 project_registry_provider: Callable[[], MobileGatewayProjectRegistry | None] | None = None,
                 project_opener: Callable[[Path], int] | None = None,
                 gateway: MobileGatewayService | None = None) -> None:
        self.registry = project_registry
        self._registry_lock = threading.Lock()
        self._registry_refresh_generation = 0
        self._project_registry_provider = project_registry_provider
        self._project_opener = project_opener
        self._project_open_lock = threading.Lock()
        self._uncertain_project_roots: set[Path] = set()
        self.assets_dir = Path(assets_dir).resolve()
        self.state_dir = Path(state_dir or Path.home() / '.local/state/muxary/workbench').expanduser()
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.bootstrap_token = secrets.token_urlsafe(32)
        self._bootstrap_used = False
        self._sessions: dict[str, float] = {}
        self._auth_lock = threading.Lock()
        self._receipts_lock = threading.Lock()
        self._config_opener = config_opener
        self.origin: str | None = None
        self._db_path = self.state_dir / 'requests.sqlite3'
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS receipts (scope TEXT, key TEXT, fingerprint TEXT NOT NULL, '
                       'status INTEGER, payload TEXT, PRIMARY KEY(scope,key))')
        self._db_path.chmod(0o600)
        default = project_registry.default_project
        self._pairing = MobileGatewayPairingStore(self.state_dir / 'gateway')
        pairing = self._pairing.create_pairing_payload(
            project_id=default.project_id, gateway_url='http://127.0.0.1', scopes=_SCOPES)
        claimed = self._pairing.claim_pairing(pairing_code=pairing['pairing_code'], device_name='Muxary workbench')
        self._device_id = claimed['device']['device_id']
        self._gateway_headers = {'Authorization': f"Bearer {claimed['device_token']}"}
        self.gateway = gateway or MobileGatewayService(
            project_id=default.project_id, project_root=default.project_root,
            ccbd_client_factory=default.ccbd_client_factory, project_registry=project_registry,
            project_registry_provider=self._registry_snapshot,
            mobile_dir=self.state_dir / 'gateway', pairing_store=self._pairing,
            mode='loopback_server_registry')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self._db_path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def close(self) -> None:
        if getattr(self, '_closed', False):
            return
        self._closed = True
        self.gateway.close()
        self._pairing.revoke_device_locally(device_id=self._device_id, reason='workbench_closed')
        with self._auth_lock:
            self._sessions.clear()

    def authenticate(self, cookie: str) -> bool:
        cookies = SimpleCookie()
        try:
            cookies.load(cookie)
        except Exception:
            return False
        token = cookies.get(self.session_cookie_name)
        if token is None:
            return False
        digest = hashlib.sha256(token.value.encode()).hexdigest()
        with self._auth_lock:
            expires = self._sessions.get(digest, 0)
            if expires <= time.monotonic():
                self._sessions.pop(digest, None)
                return False
        return True

    def create_session(self, token: object) -> str:
        with self._auth_lock:
            if (not isinstance(token, str) or not token.isascii() or self._bootstrap_used or
                    not hmac.compare_digest(token, self.bootstrap_token)):
                raise MobileGatewayError('bootstrap token denied', status_code=401)
            self._bootstrap_used = True
            session = secrets.token_urlsafe(32)
            self._sessions[hashlib.sha256(session.encode()).hexdigest()] = time.monotonic() + 12 * 3600
            return session

    @property
    def session_cookie_name(self) -> str:
        # Cookies ignore ports. Distinct loopback instances must not overwrite
        # each other's login; this is not isolation from local OS processes.
        return f'{_COOKIE}_{urlsplit(self.origin or "").port or 0}'

    def _project(self, project_id: str):
        project = self._registry_snapshot().get(project_id)
        if project is None:
            raise MobileGatewayError('project not found', status_code=404)
        return project

    def _registry_snapshot(self) -> MobileGatewayProjectRegistry:
        with self._registry_lock:
            return self.registry

    def _refresh_registry(self) -> MobileGatewayProjectRegistry:
        # Discovery may probe processes/endpoints. Never hold the shared lock
        # during discovery, CCB startup, or control-plane requests.
        if self._project_registry_provider is not None:
            with self._registry_lock:
                self._registry_refresh_generation += 1
                generation = self._registry_refresh_generation
            registry = self._project_registry_provider()
            if registry is not None:
                with self._registry_lock:
                    if generation == self._registry_refresh_generation:
                        self.registry = registry
                # A newer request may still be discovering. The caller must
                # be able to inspect its own completed candidate rather than
                # mistake the previously published snapshot for fresh evidence.
                return registry
        return self._registry_snapshot()

    def _registered_root(self, root: Path, *, registry: MobileGatewayProjectRegistry | None = None):
        matches = [project for project in (registry or self._registry_snapshot()).projects()
                   if project.project_root.resolve() == root]
        if len(matches) > 1:
            raise ValueError('ambiguous project root in registry')
        return matches[0] if matches else None

    def _publish_confirmed_project(self, project) -> None:
        # Publish only the identity/mount-confirmed entry, preserving unrelated
        # current projects. Fence every discovery already in flight, including
        # one that began after this open's own discovery but before its RPC.
        with self._registry_lock:
            projects = list(self.registry.projects())
            for index, current in enumerate(projects):
                if current.project_id == project.project_id:
                    projects[index] = project
                    break
            else:
                projects.append(project)
            self.registry = MobileGatewayProjectRegistry(projects)
            self._registry_refresh_generation += 1

    @staticmethod
    def _project_is_ready(project, root: Path) -> bool:
        client = project.client()
        if callable(getattr(client, 'with_timeout', None)):
            client = client.with_timeout(3)
        payload = client.project_view(schema_version=1)
        view = payload.get('view') if isinstance(payload, dict) else None
        identity = view.get('project') if isinstance(view, dict) else None
        if (not isinstance(identity, dict) or identity.get('id') != project.project_id or
                project.project_id != compute_project_id(root) or
                not isinstance(identity.get('root'), str) or
                Path(identity['root']).resolve(strict=True) != root):
            raise ValueError('project startup identity could not be confirmed')
        return view.get('ccbd', {}).get('state') == 'mounted'

    def _open_project(self, body: dict) -> tuple[int, dict]:
        if set(body) != {'path'}:
            raise MobileGatewayError('only path is accepted', status_code=400)
        try:
            root = _project_open_root(body['path'])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise MobileGatewayError(str(exc), status_code=400) from exc
        if self._project_opener is None or getattr(self, '_closed', False):
            return 503, _error('project_open_unavailable', outcome_unknown=False,
                               refresh_required=False, retry_safe=True)
        if not self._project_open_lock.acquire(blocking=False):
            return 409, _error('project_open_in_progress', outcome_unknown=False,
                               refresh_required=True, retry_safe=True)
        attempted = False
        try:
            registry = self._refresh_registry()
            # Preflight can finish after another discovery has published a
            # live target. Prefer that current entry before an older candidate
            # can authorize a redundant launcher invocation.
            project = self._registered_root(root)
            if project is None:
                project = self._registered_root(root, registry=registry)
            if project is not None and self._project_is_ready(project, root):
                self._publish_confirmed_project(project)
                self._uncertain_project_roots.discard(root)
                return 200, {'schema_version': 1, 'project_id': project.project_id,
                             'root': str(root), 'status': 'ready'}
            if root in self._uncertain_project_roots:
                return 409, _error('project_start_outcome_unknown', outcome_unknown=True,
                                   refresh_required=True, retry_safe=False, root=str(root))
            attempted = True
            result = self._project_opener(root)
            if result != 0:
                raise RuntimeError('CCB project startup failed')
            registry = self._refresh_registry()
            project = self._registered_root(root, registry=registry)
            if project is None or not self._project_is_ready(project, root):
                raise RuntimeError('CCB project startup is not confirmed')
            self._publish_confirmed_project(project)
            return 200, {'schema_version': 1, 'project_id': project.project_id,
                         'root': str(root), 'status': 'ready'}
        except Exception as exc:
            if attempted:
                self._uncertain_project_roots.add(root)
            # Never force/restart, roll back, or kill existing agents. A
            # successful subprocess exit alone is not proof of readiness.
            return (504 if isinstance(exc, subprocess.TimeoutExpired) else 503), _error(
                'project_start_timeout' if isinstance(exc, subprocess.TimeoutExpired) else 'project_open_unconfirmed',
                outcome_unknown=True, refresh_required=True, retry_safe=False, root=str(root))
        finally:
            self._project_open_lock.release()

    def _job(self, project, job_id: str) -> dict:
        if not _JOB_ID.fullmatch(job_id):
            raise MobileGatewayError('invalid job id', status_code=400)
        try:
            result = project.client().get(job_id)
        except CcbdClientError as exc:
            raise MobileGatewayError('job unavailable', status_code=503) from exc
        if not isinstance(result, dict):
            raise MobileGatewayError('invalid job response', status_code=502)
        job = result.get('job')
        request = job.get('request') if isinstance(job, dict) else None
        # Never trust a client-supplied project, alias, or an unscoped receipt.
        if (result.get('job_id') != job_id or not isinstance(job, dict) or job.get('job_id') != job_id or not isinstance(request, dict) or
                request.get('project_id') != project.project_id):
            raise MobileGatewayError('job not found in project', status_code=404)
        return result

    def _view(self, project) -> dict:
        payload = project.client().project_view(schema_version=1)
        view = payload.get('view') if isinstance(payload, dict) else None
        identity = view.get('project') if isinstance(view, dict) else None
        if not isinstance(identity, dict) or identity.get('id') != project.project_id:
            raise MobileGatewayError('project identity mismatch', status_code=409)
        return view

    def _list_jobs(self, project, query: str) -> dict:
        params = parse_qs(query)
        agent = params.get('agent', [''])[0]
        view = self._view(project)
        agents = [item for item in view.get('agents', []) if isinstance(item, dict)]
        if agent and not any(item.get('name') == agent for item in agents):
            raise MobileGatewayError('agent not found', status_code=404)
        ids = []
        if agent:
            queue = project.client().queue(agent, detail=True)
            detail = queue.get('agent', {})
            events = [detail.get('active'), *detail.get('queued_events', [])]
            ids.extend(item.get('job_id') for item in events if isinstance(item, dict))
        for item in agents:
            if not agent or item.get('name') == agent:
                ids.append(item.get('current_job_id'))
        for item in view.get('comms', []):
            if isinstance(item, dict) and (not agent or item.get('target') == agent):
                ids.append(item.get('id'))
        jobs = []
        seen = set()
        for job_id in ids:
            if not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id) or job_id in seen:
                continue
            seen.add(job_id)
            result = self._job(project, job_id)
            record = result['job']
            if not agent or record.get('agent_name') == agent:
                jobs.append({**record, 'reply': result.get('reply', ''),
                             'completion_reason': result.get('completion_reason'),
                             'completion_confidence': result.get('completion_confidence')})
            if len(jobs) >= 30:
                break
        return {'schema_version': 1, 'project_id': project.project_id, 'jobs': jobs,
                'source': 'ccbd_queue_and_project_view', 'history_complete': False}

    def _mutation(self, scope: str, body: dict, action: Callable[[], tuple[int, dict]],
                  *, preflight: Callable[[], None] | None = None) -> tuple[int, dict]:
        key = body.get('idempotency_key')
        if not isinstance(key, str) or not key.strip() or len(key) > 128:
            raise MobileGatewayError('idempotency_key is required (1..128 characters)', status_code=400)
        fingerprint = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self._receipts_lock, self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT fingerprint,status,payload FROM receipts WHERE scope=? AND key=?', (scope, key)).fetchone()
            if row is not None:
                if row[0] != fingerprint:
                    return 409, _error('idempotency_conflict')
                if row[1] is None:
                    return 503, _error('outcome_unknown', idempotency_key=key, retry_safe=False)
                return row[1], {**json.loads(row[2]), 'replayed': True}
            if preflight is not None:
                preflight()
            db.execute('INSERT INTO receipts(scope,key,fingerprint) VALUES(?,?,?)', (scope, key, fingerprint))
        try:
            status, result = action()
            if not isinstance(result, dict):
                raise ValueError('invalid mutation receipt')
        except Exception:
            # The RPC may already have committed. No transport retry is safe.
            status, result = 503, _error('outcome_unknown', idempotency_key=key, retry_safe=False)
        try:
            with self._receipts_lock, self._db() as db:
                db.execute('UPDATE receipts SET status=?,payload=? WHERE scope=? AND key=?',
                           (status, json.dumps(result), scope, key))
        except Exception:
            # The pending reservation was committed before the RPC. A failed
            # receipt write must not turn an already-sent action into a denial.
            return 503, _error('outcome_unknown', idempotency_key=key, retry_safe=False)
        return status, result

    def dispatch(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        body = body or {}
        parsed = urlsplit(path)
        parts = [unquote(part) for part in parsed.path.strip('/').split('/')]
        if method == 'GET' and parts == ['api', 'session']:
            return 200, {'authenticated': True, 'schema_version': 1}
        if method == 'GET' and parts == ['api', 'projects']:
            self._refresh_registry()
            payload = self.gateway.projects_payload()
            listed = {item['id'] for item in payload.get('projects', [])}
            # Mobile intentionally hides unmounted projects; a desktop picker
            # must still show registry entries without pretending they are up.
            missing = [{'id': project.project_id, 'root': str(project.project_root),
                        'display_name': project.public_display_name, 'health': 'unknown',
                        'availability': 'unknown', 'health_freshness': 'unknown'}
                       for project in self.registry.projects() if project.project_id not in listed]
            return 200, {**payload, 'projects': [*payload.get('projects', []), *missing]}
        if method == 'POST' and parts == ['api', 'projects', 'open']:
            return self._open_project(body)
        if method == 'GET' and parts == ['api', 'config']:
            return 200, {'available': self._config_opener is not None, 'command': 'ccb config ui'}
        if len(parts) < 4 or parts[:2] != ['api', 'projects']:
            raise MobileGatewayError('not found', status_code=404)
        project = self._project(parts[2])
        route = parts[3:]
        if method == 'GET' and len(route) == 3 and route[0] == 'agents' and route[2] == 'workspace':
            return 200, inspect_workspace(project, self._view(project), route[1])
        if method == 'GET' and route == ['diff']:
            params = parse_qs(parsed.query, keep_blank_values=True)
            if 'agent' in params:
                if len(params['agent']) != 1 or not params['agent'][0]:
                    raise MobileGatewayError('invalid agent query', status_code=400)
                summary = inspect_workspace(project, self._view(project), params['agent'][0])
                if (summary['workspace']['mode'] == 'copy' or
                        summary['workspace']['git_state'] not in ('attached', 'detached')):
                    raise MobileGatewayError('workspace git diff unavailable', status_code=409)
                return 200, {**summary, **self._diff(Path(summary['workspace']['path']))}
            return 200, self._diff(project.project_root)
        if method == 'POST' and route == ['config', 'open']:
            if self._config_opener is None:
                return 409, _error('config_ui_unavailable', command='ccb config ui')
            return 200, {'url': self._config_opener(project)}
        if route and route[0] == 'jobs':
            return self._jobs(method, project, route[1:], parsed.query, body)
        # Deliberate allowlist: do not expose pairing/device/host routes.
        allowed_get = route in (['view'], ['terminal-history']) or (
            len(route) == 3 and route[0] == 'agents' and route[2] in ('conversation', 'provider-control', 'provider-quota'))
        allowed_post = route in (['terminals'], ['focus-agent'], ['lifecycle']) or (
            len(route) == 3 and route[0] == 'agents' and route[2] in ('provider-control', 'ui-response'))
        gateway_path = '/v1/' + parsed.path.removeprefix('/api/')
        if parsed.query:
            gateway_path += '?' + parsed.query
        headers = {**self._gateway_headers, 'Host': urlsplit(self.origin or '').netloc}
        if method == 'GET' and allowed_get:
            self._view(project)
            return self.gateway.dispatch_get(gateway_path, headers)
        if method == 'POST' and allowed_post:
            self._view(project)
            status, payload = self.gateway.dispatch_post(gateway_path, body, headers)
            if route == ['terminals'] and 'terminal_id' in payload:
                payload['websocket_url'] = f"{self.origin.replace('http:', 'ws:')}/api/terminals/{payload['terminal_id']}/ws"
            return status, payload
        raise MobileGatewayError('not found', status_code=404)

    def _jobs(self, method: str, project, route: list[str], query: str, body: dict) -> tuple[int, dict]:
        if not route and method == 'GET':
            return 200, self._list_jobs(project, query)
        if not route and method == 'POST':
            if body.get('project_id', project.project_id) != project.project_id:
                raise MobileGatewayError('request project_id does not match route', status_code=400)
            agent, text = body.get('agent'), body.get('body')
            if not isinstance(agent, str) or not isinstance(text, str) or not text.strip():
                raise MobileGatewayError('agent and body are required', status_code=400)
            request = MessageEnvelope(project_id=project.project_id, to_agent=agent, from_actor='user',
                                      body=text, task_id=None, reply_to=None, message_type='ask',
                                      delivery_scope=DeliveryScope.SINGLE)
            def preflight():
                view = self._view(project)
                if not any(isinstance(item, dict) and item.get('name') == agent for item in view.get('agents', [])):
                    raise MobileGatewayError('agent not found', status_code=404)
                if 'namespace_epoch' in body and body['namespace_epoch'] != view.get('namespace', {}).get('epoch'):
                    raise MobileGatewayError('namespace epoch changed', status_code=409)
            def submit():
                receipt = project.client().submit(request)
                if (not isinstance(receipt, dict) or not _JOB_ID.fullmatch(str(receipt.get('job_id') or '')) or
                        receipt.get('agent_name') != agent or receipt.get('status') not in {'accepted', 'queued', 'running'}):
                    raise ValueError('ccbd returned no single job receipt')
                return 202, {**receipt, 'project_id': project.project_id, 'idempotency_key': body['idempotency_key']}
            return self._mutation(f'{project.project_id}/submit', body, submit, preflight=preflight)
        if not route or len(route) > 2:
            raise MobileGatewayError('not found', status_code=404)
        job_id = route[0]
        current = self._job(project, job_id)
        if method == 'GET' and len(route) == 1:
            return 200, current
        if method == 'GET' and route[1:] == ['watch']:
            try:
                cursor = int(parse_qs(query).get('cursor', ['0'])[0])
            except ValueError as exc:
                raise MobileGatewayError('invalid cursor', status_code=400) from exc
            if cursor < 0:
                raise MobileGatewayError('invalid cursor', status_code=400)
            result = project.client().watch(job_id, cursor=cursor)
            if not isinstance(result, dict) or result.get('job_id') != job_id:
                raise MobileGatewayError('watch identity mismatch', status_code=502)
            return 200, result
        if method == 'POST' and route[1:] in (['cancel'], ['retry']):
            action = route[1]
            def mutate():
                latest = self._job(project, job_id)
                state = latest.get('status')
                # Persist only the mutation receipt, never a full job/prompt.
                observed = {'job_id': job_id, 'status': state}
                if action == 'cancel' and state in _TERMINAL:
                    return 409, _error('job_already_terminal', job=observed)
                if action == 'retry' and state not in {'failed', 'incomplete', 'cancelled'}:
                    return 409, _error('job_not_retryable', job=observed)
                try:
                    receipt = getattr(project.client(), action)(job_id)
                except CcbdClientError:
                    # A completion may win after the preflight. Report the
                    # authority's state instead of optimistically cancelling.
                    latest = self._job(project, job_id)
                    if action == 'cancel' and latest.get('status') in _TERMINAL:
                        return 409, _error('job_already_terminal', job={'job_id': job_id, 'status': latest.get('status')})
                    raise
                if (not isinstance(receipt, dict) or not _JOB_ID.fullmatch(str(receipt.get('job_id') or '')) or
                        receipt.get('agent_name') != latest['job'].get('agent_name') or
                        (action == 'cancel' and (receipt.get('job_id') != job_id or receipt.get('status') != 'cancelled')) or
                        (action == 'retry' and (receipt.get('job_id') == job_id or receipt.get('status') not in {'accepted', 'queued', 'running'}))):
                    raise ValueError('invalid ccbd mutation receipt')
                return 202, receipt
            return self._mutation(f'{project.project_id}/{job_id}/{action}', body, mutate)
        raise MobileGatewayError('not found', status_code=404)

    def _diff(self, root: Path) -> dict:
        output = {}
        for key, extra, limit in (('stat', ['--stat'], 32768), ('patch', [], 262144)):
            command = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.pager=cat', '-C', str(root),
                       'diff', '--no-ext-diff', '--no-textconv', '--no-color', *extra]
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  env=git_environment()) as process:
                chunks, size, deadline, truncated = [], 0, time.monotonic() + 5, False
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while selector.get_map():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            process.kill()
                            process.wait()
                            raise MobileGatewayError('git diff timed out', status_code=504)
                        for event, _ in selector.select(min(remaining, 0.1)):
                            chunk = os.read(event.fd, min(65536, limit + 1 - size))
                            if not chunk:
                                selector.unregister(event.fileobj)
                                continue
                            chunks.append(chunk)
                            size += len(chunk)
                            if size > limit:
                                truncated = True
                                process.kill()
                                selector.unregister(event.fileobj)
                code = process.wait(timeout=1)
                if code and not truncated:
                    raise MobileGatewayError('git diff unavailable', status_code=409)
                output[key] = b''.join(chunks)[:limit].decode('utf-8', errors='replace')
                output[f'{key}_truncated'] = truncated
        return {'schema_version': 1, **output, 'scope': 'unstaged_tracked'}


def build_workbench_server(service: WorkbenchService, *, host: str = '127.0.0.1', port: int = 0) -> ThreadingHTTPServer:
    if host != '127.0.0.1':
        raise ValueError('workbench binds only to 127.0.0.1')

    class Handler(BaseHTTPRequestHandler):
        server_version = 'MuxaryWorkbench/1'

        def setup(self):
            super().setup()
            self.connection.settimeout(_HTTP_READ_TIMEOUT)

        def log_message(self, *args):
            pass  # Neither bootstrap credentials nor query strings enter logs.

        def _boundary(self, *, mutation=False, websocket=False):
            if (len(self.headers.get_all('Host', [])) != 1 or
                    self.headers.get('Host') != urlsplit(service.origin).netloc):
                raise MobileGatewayError('host denied', status_code=403)
            origin = self.headers.get('Origin')
            if (len(self.headers.get_all('Origin', [])) > 1 or
                    (origin is not None and origin != service.origin) or
                    ((mutation or websocket) and origin != service.origin)):
                raise MobileGatewayError('origin denied', status_code=403)
            if self.headers.get('Sec-Fetch-Site') in ('cross-site', 'same-site'):
                raise MobileGatewayError('cross-site request denied', status_code=403)

        def _json(self, status, payload, *, cookie=None):
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            if cookie:
                self.send_header('Set-Cookie', cookie)
            self._finish(data)

        def _finish(self, data):
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            ws_origin = service.origin.replace('http:', 'ws:')
            self.send_header('Content-Security-Policy', f"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' {ws_origin}; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            if self.headers.get('Transfer-Encoding'):
                raise MobileGatewayError('transfer encoding denied', status_code=400)
            if self.headers.get_content_type() != 'application/json':
                raise MobileGatewayError('JSON content-type required', status_code=415)
            if len(self.headers.get_all('Content-Length', [])) > 1:
                raise ValueError('multiple content lengths denied')
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError as exc:
                raise ValueError('invalid content length') from exc
            if length < 0 or length > 65536:
                raise ValueError('request body too large')
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError('incomplete request body')
            body = json.loads(raw or b'{}')
            if not isinstance(body, dict):
                raise ValueError('JSON object required')
            return body

        def _handle(self, method):
            try:
                parsed = urlsplit(self.path)
                websocket = is_websocket_upgrade(self.headers)
                self._boundary(mutation=method != 'GET', websocket=websocket)
                if method == 'POST' and parsed.path == '/api/session':
                    token = service.create_session(self._body().get('token'))
                    self._json(200, {'authenticated': True}, cookie=f'{service.session_cookie_name}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200')
                    return
                if parsed.path.startswith('/api/'):
                    if not service.authenticate(self.headers.get('Cookie', '')):
                        raise MobileGatewayError('session required', status_code=401)
                    terminal = re.fullmatch(r'/api/terminals/(term_[a-zA-Z0-9_-]+)/ws', parsed.path)
                    if websocket and terminal and method == 'GET':
                        connection = accept_websocket(self)
                        # Long-lived terminals use the existing gateway's own
                        # lifecycle, not the HTTP header/body inactivity limit.
                        self.connection.settimeout(None)
                        service.gateway.handle_terminal_websocket(terminal[1], connection)
                        return
                    body = self._body() if method == 'POST' else None
                    status, payload = service.dispatch(method, self.path, body)
                    self._json(status, payload)
                    return
                if method != 'GET' or websocket:
                    raise MobileGatewayError('not found', status_code=404)
                relative = unquote(parsed.path).lstrip('/') or 'index.html'
                path = (service.assets_dir / relative).resolve()
                if not path.is_relative_to(service.assets_dir) or not path.is_file():
                    raise MobileGatewayError('not found', status_code=404)
                self.send_response(200)
                self.send_header('Content-Type', mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
                self._finish(path.read_bytes())
            except MobileGatewayError as exc:
                self._json(exc.status_code, _error(str(exc)))
            except TimeoutError:
                self._json(408, _error('request_read_timeout'))
            except (ValueError, UnicodeError) as exc:
                self._json(400, _error(str(exc)))
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception:
                self._json(503, _error('backend_unavailable'))

        def do_GET(self):  # noqa: N802
            self._handle('GET')

        def do_POST(self):  # noqa: N802
            self._handle('POST')

        def do_OPTIONS(self):  # noqa: N802
            self._json(405, _error('method_not_allowed'))

    class Server(ThreadingHTTPServer):
        daemon_threads = True

        def server_close(self):
            service.close()
            super().server_close()

    server = Server((host, port), Handler)
    service.origin = f'http://127.0.0.1:{server.server_address[1]}'
    return server
