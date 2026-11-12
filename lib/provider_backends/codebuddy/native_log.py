"""Read an explicitly bound CodeBuddy transcript, never terminal prompt echoes.

CodeBuddy 2.x persists Responses-style message items, not Claude's nested
``message`` records. Tool results and reasoning are deliberately not replies.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import time


_SESSION_ID_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_:-]*\Z')
_ERROR_CODE_RE = re.compile(r'[A-Za-z0-9_.:-]{1,120}\Z')


def default_sessions_root() -> Path:
    config = (os.environ.get('CODEBUDDY_CONFIG_DIR') or '').strip()
    home = Path(config).expanduser() if config else Path.home() / '.codebuddy'
    return home / 'projects'


def codebuddy_project_dir(work_dir: Path, *, root: Path | None = None) -> Path:
    """Match CodeBuddy's canonicalizeStorePath/compressWorkspacePathName."""
    normalized = re.sub(r'[/\\:]', '-', str(Path(work_dir).expanduser().resolve(strict=False)))
    normalized = re.sub(r'-+', '-', normalized).strip('-')
    encoded = normalized.encode('utf-8')
    if len(encoded) > 255:
        hashed = 5381
        for byte in encoded:
            hashed = ((33 * hashed) ^ byte) & 0xFFFFFFFF
        suffix = ''
        while hashed:
            suffix = '0123456789abcdefghijklmnopqrstuvwxyz'[hashed % 36] + suffix
            hashed //= 36
        prefix = encoded[:180].decode('utf-8', errors='ignore')
        normalized = f'{prefix}-{suffix or "0"}'
    return (Path(root).expanduser() if root is not None else default_sessions_root()) / normalized


class CodebuddyNativeLogReader:
    """Read one pinned, append-only native transcript (including before birth).

    A changed inode or an observed size below the cursor signals a reset. A
    same-inode rewrite that regrows past the cursor between polls is outside
    this trusted-writer contract; the reader does not hash historical bytes.
    """

    def __init__(
        self,
        root: Path | None = None,
        work_dir: Path | None = None,
        session_path: Path | None = None,
    ):
        self.root = Path(root).expanduser() if root is not None else default_sessions_root()
        self.work_dir = Path(work_dir) if work_dir is not None else Path.cwd()
        self._preferred_session = Path(session_path).expanduser() if session_path is not None else None
        self._session_id_hint: str | None = None
        try:
            poll = float(os.environ.get('CODEBUDDY_POLL_INTERVAL', '0.05'))
        except ValueError:
            poll = 0.05
        self._poll_interval = min(0.5, max(0.02, poll))

    def set_preferred_session(self, session_path: Path | None) -> None:
        self._preferred_session = Path(session_path).expanduser() if session_path is not None else None

    def set_session_id_hint(self, session_id: str | None) -> None:
        if session_id is not None and not _SESSION_ID_RE.fullmatch(session_id):
            raise ValueError('Invalid CodeBuddy session ID')
        self._session_id_hint = session_id

    def current_session_path(self) -> Path | None:
        if self._preferred_session is not None:
            return self._preferred_session
        if self._session_id_hint:
            return codebuddy_project_dir(self.work_dir, root=self.root) / f'{self._session_id_hint}.jsonl'
        return None

    def capture_state(self) -> dict:
        path = self.current_session_path()
        state: dict = {'session_path': path, 'offset': 0}
        if path is not None:
            try:
                # Open, rather than merely stat, before sending a request: an
                # existing but unreadable transcript cannot supply evidence.
                with path.open('rb') as handle:
                    stat = os.fstat(handle.fileno())
            except FileNotFoundError:
                pass
            else:
                state.update(offset=stat.st_size, file_identity=[stat.st_dev, stat.st_ino])
        return state

    def try_get_events(self, state: dict) -> tuple[list[tuple[str, str]], dict]:
        path = self.current_session_path()
        next_state = dict(state or {})
        if path is None:
            return [], next_state
        previous_path = next_state.get('session_path')
        if previous_path is not None and Path(previous_path) != path:
            next_state = {'reset_reason': 'session_changed'}
        else:
            next_state.pop('reset_reason', None)
        next_state['session_path'] = path
        try:
            with path.open('rb') as handle:
                stat = os.fstat(handle.fileno())
                identity = [stat.st_dev, stat.st_ino]
                offset = int(next_state.get('offset') or 0)
                previous_identity = next_state.get('file_identity')
                if offset > stat.st_size or (previous_identity is not None and list(previous_identity) != identity):
                    next_state['reset_reason'] = 'truncated' if offset > stat.st_size else 'replaced'
                    offset = 0
                    next_state.pop('generation_id', None)
                handle.seek(offset)
                payload = handle.read()
        except FileNotFoundError:
            # A SessionStart binding can precede the first transcript write.
            # Once observed, disappearance is a failure, not a new birth.
            if next_state.get('file_identity') is not None:
                raise
            return [], next_state
        # Do not consume a partial record or a split UTF-8 code point. It will
        # be reread on the next poll after the writer appends its newline.
        boundary = payload.rfind(b'\n') + 1
        next_state.update(offset=offset + boundary, file_identity=identity)
        events: list[tuple[str, str]] = []
        for raw in payload[:boundary].splitlines():
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                # Skipping a corrupted user/error record could authorize a
                # later assistant from a different turn. Partial last lines
                # are retried above; complete damaged lines are not recoverable.
                raise ValueError('Invalid complete CodeBuddy transcript record') from exc
            if not isinstance(entry, dict):
                raise ValueError('CodeBuddy transcript record must be an object')
            event = _message_event(entry, next_state)
            if event is not None:
                events.append(event)
        return events, next_state

    def wait_for_events(self, state: dict, timeout: float) -> tuple[list[tuple[str, str]], dict]:
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            events, state = self.try_get_events(state)
            if events or time.monotonic() >= deadline:
                return events, state
            time.sleep(min(self._poll_interval, max(0.0, deadline - time.monotonic())))

    def try_get_message(self, state: dict) -> tuple[str | None, dict]:
        events, state = self.try_get_events(state)
        replies = [text for role, text in events if role == 'assistant']
        return (replies[-1] if replies else None), state

    def wait_for_message(self, state: dict, timeout: float) -> tuple[str | None, dict]:
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            message, state = self.try_get_message(state)
            if message is not None or time.monotonic() >= deadline:
                return message, state
            time.sleep(min(self._poll_interval, max(0.0, deadline - time.monotonic())))

    def latest_message(self) -> str | None:
        events, _ = self.try_get_events({'offset': 0})
        replies = [text for role, text in events if role == 'assistant']
        return replies[-1] if replies else None

    def latest_conversations(self, n: int = 1) -> list[tuple[str, str]]:
        events, _ = self.try_get_events({'offset': 0})
        pairs: list[tuple[str, str]] = []
        user = ''
        replies: list[str] = []
        for role, text in events:
            if role == 'user':
                if replies:
                    pairs.append((user, '\n'.join(replies)))
                user, replies = text, []
            elif role == 'assistant':
                replies.append(text)
        if replies:
            pairs.append((user, '\n'.join(replies)))
        return pairs[-max(1, int(n)):]


