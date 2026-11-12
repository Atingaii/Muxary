import 'package:ccb_mobile/models/ccb_agent_conversation.dart';
import 'package:test/test.dart';

void main() {
  group('CcbAgentMessageSubmitResult', () {
    test('uses submit created_at as returned message sent time', () {
      final result = CcbAgentMessageSubmitResult.fromJson({
        'message_submit': {
          'accepted': true,
          'idempotency_key': 'local-lead-0',
          'message_id': 'local-lead-0',
          'state': 'sent',
          'created_at': '2026-07-01T03:42:00Z',
          'message': {
            'id': 'local-lead-0',
            'agent': 'lead',
            'kind': 'user_message',
            'title': 'You',
            'body': 'hello',
            'format': 'markdown',
            'state': 'sent',
            'source': 'mobile',
          },
        },
      });

      expect(result.message?.sentAt, DateTime.utc(2026, 7, 1, 3, 42));
    });
  });
}
