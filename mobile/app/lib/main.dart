import 'package:flutter/material.dart';

import 'app/ccb_mobile_app.dart';
import 'notifications/push_notifications.dart';

export 'app/ccb_mobile_app.dart';
export 'features/project_home/project_home_screen.dart';
export 'l10n/ccb_mobile_localizations.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  registerPushNotificationBackgroundHandler();
  runApp(const CcbMobileApp());
}
