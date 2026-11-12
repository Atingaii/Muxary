import 'dart:io';

import 'package:ccb_mobile/cache/mobile_snapshot_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'isolates conversation snapshots by host project agent and epoch',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'ccb-snapshot-test',
      );
      addTearDown(() => directory.delete(recursive: true));
      final file = File('${directory.path}/snapshots.json');
      final store = MobileSnapshotStore(fileFactory: () async => file);
      final namespace = mobileSnapshotNamespace(
        hostId: 'host',
        deviceId: 'device',
      );
      final first = mobileConversationSnapshotKey(
        namespace: namespace,
        projectId: 'project',
        agent: 'lead',
        namespaceEpoch: 7,
      );
      final nextEpoch = mobileConversationSnapshotKey(
        namespace: namespace,
        projectId: 'project',
        agent: 'lead',
        namespaceEpoch: 8,
      );
      final otherAgent = mobileConversationSnapshotKey(
        namespace: namespace,
        projectId: 'project',
        agent: 'worker',
        namespaceEpoch: 7,
      );

      await store.write(first, {
        'conversation': {'agent': 'lead', 'items': []},
      });
      await store.write(nextEpoch, {
        'conversation': {
          'agent': 'lead',
          'items': ['new'],
        },
      });
      await store.write(otherAgent, {
        'conversation': {'agent': 'worker', 'items': []},
      });

      expect((await store.read(first))?['conversation'], {
        'agent': 'lead',
        'items': [],
      });
      expect((await store.read(nextEpoch))?['conversation'], {
        'agent': 'lead',
        'items': ['new'],
      });
      expect((await store.read(otherAgent))?['conversation'], {
        'agent': 'worker',
        'items': [],
      });
    },
  );

  test('enforces a byte budget and degrades from a corrupt file', () async {
    final directory = await Directory.systemTemp.createTemp(
      'ccb-snapshot-test',
    );
    addTearDown(() => directory.delete(recursive: true));
    final file = File('${directory.path}/snapshots.json');
    final store = MobileSnapshotStore(
      fileFactory: () async => file,
      maxEntries: 2,
      maxBytes: 180,
    );

    await store.write('one', {'value': 'a' * 50});
    await store.write('two', {'value': 'b' * 50});
    await store.write('three', {'value': 'c' * 50});

    expect(await file.length(), lessThanOrEqualTo(300));
    expect(await store.read('three'), isNotNull);
    await file.writeAsString('{not json');
    expect(await store.read('three'), isNull);
  });

  test(
    'serializes concurrent writes, marks TTL stale, and clears a profile',
    () async {
      final directory = await Directory.systemTemp.createTemp(
        'ccb-snapshot-test',
      );
      addTearDown(() => directory.delete(recursive: true));
      final file = File('${directory.path}/snapshots.json');
      var now = DateTime.utc(2026, 7, 10, 0, 0);
      final store = MobileSnapshotStore(
        fileFactory: () async => file,
        maxAge: const Duration(minutes: 5),
        clock: () => now,
      );
      const namespace = 'host:device';
      await Future.wait([
        store.write(mobileProjectsSnapshotKey(namespace), {
          'projects': ['one'],
        }),
        store.write(
          mobileProjectViewSnapshotKey(
            namespace: namespace,
            projectId: 'one',
            namespaceEpoch: 7,
          ),
          {
            'view': {'project': 'one'},
          },
        ),
        store.write(
          mobileConversationSnapshotKey(
            namespace: namespace,
            projectId: 'one',
            agent: 'lead',
            namespaceEpoch: 7,
          ),
          {
            'conversation': ['hello'],
          },
        ),
      ]);
      expect(await store.read(mobileProjectsSnapshotKey(namespace)), isNotNull);
      expect(
        await store.readLatestWithPrefix(
          mobileProjectViewSnapshotPrefix(
            namespace: namespace,
            projectId: 'one',
          ),
        ),
        isNotNull,
      );
      now = now.add(const Duration(minutes: 6));
      expect(
        (await store.readRecord(mobileProjectsSnapshotKey(namespace)))?.isStale,
        isTrue,
      );
      await store.clearNamespace(namespace);
      expect(await store.read(mobileProjectsSnapshotKey(namespace)), isNull);
      expect(
        await store.readLatestWithPrefix(
          mobileProjectViewSnapshotPrefix(
            namespace: namespace,
            projectId: 'one',
          ),
        ),
        isNull,
      );
    },
  );
}
