from __future__ import annotations

import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

from mobile_gateway.fcm import (
    FcmHttpV1PushSender,
    FcmSenderConfig,
    _GoogleAuthAccessTokenProvider,
    build_fcm_sender_from_env,
)


class _TokenProvider:
    def __init__(self, token: str = 'access-token') -> None:
        self.token = token
        self.calls = 0

    def access_token(self, *, timeout: float) -> str:
        self.calls += 1
        return self.token


class _Response:
    status = 200

    def __enter__(self) -> '_Response':
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"name":"projects/demo/messages/1"}'


def _payload() -> dict[str, object]:
    return {
        'id': 'mnotif_000000000001',
        'kind': 'task_completed',
        'project_id': 'proj-demo',
        'project_short_name': 'demo',
        'agent': 'worker',
        'completed_at': '2026-07-14T01:02:03Z',
        'dedupe_key': 'proj-demo:7:worker:1',
        'host_id': 'host-demo',
        'device_id': 'device-demo',
    }


def test_fcm_sender_posts_notification_and_whitelisted_string_data() -> None:
    requests: list[tuple[str, dict[str, str], dict[str, object], float]] = []

    def opener(request, *, timeout: float):
        requests.append(
            (
                request.full_url,
                dict(request.header_items()),
                json.loads(request.data.decode('utf-8')),
                timeout,
            )
        )
        return _Response()

    sender = FcmHttpV1PushSender(
        FcmSenderConfig(project_id='firebase-project', max_retries=0),
        access_token_provider=_TokenProvider(),
        opener=opener,
    )

    result = sender('fcm-device-token', _payload(), 1.5)

    assert result.sent is True
    assert result.invalid_token is False
    url, headers, body, timeout = requests[0]
    assert url == 'https://fcm.googleapis.com/v1/projects/firebase-project/messages:send'
    assert headers['Authorization'] == 'Bearer access-token'
    assert timeout == 1.5
    message = body['message']
    assert message['token'] == 'fcm-device-token'
    assert message['notification'] == {
        'title': 'CCB Mobile',
        'body': 'demo / worker 任务完成',
    }
    assert message['android']['notification']['channel_id'] == 'ccb_task_completion'
    assert set(message['data']) == set(_payload())
    assert message['data'] == {key: str(value) for key, value in _payload().items()}
    assert 'proj-demo:7:worker:1' not in json.dumps(message['notification'])


def test_fcm_sender_retries_transient_http_errors_then_succeeds() -> None:
    attempts = 0

    def opener(_request, *, timeout: float):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise HTTPError(
                url='https://fcm.googleapis.com',
                code=503,
                msg='UNAVAILABLE',
                hdrs={},
                fp=io.BytesIO(b'{"error":{"status":"UNAVAILABLE"}}'),
            )
        return _Response()

    sender = FcmHttpV1PushSender(
        FcmSenderConfig(project_id='firebase-project', max_retries=1),
        access_token_provider=_TokenProvider(),
        opener=opener,
        sleep=lambda _seconds: None,
    )

    assert sender('token', _payload(), 2.0).sent is True
    assert attempts == 2


def test_fcm_sender_classifies_unregistered_token_without_retry() -> None:
    attempts = 0

    def opener(_request, *, timeout: float):
        nonlocal attempts
        attempts += 1
        raise HTTPError(
            url='https://fcm.googleapis.com',
            code=404,
            msg='NOT_FOUND',
            hdrs={},
            fp=io.BytesIO(
                json.dumps(
                    {
                        'error': {
                            'status': 'NOT_FOUND',
                            'details': [
                                {
                                    '@type': 'type.googleapis.com/google.firebase.fcm.v1.FcmError',
                                    'errorCode': 'UNREGISTERED',
                                }
                            ],
                        }
                    }
                ).encode('utf-8')
            ),
        )

    sender = FcmHttpV1PushSender(
        FcmSenderConfig(project_id='firebase-project', max_retries=2),
        access_token_provider=_TokenProvider(),
        opener=opener,
        sleep=lambda _seconds: None,
    )

    result = sender('token', _payload(), 2.0)

    assert result.sent is False
    assert result.invalid_token is True
    assert result.error_code == 'UNREGISTERED'
    assert attempts == 1


def test_fcm_sender_rejects_non_whitelisted_payload_before_http() -> None:
    calls = 0

    def opener(_request, *, timeout: float):
        nonlocal calls
        calls += 1
        return _Response()

    sender = FcmHttpV1PushSender(
        FcmSenderConfig(project_id='firebase-project'),
        access_token_provider=_TokenProvider(),
        opener=opener,
    )
    payload = {**_payload(), 'body': 'secret reply'}

    result = sender('token', payload, 2.0)

    assert result.sent is False
    assert result.error_code == 'invalid_payload'
    assert calls == 0


def test_build_fcm_sender_from_env_is_fail_closed_and_redacted(tmp_path: Path) -> None:
    sender, diagnostic = build_fcm_sender_from_env({})
    assert sender is None
    assert diagnostic == {'configured': False, 'provider': 'fcm_http_v1'}

    missing = tmp_path / 'missing-service-account.json'
    sender, diagnostic = build_fcm_sender_from_env(
        {
            'CCB_MOBILE_FCM_PROJECT_ID': 'firebase-project',
            'CCB_MOBILE_FCM_CREDENTIALS_FILE': str(missing),
        }
    )

    assert sender is None
    assert diagnostic['configured'] is True
    assert diagnostic['ready'] is False
    assert diagnostic['credential_source'] == 'service_account_file'
    assert str(missing) not in json.dumps(diagnostic)


def test_fcm_sender_reports_transport_error_after_retry_budget() -> None:
    sender = FcmHttpV1PushSender(
        FcmSenderConfig(project_id='firebase-project', max_retries=1),
        access_token_provider=_TokenProvider(),
        opener=lambda _request, *, timeout: (_ for _ in ()).throw(
            URLError('temporary failure')
        ),
        sleep=lambda _seconds: None,
    )

    result = sender('token', _payload(), 2.0)

    assert result.sent is False
    assert result.retryable is True
    assert result.error_code == 'transport_error'


def test_google_auth_provider_reuses_valid_access_token() -> None:
    class Credentials:
        token = 'cached-access-token'
        valid = True
        refresh_calls = 0

        def refresh(self, _request) -> None:
            self.refresh_calls += 1

    credentials = Credentials()
    def unexpected_request_factory() -> object:
        raise AssertionError('valid cached token must not load the optional Google transport')

    provider = _GoogleAuthAccessTokenProvider(
        credentials,
        request_factory=unexpected_request_factory,
    )

    assert provider.access_token(timeout=1.0) == 'cached-access-token'
    assert provider.access_token(timeout=1.0) == 'cached-access-token'
    assert credentials.refresh_calls == 0


def test_google_auth_provider_refresh_uses_bounded_transport() -> None:
    transport_calls: list[dict[str, object]] = []

    def transport(*_args: object, **kwargs: object) -> object:
        transport_calls.append(dict(kwargs))
        return object()

    class Credentials:
        token = None
        valid = False

        def refresh(self, request) -> None:
            request(url='https://oauth.example.test/token', method='POST')
            self.token = 'fresh-access-token'
            self.valid = True

    provider = _GoogleAuthAccessTokenProvider(
        Credentials(),
        request_factory=lambda: transport,
    )

    assert provider.access_token(timeout=1.25) == 'fresh-access-token'
    assert transport_calls == [
        {
            'url': 'https://oauth.example.test/token',
            'method': 'POST',
            'timeout': 1.25,
        }
    ]
