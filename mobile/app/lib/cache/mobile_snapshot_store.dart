import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// A cached payload is always visibly distinguishable from live gateway data.
class MobileSnapshotRead {
  const MobileSnapshotRead({
    required this.payload,
    required this.capturedAt,
    required this.isStale,
  });

  final Map<String, Object?> payload;
  final DateTime capturedAt;
  final bool isStale;
}

/// Bounded app-private startup snapshots. Device tokens never enter this file:
/// callers pass only a stable host/device namespace. Every operation is
/// serialized so concurrent project and conversation writes cannot lose data.
class MobileSnapshotStore {
  MobileSnapshotStore({
    Future<File> Function()? fileFactory,
    this.maxEntries = 48,
    this.maxBytes = 2 * 1024 * 1024,
    this.maxAge = const Duration(minutes: 15),
    DateTime Function()? clock,
  }) : _fileFactory = fileFactory ?? _defaultFile,
       _clock = clock ?? DateTime.now;

  static const schemaVersion = 1;

  final Future<File> Function() _fileFactory;
  final DateTime Function() _clock;
  final int maxEntries;
  final int maxBytes;
  final Duration maxAge;
  Future<void> _tail = Future<void>.value();

  static Future<File> _defaultFile() async {
    final directory = await getApplicationDocumentsDirectory();
    return File(p.join(directory.path, 'mobile_readonly_snapshots.json'));
  }

  Future<Map<String, Object?>?> read(String key) async =>
      (await readRecord(key))?.payload;

  Future<Map<String, Object?>?> readLatestWithPrefix(String prefix) async =>
      (await readLatestRecordWithPrefix(prefix))?.payload;

  Future<MobileSnapshotRead?> readRecord(String key) {
    return _serialize(() async => _recordFor(_entries(await _readData())[key]));
  }

  Future<MobileSnapshotRead?> readLatestRecordWithPrefix(String prefix) {
    return _serialize(() async {
      final entries = _entries(await _readData());
      MapEntry<String, Object?>? latest;
      for (final entry in entries.entries) {
        if (!entry.key.startsWith(prefix) || entry.value is! Map) {
          continue;
        }
        if (latest == null ||
            _capturedAt(entry.value).isAfter(_capturedAt(latest.value))) {
          latest = entry;
        }
      }
      return _recordFor(latest?.value);
    });
  }

  Future<void> write(String key, Map<String, Object?> payload) {
    return _serialize(() async {
      final normalized = key.trim();
      if (normalized.isEmpty) {
        return;
      }
      final data = await _readData();
      final entries = _entries(data);
      final captured = _clock().toUtc().toIso8601String();
      entries[normalized] = {
        'captured_at': captured,
        // Keep the old name for forward compatibility with cache inspectors.
        'updated_at': captured,
        'payload': payload,
      };
      data
        ..['schema_version'] = schemaVersion
        ..['entries'] = _boundedEntries(entries);
      await _writeData(data);
    });
  }

  Future<void> clearPrefix(String prefix) {
    return _serialize(() async {
      final data = await _readData();
      final entries = _entries(data);
      entries.removeWhere((key, _) => key.startsWith(prefix));
      data
        ..['schema_version'] = schemaVersion
        ..['entries'] = entries;
      await _writeData(data);
    });
  }

  Future<void> clearNamespace(String namespace) async {
    // Queue as one operation; calling three public methods concurrently would
    // be correct but needlessly permits a reader between individual clears.
    await _serialize(() async {
      final data = await _readData();
      final entries = _entries(data);
      entries.removeWhere(
        (key, _) =>
            key == 'projects:$namespace' ||
            key.startsWith('view:$namespace:') ||
            key.startsWith('conversation:$namespace:'),
      );
      data
        ..['schema_version'] = schemaVersion
        ..['entries'] = entries;
      await _writeData(data);
    });
  }

