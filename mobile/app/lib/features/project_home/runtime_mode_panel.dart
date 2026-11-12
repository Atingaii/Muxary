import 'package:flutter/material.dart';

import '../../app/runtime_mode.dart';
import '../../l10n/ccb_mobile_localizations.dart';
import '../../pairing/gateway_pairing.dart';
import '../../transport/gateway_route_diagnostics.dart';
import 'project_home_gateway_profiles.dart';

export 'project_home_gateway_profiles.dart'
    show projectHomeGatewayProfileKey, projectHomeGatewayProfileLabel;

class RuntimeModePanel extends StatelessWidget {
  const RuntimeModePanel({
    required this.mode,
    required this.profiles,
    required this.selectedProfile,
    required this.routeDiagnostics,
    required this.loadingProfiles,
    required this.checkingRoute,
    required this.onModeChanged,
    required this.onProfileSelected,
    required this.onCheckRoute,
    super.key,
  });

  final AppRuntimeMode mode;
  final List<GatewayPairedHost> profiles;
  final GatewayPairedHost? selectedProfile;
  final GatewayRouteDiagnosticReport? routeDiagnostics;
  final bool loadingProfiles;
  final bool checkingRoute;
  final ValueChanged<AppRuntimeMode> onModeChanged;
  final ValueChanged<GatewayPairedHost> onProfileSelected;
  final VoidCallback onCheckRoute;

  @override
  Widget build(BuildContext context) {
    final strings = CcbMobileLocalizations.of(context);
    final modes = AppRuntimeMode.values;
    final selectedMode = modes.contains(mode) ? mode : AppRuntimeMode.fake;
    return ExpansionTile(
      key: const ValueKey('runtime-mode-panel'),
      tilePadding: EdgeInsets.zero,
      childrenPadding: const EdgeInsets.only(top: 8, bottom: 8),
      leading: Icon(mode.icon),
      title: Text(strings.runtime),
      subtitle: Text(
        _runtimeSubtitle(context),
        key: const ValueKey('runtime-mode-status'),
      ),
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: SegmentedButton<AppRuntimeMode>(
            key: const ValueKey('runtime-mode-segments'),
            selected: {selectedMode},
            onSelectionChanged: (selection) => onModeChanged(selection.single),
            segments: [
              for (final item in modes)
                ButtonSegment<AppRuntimeMode>(
                  value: item,
                  icon: Icon(item.icon),
                  label: Text(strings.runtimeModeLabel(item.label)),
                ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<GatewayPairedHost>(
          key: ValueKey(
            'gateway-profile-select-${selectedProfile == null ? 'none' : projectHomeGatewayProfileKey(selectedProfile!)}',
          ),
          initialValue:
              profiles.contains(selectedProfile) ? selectedProfile : null,
          items: [
            for (final profile in profiles)
              DropdownMenuItem(
                value: profile,
                child: Text(
                  projectHomeGatewayProfileLabel(profile),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
          ],
          isExpanded: true,
          onChanged:
              profiles.isEmpty
                  ? null
                  : (profile) {
                    if (profile != null) {
                      onProfileSelected(profile);
                    }
                  },
          decoration: InputDecoration(
            labelText: strings.gatewayProfile,
            prefixIcon:
                loadingProfiles
                    ? const SizedBox.square(
                      dimension: 18,
                      child: Padding(
                        padding: EdgeInsets.all(14),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                    : const Icon(Icons.storage),
          ),
        ),
        if (selectedProfile != null) ...[
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Text(
                  _diagnosticsStatus(context),
                  key: const ValueKey('gateway-route-diagnostics-status'),
                ),
              ),
              const SizedBox(width: 12),
              OutlinedButton.icon(
                key: const ValueKey('gateway-route-check-button'),
                onPressed: checkingRoute ? null : onCheckRoute,
                icon:
                    checkingRoute
                        ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                        : const Icon(Icons.network_check),
                label: Text(
                  checkingRoute ? strings.checking : strings.checkRoute,
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }

  String _runtimeSubtitle(BuildContext context) {
    if (mode == AppRuntimeMode.pairedGateway && selectedProfile != null) {
      return projectHomeGatewayProfileLabel(selectedProfile!);
    }
    return CcbMobileLocalizations.of(context).runtimeModeLabel(mode.label);
  }

  String _diagnosticsStatus(BuildContext context) {
    final strings = CcbMobileLocalizations.of(context);
    if (checkingRoute) {
      return strings.checkingRoute;
    }
    return routeDiagnostics?.summary ?? strings.routeUnchecked;
  }
}
