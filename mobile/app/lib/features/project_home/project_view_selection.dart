import '../../models/ccb_agent.dart';
import '../../models/ccb_project_view.dart';
import '../../models/ccb_window.dart';

String? firstAgentNameForWindow(CcbProjectView view, String windowName) {
  final agents = agentsForWindow(view, windowName);
  return agents.isEmpty ? null : agents.first.name;
}

CcbAgent? selectedProjectHomeAgent(
  CcbProjectView view,
  String? selectedAgentName,
) {
  if (selectedAgentName != null) {
    final selected = view.agentByName(selectedAgentName);
    if (selected != null) {
      return selected;
    }
  }
  for (final agent in view.agents) {
    if (agent.active) {
      return agent;
    }
  }
  return view.agents.isEmpty ? null : view.agents.first;
}

String? projectHomeLocalWindowSelectionAgentName(
  CcbProjectView view,
  String windowName,
) {
  return firstAgentNameForWindow(view, windowName);
}

List<CcbWindow> orderedWindowsForView(CcbProjectView view) {
  final windows = [...view.windows];
  windows.sort((a, b) {
    final byOrder = a.order.compareTo(b.order);
    return byOrder != 0 ? byOrder : a.name.compareTo(b.name);
  });
  if (windows.isNotEmpty) {
    return windows;
  }
  final names = <String>[];
  for (final agent in view.agents) {
    final name = _normalizedWindowName(agent.window);
    if (!names.contains(name)) {
      names.add(name);
    }
  }
  return [
    for (var index = 0; index < names.length; index += 1)
      CcbWindow(
        name: names[index],
        label: names[index],
        kind: 'agents',
        order: index,
        active: _normalizedWindowName(view.activeWindow) == names[index],
        agents: [
          for (final agent in view.agents)
            if (_normalizedWindowName(agent.window) == names[index]) agent.name,
        ],
      ),
  ];
}

List<CcbAgent> agentsForWindow(CcbProjectView view, String windowName) {
  final normalized = _normalizedWindowName(windowName);
  final byName = {for (final agent in view.agents) agent.name: agent};
  final result = <CcbAgent>[];
  final seen = <String>{};
  final window = view.windowByName(windowName) ?? view.windowByName(normalized);
  if (window != null) {
    for (final name in window.agents) {
      final agent = byName[name];
      if (agent != null && seen.add(agent.name)) {
        result.add(agent);
      }
    }
  }
  final remaining = [
    for (final agent in view.agents)
      if (_normalizedWindowName(agent.window) == normalized &&
          seen.add(agent.name))
        agent,
  ]..sort((a, b) {
    final byOrder = a.order.compareTo(b.order);
    return byOrder != 0 ? byOrder : a.name.compareTo(b.name);
  });
  result.addAll(remaining);
  return result;
}

CcbWindow? selectedWindowForView(CcbProjectView view, CcbAgent? selectedAgent) {
  final windows = orderedWindowsForView(view);
  if (windows.isEmpty) {
    return null;
  }
  final selectedAgentWindow = selectedAgent?.window;
  if (selectedAgentWindow != null && selectedAgentWindow.trim().isNotEmpty) {
    final normalized = _normalizedWindowName(selectedAgentWindow);
    for (final window in windows) {
      if (_normalizedWindowName(window.name) == normalized) {
        return window;
      }
    }
  }
  final activeWindow = view.activeWindow;
  if (activeWindow != null && activeWindow.trim().isNotEmpty) {
    final normalized = _normalizedWindowName(activeWindow);
    for (final window in windows) {
      if (_normalizedWindowName(window.name) == normalized) {
        return window;
      }
    }
  }
  for (final window in windows) {
    if (window.active) {
      return window;
    }
  }
  return windows.first;
}

String _normalizedWindowName(String? value) {
  final trimmed = (value ?? '').trim();
  return trimmed.isEmpty ? 'main' : trimmed;
}
