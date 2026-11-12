# Decision 018: Stable Android Release Channel And In-App Update Handoff

Date: 2026-06-30
Status: Accepted for the Android upgrade/signing stability fix

## Context

User installs exposed two release-readiness gaps:

- CCB Mobile had no in-app place to see the current version or find the next
  APK.
- Android release builds were still signed with the debug key, so APKs built
  on another machine or CI could conflict with already installed copies and
  force an uninstall before install.

Android package updates preserve app data only when the new APK has the same
application id and signing lineage as the installed APK. The app already stores
paired gateway profiles in secure storage, so normal same-signature
cover-install must remain the release path. Android cannot bypass a prior
different-signature install; those users need a one-time uninstall/reinstall
notice.

## Decision

CCB Mobile Android release builds must use a stable release signing key from
local secret material, never the debug key.

The Gradle release signing boundary is:

- release signing values may come from ignored
  `app/android/release-signing.properties` or from environment variables:
  `CCB_MOBILE_RELEASE_STORE_FILE`,
  `CCB_MOBILE_RELEASE_STORE_PASSWORD`,
  `CCB_MOBILE_RELEASE_KEY_ALIAS`, and
  `CCB_MOBILE_RELEASE_KEY_PASSWORD`;
- `app/android/release-signing.properties.example` documents the shape without
  committing secrets;
- release tasks fail with a clear message when release signing is missing;
- debug builds remain debug-signed for local development only.

The first in-app update path is a browser/system-download handoff, not an
in-app APK installer:

- the app shows the current version and an APK download button in setup and
  connection details;
- the button opens the configured release/APK URL with the platform browser;
- release builds may override the displayed version and URL with
  `--dart-define=CCB_MOBILE_VERSION=...` and
  `--dart-define=CCB_MOBILE_APK_URL=...`;
- the UI explicitly explains that same-signature cover-install preserves paired
  data, while a historic different-signature APK requires one one-time
  uninstall before installing the official build.

## Channel Boundary

Debug/profile APKs are test artifacts. They must not be used as the official
upgrade channel for users and must not be mixed with stable release APKs on the
same device as a normal support path.

This package does not introduce flavors or an `applicationIdSuffix`; the
minimal channel boundary is the enforced signing split plus user-facing
guidance. If CI, Play, or public beta distribution needs parallel installable
channels later, add explicit flavors before distributing those builds.

## Remaining Risks

- The first update entry opens a browser/release page; it does not download the
  APK into app storage or invoke the package installer.
- The default release URL is a compile-time fallback until the official
  distribution pipeline sets `CCB_MOBILE_APK_URL` for release artifacts.
- Android cannot migrate data across APKs already installed with unrelated
  signing keys; support docs must tell affected historical users to uninstall
  once.
