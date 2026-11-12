# Muxary Windows release scope

Muxary 0.1.0 has no independently validated Windows artifact or source-install
acceptance. Its active [projection](../../lib/platforms/windows/release/projection.json)
is explicitly **blocked**: no release artifact reference, executable entry,
Windows npm eligibility, or source-install admission. Linux source development
is not Windows release evidence.

The [unaltered upstream 8.7.22 projection](upstream-ccb-windows-projection-8.7.22.json)
is preserved only as historical source material from upstream commit
`df98e61e91b4be57873029b01667135e6265f371`. Its SHA-256 is
`c98812e869ac928d8ab0d018143452a959062684a566634d490643a3b8dabc16`.
Its inherited readiness statements do not attest any Muxary release.

The legacy `windows_beta_projection()` remains for upstream compatibility
fixtures; the current package identity selects a blocked fork policy instead.
Loading an inherited ready projection under the Muxary package identity cannot
promote it into fork acceptance. Freshness still requires the committed active
projection to match the current version and policy.

The [Windows workflow](../../.github/workflows/release-windows.yml) no longer runs
on tag pushes. It requires manual dispatch and repository variable
`MUXARY_ENABLE_WINDOWS_RELEASE=true`; publication additionally requires the
explicit `publish` input, which defaults to false. These controls do not certify
Windows support or ownership of publishing credentials. Existing build, smoke,
checksum, and bilingual-release-note checks remain in place. Independently
verified fork evidence and a reviewed policy change are still required before
unblocking the supported surface.
