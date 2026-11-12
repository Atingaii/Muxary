import 'package:flutter/material.dart';

import '../../models/readable_terminal_history.dart';
import '../../repository/mobile_ccb_repository.dart';
import 'clipboard_feedback.dart';
import 'terminal_history_presentation.dart';

class AgentReadableHistoryLoader extends StatefulWidget {
  const AgentReadableHistoryLoader({
    required this.repository,
    required this.projectId,
    required this.agentName,
    required this.namespaceEpoch,
    required this.initialHistory,
    super.key,
  });

  final MobileCcbRepository repository;
  final String projectId;
  final String agentName;
  final int? namespaceEpoch;
  final ReadableTerminalHistory? initialHistory;

  @override
  State<AgentReadableHistoryLoader> createState() =>
      _AgentReadableHistoryLoaderState();
}

class _AgentReadableHistoryLoaderState
    extends State<AgentReadableHistoryLoader> {
  Future<ReadableTerminalHistory?>? _historyFuture;

  @override
  void initState() {
    super.initState();
    _historyFuture = _loadHistory();
  }

  @override
  void didUpdateWidget(covariant AgentReadableHistoryLoader oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.repository != widget.repository ||
        oldWidget.projectId != widget.projectId ||
        oldWidget.agentName != widget.agentName ||
        oldWidget.namespaceEpoch != widget.namespaceEpoch) {
      _historyFuture = _loadHistory();
    }
  }

  Future<ReadableTerminalHistory?> _loadHistory() async {
    final epoch = widget.namespaceEpoch;
    if (epoch == null) {
      return widget.initialHistory;
    }
    try {
      return await widget.repository.getReadableTerminalHistory(
            projectId: widget.projectId,
            agent: widget.agentName,
            namespaceEpoch: epoch,
            maxLines: 240,
          ) ??
          widget.initialHistory;
    } catch (_) {
      return widget.initialHistory;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ReadableTerminalHistory?>(
      future: _historyFuture,
      initialData: widget.initialHistory,
      builder: (context, snapshot) {
        return ReadableTerminalHistoryPanel(
          history: snapshot.data,
          namespaceEpoch: widget.namespaceEpoch,
        );
      },
    );
  }
}

class ReadableTerminalHistoryPanel extends StatelessWidget {
  const ReadableTerminalHistoryPanel({
    required this.history,
    required this.namespaceEpoch,
    super.key,
  });

  final ReadableTerminalHistory? history;
  final int? namespaceEpoch;

  @override
  Widget build(BuildContext context) {
    final terminalHistory = history;
    if (terminalHistory == null || terminalHistory.blocks.isEmpty) {
      return const Text('No terminal history yet');
    }
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;
    return Column(
      key: const ValueKey('readable-terminal-history'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Chip(
              avatar: const Icon(Icons.history, size: 18),
              label: Text(historyScopeLabel(terminalHistory.historyScope)),
              visualDensity: VisualDensity.compact,
            ),
            Chip(
              avatar: const Icon(Icons.tag, size: 18),
              label: Text('epoch ${namespaceEpoch?.toString() ?? 'stale'}'),
              visualDensity: VisualDensity.compact,
            ),
            if (terminalHistory.sourcePaneId != null)
              Chip(
                avatar: const Icon(Icons.web_asset, size: 18),
                label: Text(terminalHistory.sourcePaneId!),
                visualDensity: VisualDensity.compact,
              ),
            if (terminalHistory.stale)
              Chip(
                avatar: const Icon(Icons.warning_amber, size: 18),
                label: const Text('stale'),
                visualDensity: VisualDensity.compact,
                backgroundColor: colorScheme.errorContainer,
              ),
          ],
        ),
        if (terminalHistory.generatedAt != null) ...[
          const SizedBox(height: 4),
          Text(
            'Captured ${terminalHistory.generatedAt}',
            style: textTheme.bodySmall,
          ),
        ],
        const SizedBox(height: 8),
        SizedBox(
          height: 260,
          child: Scrollbar(
            child: ListView.separated(
              key: const ValueKey('readable-terminal-history-scroll'),
              primary: false,
              itemCount: terminalHistory.blocks.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                return TerminalHistoryBlockView(
                  block: terminalHistory.blocks[index],
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

class TerminalHistoryBlockView extends StatelessWidget {
  const TerminalHistoryBlockView({required this.block, super.key});

  final ReadableTerminalBlock block;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final textTheme = Theme.of(context).textTheme;
    final accent = terminalBlockColor(colorScheme, block.type);
    return DecoratedBox(
      key: ValueKey('terminal-history-block-${block.id}'),
      decoration: BoxDecoration(
        border: Border(left: BorderSide(color: accent, width: 4)),
        color: terminalBlockBackgroundColor(colorScheme, block.type),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(10, 8, 8, 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(terminalBlockIcon(block.type), size: 18, color: accent),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    block.title ?? terminalBlockLabel(block.type),
                    style: textTheme.titleSmall,
                  ),
                ),
                IconButton(
                  key: ValueKey('copy-terminal-history-${block.id}'),
                  tooltip: 'Copy block',
                  visualDensity: VisualDensity.compact,
                  onPressed: () {
                    copyTextWithFeedback(context, block.text);
                  },
                  icon: const Icon(Icons.copy, size: 18),
                ),
              ],
            ),
            if (block.language != null || block.status != null)
              Padding(
                padding: const EdgeInsets.only(left: 26, bottom: 4),
                child: Text(
                  [
                    if (block.language != null) block.language,
                    if (block.status != null) block.status,
                  ].join(' / '),
                  style: textTheme.bodySmall,
                ),
              ),
            Padding(
              padding: const EdgeInsets.only(left: 26),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: SelectableText(
                  terminalBlockText(block),
                  style: terminalBlockTextStyle(
                    textTheme: textTheme,
                    colorScheme: colorScheme,
                    type: block.type,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
