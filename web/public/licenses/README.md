# Supplementary dependency licenses

Vite generates `../THIRD_PARTY_NOTICES.md` from the dependencies present in the
JavaScript bundle. These supplementary files are copied unchanged by Vite's
standard `public` directory behavior; no second license collector is used.
They do not replace the generated per-package copyright notices or the
separately retained licenses for vendored Agent Elements and shadcn sources.

## Apache License 2.0

- File: `Apache-2.0.txt` (unmodified official text, 11,358 bytes).
- Source: <https://www.apache.org/licenses/LICENSE-2.0.txt>.
- Retrieved: 2026-11-11.
- SHA-256: `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`.
- Applies to bundled `streamdown@2.7.1` and `remend@1.4.0`, whose installed
  `LICENSE` files contain the Apache copyright/license-reference statement
  rather than the full terms. Their own statements remain in the generated
  notices; this file supplies the complete referenced license.

## react-remove-scroll-bar upstream MIT supplement

- File: `react-remove-scroll-bar-upstream-MIT.txt` (unmodified upstream text,
  1,093 bytes).
- Source: <https://raw.githubusercontent.com/theKashey/react-remove-scroll-bar/8ca9ba5ea52de03308fe8ced94f7b159a44d28ff/LICENSE>.
- Fixed repository commit: `8ca9ba5ea52de03308fe8ced94f7b159a44d28ff`.
- Retrieved: 2026-11-11.
- SHA-256: `a79aae0c0f21990d9d963bb3c5a79cdcea9a46f8523ba55c58d7fe776b6ebc84`.
- Association: supplementary MIT text from the same upstream project as bundled
  `react-remove-scroll-bar@2.3.8`. The file carries the upstream's actual 2025
  copyright notice; it is not rewritten to invent a release-specific notice.

The npm distribution of `react-remove-scroll-bar@2.3.8` contains no license file;
its manifest and README declare MIT. Its npm metadata reports `gitHead`
`b3b1287aad81def2e2ae707274b74531b61ddbaf`, but requests for that commit's license
and package manifest in the declared repository returned 404. No exact release
license text has therefore been verified. The fixed upstream commit used for
the supplement still identifies its package as `2.3.7`; this supplement is not
proof of the published 2.3.8 bytes or its release commit. Metadata source:
<https://registry.npmjs.org/react-remove-scroll-bar/2.3.8>.

## Verification boundary

For the 135 packages listed by the checked build on 2026-11-11, 134 have license
text matching the installed package's license file. No separate `NOTICE` file
was found within those package directories. This observation is specific to
the installed lockfile and emitted bundle, not a general guarantee about
future dependencies or versions. The two `NOTICE.txt` files belonging to the
development-only TypeScript installation are not part of the emitted bundle.

`react-remove-scroll-bar@2.3.8` remains the generated entry with only an MIT
identifier and no body. Its supplementary same-project text and the unresolved
release-provenance boundary are recorded above rather than silently replacing
the generated evidence. A generic nonempty-file release gate checks presence,
not the completeness or legal status of every possible dependency license.
