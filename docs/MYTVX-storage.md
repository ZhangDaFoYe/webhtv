# MYTVX storage and fork builds

## Approved scope and decision (2026-10-05)
User approved moving app-managed shared storage under Download/mytvx, preserving
TVBox/VOX/TV subdirectories without migrating or deleting existing files, and
building signed APKs in ZhangDaFoYe/webhtv Actions. No upstream publication.

Evidence: source baseline 84769dcc09348e0c2cb2a7ce34c8c921fecb3302,
`catvod/.../utils/Path.java` is the shared app/spider API; app backups,
CustomCsp, remote store, local upload, GitCloud, SyncFiles and LoginStateSync all
consume it. No literal VOX or TVBox write exists in the tracked Java sources;
those names may be supplied by downloaded spiders. FileChooser's external root
references resolve user-selected files for reading, not app-managed directories.
`Updater.start` launches upstream GitHub stable/beta checks; custom signing makes
those APKs incompatible. `.github/workflows/android-release.yml` gives the exact
JDK21/Android37 release matrix and signing properties.

Primary references retrieved 2026-10-05 (official, high confidence):
- https://developer.android.com/training/data-storage/app-specific — app-specific
  external files and internal files are safe fallbacks when public paths are not
  writable; public Download access depends on platform permissions/scoped storage.
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
  — GITHUB_TOKEN writes do not trigger push workflows, but workflow_dispatch does.

No upstream feature/dependency integration is proposed. Upstream issue/revert
research, related player projects and papers are inapplicable to this bounded
filesystem policy. No claim of a general sandbox for arbitrary third-party code.

Alternatives: no change/upstream paths violate the request; changing only TV()
misses root-based TVBox/VOX consumers. Selected: relocate the shared root API,
remap legacy absolute names at helper write boundaries, preserve legacy reads,
reject traversal from root child APIs, and use app-specific/internal fallbacks.
This deliberately also puts other Path.root consumers (e.g. TVData and remote
trust) under the same base, keeping sync/file browsing consistent. Disable the
built-in updater for this fork with an explanatory message; distribute via Actions
rather than pretending upstream manifests contain compatible custom builds.

## Acceptance and rollback
- New helper-managed TVBox/VOX/TV writes are beneath public Download/mytvx when
  writable, otherwise app-specific Download/mytvx, then internal files/mytvx.
- Legacy files are not migrated/deleted on startup. Local reads can fall back.
- JVM filesystem regression tests cover remaps, traversal and denied public path.
- Four normal release variants compile with a stable fork-owned signing key.
- Hourly sync merges non-destructively; successful changed HEAD dispatches build.
- Roll back by reverting the task commit; existing new/legacy data is untouched.

## Operations and caveats
Private signing material is stored outside Git under /opt/webhtv-mytvx-signing
(mode 700 directory, 600 files), and uploaded as MYTVX_* repository secrets.
Back up that directory privately: losing the key prevents in-place future updates.
The application ID remains upstream's; switching from an upstream-signed install
requires uninstalling it (back up app data first). No automatic migration occurs.
Actions artifacts expire after 30 days. No CNB/OCI publishing or upstream release.

Downloaded jars, Python/JS/native libraries which directly use filesystem APIs,
hardcode /sdcard/TVBox, or bundle their own Path class can bypass this policy.
A Java helper is not an OS sandbox. They must be audited individually or avoided.
No attached Android device: scoped-storage behavior, UI restoration, playback and
real plugin writes remain device-unverified even after APK compilation.

## Recovery anchor
Implemented on main in /root/projects/webhtv-mytvx; initial tree was clean.
`python3 scripts/test_mytvx_storage.py`: PASS, 60 assertions executing production
Path and StorageRoot against filesystem fixtures with minimal Android stubs.
Includes all three directories, alias paths, nested writes, read compatibility,
copy/create/stream operations, traversal/symlink rejection and fallback selection.
`git diff --check`: passed. MYTVX_* secrets uploaded and names read back via gh.
Implementation commit: d75bb98a0f7be2763b134a10ae5af176617516fc.
First CI https://github.com/ZhangDaFoYe/webhtv/actions/runs/37277654911 passed
storage tests, native asset verification and signing setup, then failed because
Chaquopy requires Python 3.10. Follow-up c3bf1caeb0d5e866322bff1e743a0244c668e6fc
installs Python 3.10; retry https://github.com/ZhangDaFoYe/webhtv/actions/runs/37277985186
completed successfully for all four release variants (Mobile/Leanback x
arm64-v8a/armeabi-v7a), including apksigner verification and artifact upload.
GitHub artifacts API returned exactly four non-expired artifacts, IDs:
11331665883, 11331197607, 11331182671, 11330369380.
An attempted local `gh run download` timed out before extracting files; artifacts
remain available through the successful run page. Sync verification run
https://github.com/ZhangDaFoYe/webhtv/actions/runs/37277776138 succeeded (no new
upstream commit, so no automatic build dispatch was needed).
Next: parent independent review and device testing; local APK download may be
retried separately if needed.
Parent independently reviews before closure; actual Android permissions and
plugin runtime behavior are still unverified.
