import 'package:ccb_mobile/features/agent_chat/agent_chat_state_helpers.dart';
import 'package:ccb_mobile/features/agent_chat/pane_chat_controller.dart';
import 'package:ccb_mobile/models/ccb_agent_conversation.dart';
import 'package:ccb_mobile/models/ccb_conversation_item.dart';
import 'package:ccb_mobile/transport/http_gateway_transport.dart';
import 'package:test/test.dart';

void main() {
  group('agent chat state helpers', () {
    test('maps pane partial-input failures to unconfirmed delivery', () {
      const partial = PaneChatSendException(
        stage: PaneChatSendFailureStage.enter,
        cause: 'enter failed',
        inputMayHaveReachedPane: true,
      );

      expect(paneInputMayHaveReachedPane(partial), isTrue);
      expect(
        paneFailureDeliveryState(partial),
        CcbConversationDeliveryState.unconfirmed,
      );
      expect(
        paneFailureDeliveryState(Exception('open failed')),
        CcbConversationDeliveryState.failed,
      );
    });

    test('detects stale namespace epoch gateway errors', () {
      final stale = GatewayHttpException(
        Uri.parse('http://gateway.local/v1/projects/proj/agents/lead/messages'),
        409,
        '{"error":"stale namespace epoch"}',
      );
      final wrongStatus = GatewayHttpException(
        Uri.parse('http://gateway.local/v1/projects/proj/agents/lead/messages'),
        400,
        '{"error":"stale namespace epoch"}',
      );

      expect(isStaleNamespaceEpochError(stale), isTrue);
      expect(isStaleNamespaceEpochError(wrongStatus), isFalse);
      expect(
        isStaleNamespaceEpochError(Exception('stale namespace epoch')),
        isTrue,
      );
    });

    test('conversation signature changes when visible item fields change', () {
      final initial = _conversation([
        _user(
          id: 'u1',
          body: 'hello',
          state: CcbConversationDeliveryState.sent,
        ),
      ]);
      final same = _conversation([
        _user(
          id: 'u1',
          body: 'hello',
          state: CcbConversationDeliveryState.sent,
        ),
      ]);
      final changedBody = _conversation([
        _user(
          id: 'u1',
          body: 'hello again',
          state: CcbConversationDeliveryState.sent,
        ),
      ]);
      final changedState = _conversation([
        _user(
          id: 'u1',
          body: 'hello',
          state: CcbConversationDeliveryState.pending,
        ),
      ]);

      expect(conversationSignature(initial), conversationSignature(same));
      expect(
        conversationSignature(initial),
        isNot(conversationSignature(changedBody)),
      );
      expect(
        conversationSignature(initial),
        isNot(conversationSignature(changedState)),
      );
    });

    test('prunes local messages covered by remote user-message counts', () {
      final localItems = [
        _user(id: 'local-1', body: 'same'),
        _user(
          id: 'local-2',
          body: ' same ',
          state: CcbConversationDeliveryState.sent,
        ),
        _user(
          id: 'local-failed',
          body: 'same',
          state: CcbConversationDeliveryState.failed,
        ),
        _user(id: 'local-other', body: 'other'),
      ];
      final remote = _conversation([
        _user(
          id: 'remote-1',
          body: 'same',
          state: CcbConversationDeliveryState.sent,
        ),
        _agentReply(id: 'remote-reply', body: 'same'),
      ]);

      final next = pruneLocalMessagesCoveredByRemote(
        localItems: localItems,
        remoteConversation: remote,
      );

      expect(next.map((item) => item.id), [
        'local-2',
        'local-failed',
        'local-other',
      ]);
    });

    test(
      'prunes duplicate local bodies only as many times as remote covers',
      () {
        final localItems = [
          _user(id: 'local-1', body: 'duplicate'),
          _user(id: 'local-2', body: 'duplicate'),
          _user(id: 'local-3', body: 'duplicate'),
        ];
        final remote = _conversation([
          _user(
            id: 'remote-1',
            body: 'duplicate',
            state: CcbConversationDeliveryState.sent,
          ),
          _user(
            id: 'remote-2',
            body: 'duplicate',
            state: CcbConversationDeliveryState.sent,
          ),
        ]);

        final next = pruneLocalMessagesCoveredByRemote(
          localItems: localItems,
          remoteConversation: remote,
        );

        expect(next.map((item) => item.id), ['local-3']);
      },
    );

    test(
      'prunes duplicate local attachments only as many times as remote covers',
      () {
        final local1 = CcbConversationItem.userMessage(
          id: 'local-1',
          agentName: 'lead',
          body: '',
          attachments: const [
            CcbMessageAttachment(
              fileId: 'draft-1',
              fileName: 'notes.txt',
              mimeType: 'text/plain',
              sizeBytes: 12,
            ),
          ],
        );
        final local2 = CcbConversationItem.userMessage(
          id: 'local-2',
          agentName: 'lead',
          body: '',
          attachments: const [
            CcbMessageAttachment(
              fileId: 'draft-2',
              fileName: 'notes.txt',
              mimeType: 'text/plain',
              sizeBytes: 12,
            ),
          ],
        );
        final remote = _conversation([
          CcbConversationItem.userMessage(
            id: 'remote-1',
            agentName: 'lead',
            body: '',
            attachments: const [
              CcbMessageAttachment(
                fileId: 'file-1',
                fileName: 'notes.txt',
                mimeType: 'text/plain',
                sizeBytes: 12,
              ),
            ],
            state: CcbConversationDeliveryState.sent,
          ),
        ]);

        final next = pruneLocalMessagesCoveredByRemote(
          localItems: [local1, local2],
          remoteConversation: remote,
        );

        expect(next.map((item) => item.id), ['local-2']);
      },
    );

    test(
      'prunes attachment-only local messages only as many times as remote covers',
      () {
        final localItems = [
          _attachmentUser(id: 'local-1', fileName: 'notes.txt'),
          _attachmentUser(id: 'local-2', fileName: 'notes.txt'),
          _attachmentUser(id: 'local-other', fileName: 'other.txt'),
        ];
        final remote = _conversation([
          _attachmentUser(id: 'remote-1', fileName: 'notes.txt'),
        ]);

        final next = pruneLocalMessagesCoveredByRemote(
          localItems: localItems,
          remoteConversation: remote,
        );

        expect(next.map((item) => item.id), ['local-2', 'local-other']);
      },
    );

    test('prunes local attachment message covered by pane attachment echo', () {
      final local = CcbConversationItem.userMessage(
        id: 'local-image',
        agentName: 'lead',
        body: 'please inspect',
        attachments: const [
          CcbMessageAttachment(
            fileId: 'mobile-file-1',
            fileName: 'photo.png',
            mimeType: 'image/png',
            sizeBytes: 68,
          ),
        ],
      );
      final remote = _conversation([
        _user(
          id: 'remote-image-echo',
          body:
              'please inspect\n'
              'Attached files:\n'
              '- photo.png (image/png, 68 bytes, file id: mobile-file-1)',
          state: CcbConversationDeliveryState.sent,
        ),
      ]);

      final next = pruneLocalMessagesCoveredByRemote(
        localItems: [local],
        remoteConversation: remote,
      );

      expect(next, isEmpty);
      expect(
        remoteConversationCoversUserMessage(
          remoteConversation: remote,
          message: local,
        ),
        isTrue,
      );
    });

    test(
      'prunes attachment-only local message covered by markdown pane echo',
      () {
        final local = CcbConversationItem.userMessage(
          id: 'local-image',
          agentName: 'mobile_probe',
          body: '',
          attachments: const [
            CcbMessageAttachment(
              fileId: 'mobile-file-1',
              fileName: 'ccb-upload-smoke.png',
              mimeType: 'image/png',
              sizeBytes: 228266,
              kind: CcbMessageAttachmentKind.image,
              state: CcbMessageAttachmentState.available,
            ),
          ],
          state: CcbConversationDeliveryState.sent,
        );
        final remoteItem = _user(
          id: 'remote-image-echo',
          body:
              'Attached files:\n'
              '- [ccb-upload-smoke.png]('
              '.ccb/mobile/uploads/mobile_probe/'
              'mobile-file-1-ccb-upload-smoke.png) '
              '(image/png, 228266 bytes, file id: mobile-file-1)',
          state: CcbConversationDeliveryState.sent,
        );
        final remote = _conversation([remoteItem]);

        expect(
          pruneLocalMessagesCoveredByRemote(
            localItems: [local],
            remoteConversation: remote,
          ),
          isEmpty,
        );
        final normalized = normalizePaneAttachmentEcho(remoteItem);
        expect(normalized.body, isEmpty);
        expect(normalized.attachments, hasLength(1));
        expect(normalized.attachments.single.fileName, 'ccb-upload-smoke.png');
        expect(
          normalized.attachments.single.projectRelativePath,
          '.ccb/mobile/uploads/mobile_probe/'
          'mobile-file-1-ccb-upload-smoke.png',
        );
      },
    );

    test('detects jpg pane attachment echo from uploaded mobile file', () {
      final local = CcbConversationItem.userMessage(
        id: 'local-image',
        agentName: 'lead',
        body: 'please inspect this image',
        attachments: const [
          CcbMessageAttachment(
            fileId: 'uploaded-image-1',
            fileName: 'camera-roll-image.jpg',
            mimeType: 'image/jpeg',
            sizeBytes: 4,
            kind: CcbMessageAttachmentKind.image,
            state: CcbMessageAttachmentState.available,
          ),
        ],
        state: CcbConversationDeliveryState.sent,
      );
      final remote = _user(
        id: 'remote-image-echo',
        body:
            'please inspect this image\n'
            'Attached files:\n'
            '- camera-roll-image.jpg (image/jpeg, 4 bytes, '
            'file id: uploaded-image-1)',
        state: CcbConversationDeliveryState.sent,
      );

      expect(
        remoteUserMessageIsPaneAttachmentEcho(remote: remote, local: local),
        isTrue,
      );
      expect(
        remoteUserMessageCoversLocalMessage(remote: remote, local: local),
        isTrue,
      );
    });

    test('normalizes pane attachment echo into structured attachment', () {
      final normalized = normalizePaneAttachmentEcho(
        _user(
          id: 'remote-image-echo',
          body:
              'please inspect this image\n'
              'Attached files:\n'
              '- camera-roll-image.jpg (image/jpeg, 4 bytes, '
              'file id: uploaded-image-1)',
          state: CcbConversationDeliveryState.sent,
        ),
      );

      expect(normalized.body, 'please inspect this image');
      expect(normalized.attachments, hasLength(1));
      expect(normalized.attachments.single.fileId, 'uploaded-image-1');
      expect(normalized.attachments.single.fileName, 'camera-roll-image.jpg');
      expect(
        normalized.attachments.single.effectiveKind,
        CcbMessageAttachmentKind.image,
      );
    });

    test('detects remote coverage for attachment-only user messages', () {
      final local = CcbConversationItem.userMessage(
        id: 'local-1',
        agentName: 'lead',
        body: '',
        attachments: const [
          CcbMessageAttachment(
            fileId: 'draft-1',
            fileName: 'notes.txt',
            mimeType: 'text/plain',
            sizeBytes: 12,
          ),
        ],
      );
      final remote = _conversation([
        CcbConversationItem.userMessage(
          id: 'remote-1',
          agentName: 'lead',
          body: '',
          attachments: const [
            CcbMessageAttachment(
              fileId: 'file-1',
              fileName: 'notes.txt',
              mimeType: 'text/plain',
              sizeBytes: 12,
            ),
          ],
          state: CcbConversationDeliveryState.sent,
        ),
      ]);

      expect(
        remoteConversationCoversUserMessage(
          remoteConversation: remote,
          message: local,
        ),
        isTrue,
      );
    });
  });
}

CcbAgentConversation _conversation(List<CcbConversationItem> items) {
  return CcbAgentConversation(
    projectId: 'proj',
    agentName: 'lead',
    namespaceEpoch: 7,
    items: items,
    generatedAt: DateTime.utc(2026, 6, 22),
  );
}

CcbConversationItem _attachmentUser({
  required String id,
  required String fileName,
}) {
  return CcbConversationItem.userMessage(
    id: id,
    agentName: 'lead',
    body: '',
    attachments: [
      CcbMessageAttachment(
        fileId: id,
        fileName: fileName,
        mimeType: 'text/plain',
        sizeBytes: 12,
      ),
    ],
    state: CcbConversationDeliveryState.sent,
  );
}

CcbConversationItem _user({
  required String id,
  required String body,
  CcbConversationDeliveryState state = CcbConversationDeliveryState.pending,
}) {
  return CcbConversationItem.userMessage(
    id: id,
    agentName: 'lead',
    body: body,
    state: state,
  );
}

CcbConversationItem _agentReply({required String id, required String body}) {
  return CcbConversationItem(
    id: id,
    agentName: 'lead',
    kind: CcbConversationItemKind.agentReply,
    title: 'Agent reply',
    body: body,
  );
}