  Future<T> _serialize<T>(Future<T> Function() action) {
    final next = _tail.then<T>((_) => action());
    _tail = next.then<void>(
      (_) {},
      onError: (Object error, StackTrace stackTrace) {},
    );
    return next;
  }

  MobileSnapshotRead? _recordFor(Object? raw) {
    if (raw is! Map || raw['payload'] is! Map) {
      return null;
    }
    final capturedAt = _capturedAt(raw);
    if (capturedAt.millisecondsSinceEpoch == 0) {
      return null;
    }
    final payload = raw['payload'] as Map;
    return MobileSnapshotRead(
      payload: {
        for (final item in payload.entries) item.key.toString(): item.value,
      },
      capturedAt: capturedAt,
      isStale: _clock().toUtc().difference(capturedAt) > maxAge,
    );
  }

  Future<Map<String, Object?>> _readData() async {
    final file = await _fileFactory();
    try {
      if (!await file.exists()) {
        return _emptyData();
      }
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is Map && decoded['schema_version'] == schemaVersion) {
        return {
          for (final item in decoded.entries) item.key.toString(): item.value,
        };
      }
    } catch (_) {
      // Corrupt/interrupted local data is ignored; live gateway recovery wins.
    }
    return _emptyData();
  }

  Future<void> _writeData(Map<String, Object?> data) async {
    final file = await _fileFactory();
    final temp = File('${file.path}.tmp');
    try {
      await file.parent.create(recursive: true);
      await temp.writeAsString(jsonEncode(data));
      await temp.rename(file.path);
    } catch (_) {
      try {
        if (await temp.exists()) {
          await temp.delete();
        }
      } catch (_) {}
    }
  }

  Map<String, Object?> _boundedEntries(Map<String, Object?> entries) {
    final ordered =
        entries.entries.where((entry) => entry.value is Map).toList()..sort(
          (a, b) => _capturedAt(a.value).compareTo(_capturedAt(b.value)),
        );
    final result = <String, Object?>{};
    var usedBytes = 0;
    for (final entry in ordered.reversed) {
      final byteCount =
          utf8.encode(jsonEncode({entry.key: entry.value})).length;
      if (result.length >= maxEntries || usedBytes + byteCount > maxBytes) {
        continue;
      }
      result[entry.key] = entry.value;
      usedBytes += byteCount;
    }
    return result;
  }

  static Map<String, Object?> _emptyData() => {
    'schema_version': schemaVersion,
    'entries': <String, Object?>{},
  };

  static Map<String, Object?> _entries(Map<String, Object?> data) {
    final raw = data['entries'];
    return raw is Map
        ? {for (final item in raw.entries) item.key.toString(): item.value}
        : <String, Object?>{};
  }

  static DateTime _capturedAt(Object? value) {
    if (value is Map) {
      return DateTime.tryParse(
            (value['captured_at'] ?? value['updated_at'] ?? '').toString(),
          )?.toUtc() ??
          DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
    }
    return DateTime.fromMillisecondsSinceEpoch(0, isUtc: true);
  }
}

String mobileSnapshotNamespace({
  required String hostId,
  required String deviceId,
}) => '${Uri.encodeComponent(hostId)}:${Uri.encodeComponent(deviceId)}';

String mobileProjectsSnapshotKey(String namespace) => 'projects:$namespace';

String mobileProjectViewSnapshotKey({
  required String namespace,
  required String projectId,
  required int? namespaceEpoch,
}) =>
    'view:$namespace:${Uri.encodeComponent(projectId)}:${namespaceEpoch ?? 'none'}';

String mobileProjectViewSnapshotPrefix({
  required String namespace,
  required String projectId,
}) => 'view:$namespace:${Uri.encodeComponent(projectId)}:';

String mobileConversationSnapshotKey({
  required String namespace,
  required String projectId,
  required String agent,
  required int namespaceEpoch,
}) =>
    'conversation:$namespace:${Uri.encodeComponent(projectId)}:${Uri.encodeComponent(agent)}:$namespaceEpoch';
