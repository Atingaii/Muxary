const demoProjectViewFixture = <String, Object?>{
  'view': <String, Object?>{
    'schema_version': 1,
    'generated_at': '2026-06-18T00:00:00Z',
    'project': <String, Object?>{
      'id': 'proj-demo',
      'root': '/srv/ccb/demo',
      'display_name': 'demo',
    },
    'ccbd': <String, Object?>{
      'state': 'mounted',
      'health': 'healthy',
      'generation': 7,
    },
    'namespace': <String, Object?>{
      'epoch': 4,
      'socket_path': '/tmp/ccb-demo/tmux.sock',
      'session_name': 'ccb-demo',
      'active_window': 'main',
      'active_pane_id': '%2',
    },
    'windows': <Object?>[
      <String, Object?>{
        'name': 'main',
        'label': 'main',
        'kind': 'agents',
        'order': 0,
        'active': true,
        'agents': <Object?>['lead', 'mobile'],
        'tmux_window_id': '@1',
        'tmux_window_index': 0,
      },
    ],
    'agents': <Object?>[
      <String, Object?>{
        'name': 'lead',
        'provider': 'codex',
        'window': 'main',
        'order': 0,
        'pane_id': '%1',
        'active': false,
        'queue_depth': 0,
        'runtime_health': 'healthy',
        'state': 'completed',
      },
      <String, Object?>{
        'name': 'mobile',
        'provider': 'codex',
        'window': 'main',
        'order': 1,
        'pane_id': '%2',
        'active': true,
        'queue_depth': 1,
        'runtime_health': 'healthy',
        'state': 'callback',
      },
    ],
    'comms': <String, Object?>{
      'items': <Object?>[
        <String, Object?>{
          'id': 'comms-mobile-callback',
          'kind': 'mention',
          'agent': 'mobile',
          'window': 'main',
          'title': 'Callback needed',
          'preview': 'mobile needs a decision before continuing.',
          'requires_attention': true,
        },
      ],
    },
    'content': <String, Object?>{
      'items': <Object?>[
        <String, Object?>{
          'id': 'content-lead-plan',
          'agent': 'lead',
          'kind': 'reply',
          'format': 'markdown',
          'title': 'Architecture checkpoint',
          'source': 'ccbd',
          'text': '''
# Architecture checkpoint

- Keep the app agent-first.
- Treat structured CCB content as authoritative.
- Keep raw terminal behind Open Terminal.

```text
selected agent -> content reader -> readable history -> raw terminal fallback
```
''',
        },
        <String, Object?>{
          'id': 'content-mobile-emulator',
          'agent': 'mobile',
          'kind': 'reply',
          'format': 'markdown',
          'title': 'Emulator landing status',
          'source': 'ccbd',
          'text': '''
# Emulator landing status

The mobile slice should be validated through local AVD and loopback gateway.

| Gate | State |
| --- | --- |
| Agent switcher | ready |
| Readable history | fixture |
| Raw terminal | explicit |

```bash
adb reverse tcp:8787 tcp:8787
flutter test
```
''',
        },
      ],
    },
    'terminal_history': <String, Object?>{
      'by_agent': <String, Object?>{
        'lead': <String, Object?>{
          'history_scope': 'tmux_scrollback',
          'source_pane_id': '%1',
          'generated_at': '2026-06-20T09:40:00Z',
          'stale': false,
          'blocks': <Object?>[
            <String, Object?>{
              'id': 'lead-command-plan',
              'type': 'command',
              'title': 'Command',
              'text': 'rg -n "Agent-first" docs/plantree',
            },
            <String, Object?>{
              'id': 'lead-log-plan',
              'type': 'log',
              'title': 'Plan evidence',
              'text': 'Decision 012 accepted. Decision 013 accepted.',
            },
          ],
        },
        'mobile': <String, Object?>{
          'history_scope': 'tmux_scrollback',
          'source_pane_id': '%2',
          'generated_at': '2026-06-20T09:41:00Z',
          'stale': false,
          'blocks': <Object?>[
            <String, Object?>{
              'id': 'mobile-command-adb',
              'type': 'command',
              'title': 'Command',
              'text': 'adb reverse tcp:8787 tcp:8787',
            },
            <String, Object?>{
              'id': 'mobile-log-claim',
              'type': 'log',
              'title': 'Gateway claim',
              'text': 'paired dev-emulator through http://127.0.0.1:8787',
            },
            <String, Object?>{
              'id': 'mobile-code-smoke',
              'type': 'code',
              'title': 'Smoke command',
              'language': 'bash',
              'text': '''
flutter test test/widget_test.dart
flutter build apk --debug
''',
            },
            <String, Object?>{
              'id': 'mobile-diff-content',
              'type': 'diff',
              'title': 'Readable history contract',
              'language': 'diff',
              'text': '''
+ structured content reader
+ vertically scrollable readable terminal history
- terminal-first default page
''',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-01',
              'type': 'log',
              'title': 'Checkpoint 01',
              'text': 'ProjectView loaded from fake gateway fixture.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-02',
              'type': 'log',
              'title': 'Checkpoint 02',
              'text': 'Selected agent remains mobile after refresh.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-03',
              'type': 'log',
              'title': 'Checkpoint 03',
              'text': 'Terminal token renewal is visible in raw mode.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-04',
              'type': 'log',
              'title': 'Checkpoint 04',
              'text': 'Route diagnostics explain loopback and adb reverse.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-05',
              'type': 'log',
              'title': 'Checkpoint 05',
              'text': 'History scroll keeps older blocks accessible.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-06',
              'type': 'log',
              'title': 'Checkpoint 06',
              'text': 'Raw terminal remains an explicit action.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-07',
              'type': 'log',
              'title': 'Checkpoint 07',
              'text': 'No public route is required for emulator validation.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-08',
              'type': 'log',
              'title': 'Checkpoint 08',
              'text': 'Structured Markdown remains the authoritative source.',
            },
            <String, Object?>{
              'id': 'mobile-checkpoint-09',
              'type': 'log',
              'title': 'Checkpoint 09',
              'text': 'Long retained scrollback stays reachable by drag.',
            },
          ],
        },
      },
    },
  },
};