def _message_event(entry: object, state: dict) -> tuple[str, str] | None:
    if not isinstance(entry, dict) or entry.get('type') != 'message':
        return None
    role = entry.get('role')
    if not isinstance(role, str):
        raise ValueError('CodeBuddy message role must be a string')
    if role not in {'user', 'assistant'}:
        return None
    provider_data = entry.get('providerData')
    if provider_data is not None and not isinstance(provider_data, dict):
        raise ValueError('Invalid CodeBuddy message providerData')
    provider_data = provider_data if isinstance(provider_data, dict) else {}
    generation = provider_data.get('conversationRequestId')
    if role == 'user':
        if not isinstance(generation, str) or not generation.strip():
            raise ValueError('CodeBuddy user is missing its conversation request ID')
        state['generation_id'] = generation
    elif state.get('generation_id'):
        if not isinstance(generation, str) or not generation:
            raise ValueError('CodeBuddy assistant is missing its conversation request ID')
        if generation != state['generation_id']:
            return None
    if role == 'assistant':
        if entry.get('status') == 'incomplete' and provider_data.get('error'):
            error = provider_data['error']
            code = error.get('code') if isinstance(error, dict) else None
            # Provider error messages can embed raw requests or credentials.
            # Surface only a bounded identifier, never its raw text/content.
            suffix = f' (code={code})' if isinstance(code, str) and _ERROR_CODE_RE.fullmatch(code) else ''
            return 'error', f'CodeBuddy request failed{suffix}'
        if entry.get('status') != 'completed':
            return None
    content = entry.get('content')
    if not isinstance(content, list):
        raise ValueError('CodeBuddy message content must be an array')
    expected_type = 'input_text' if role == 'user' else 'output_text'
    for block in content:
        if not isinstance(block, dict):
            raise ValueError('CodeBuddy message content block must be an object')
        if block.get('type') == expected_type and not isinstance(block.get('text'), str):
            raise ValueError('CodeBuddy message text must be a string')
    parts = [
        block['text'] for block in content
        if isinstance(block, dict) and block.get('type') == expected_type and isinstance(block.get('text'), str)
    ]
    text = '\n'.join(parts)
    # Even an image-only/empty user message starts a different turn; never let
    # it disappear between an observed request anchor and an assistant marker.
    return (role, text) if role == 'user' or text.strip() else None


__all__ = ['CodebuddyNativeLogReader', 'codebuddy_project_dir', 'default_sessions_root']
