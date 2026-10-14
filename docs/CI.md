# Per-commit evidence and publication

## Exact source identity

`verify.py` refuses an uncommitted tree by default. It records HEAD/tree SHA and SHA256 for every tracked source; it compares these with the same manifest, Git status and HEAD after verification. No source edits occur during a run. This is a beginning/end snapshot guard, not a monitor against an adversary changing and restoring bytes mid-run. Proof build starts from a removed `.lake/build` cache and C is regenerated for that snapshot.

Each stage has `passed`, `failed` or `not_run`, return status and log. Failed dependencies cause explicit `not_run`, and other useful checks continue. Overall gate success and requirement coverage are independent: the latter is currently **incomplete**. A failed trace run remains an error; an unproved ABI remains an open coverage gap even if all tests pass.

Current verification includes the generic Basic Task model and all 76 theorem
axiom reports, its independent Python comparison, the bounded generated-C
adapter, and seven actual QEMU AArch64 scenarios. CI installs `qemu-system-arm`;
missing QEMU is a failed required gate, never a successful skip. The task
comparison is in `test-results/task-control.json`; the target image, generated
C, versions, commands and UART observations are in `qemu/`. The original M0
regression checks still run. See README for reproducible local setup.

The static requirements catalogue records scope, implementation, proof and test separately. Runtime evidence determines proof/test results; links alone never upgrade them. `trace.json` contains the same edges in both directions. The validator rejects missing source/definition/theorem/symbol/test/file references and untraced theorems. `impact.py` conservatively maps changed files/modules to requirements/proofs/tests; it is not a proof of minimal semantic impact. Full gates run regardless.

## Every commit in a push

The workflow uses full Git history and enumerates `before..after` with `git rev-list --reverse --topo-order`. It does not rely on a truncated webhook commits array. A new branch or manual backfill (`scope: history`) enumerates the entire reachable history. Manual runs default to `scope: head`, checking only the selected branch tip so a known historical failure does not prevent checking the current version. The target plan records the selected scope. If the old SHA is unavailable for a push, all reachable history is checked and the fallback is recorded. Force-push histories not reachable from the new branch are retained in prior evidence, but an unavailable historical object cannot be reconstructed.

To check the current main, choose Actions → Per-commit verification → Run workflow, select `main`, and leave scope as `head`. Re-running an old run uses its original workflow and event; it does not pick up this change. Historical failures remain recorded and are not converted into successes.

The plan lists every target SHA and initializes a `not_run` record for each **before** installing tools. A separate targets artifact is uploaded immediately. Each commit is checked in a detached worktree using that commit's own verifier. Commits predating the verifier remain explicitly `not_run`; they are not tested by substituting HEAD. Timeouts/failures retain records, and later targets are attempted. Job-wide cancellation may prevent final upload/Pages publication; the early target-plan artifact still identifies SHAs whose completion has not been established. GitHub artifact-upload outages cannot be guaranteed away.

Run IDs and attempts are part of every path: `commits/<SHA>/runs/<run-id>-<attempt>/`. The evidence artifact name contains run ID/attempt and includes `targets.json`. A local run is marked `local-...`, never called a GitHub Actions run. Artifacts are retained for 90 days, not indefinitely.

## Publication model and permissions

Verification gets only `contents: read`, no persisted checkout credentials, no project secrets and no privileged PR workflow. The trusted `main` archive job alone has `contents: write`; it appends lightweight reports to a dedicated `evidence-history` branch. That job publishes no PR artifact and refuses to overwrite an existing run. No branch history is force-pushed. No shared workflow concurrency group is used: even a non-cancelling group can replace queued runs. Concurrent history appends retry optimistic non-fast-forward conflicts without force-pushing. The deploy job has only `pages: write` and `id-token: write` and uses the `github-pages` environment. First-party Actions are pinned to verified immutable tag SHAs.

`evidence-history` retains JSON/logs/generated C/stack reports across Pages deployments. Full compiled binaries and `.olean` files remain in run-specific Actions artifacts; the report hashes them and links the workflow run. Pages `latest.json` selects the newest recorded run ID/attempt; it does not assert that a newer unverified main HEAD has completed. It is an explicit pointer, not a replacement for historical results. Failed verification is also eligible for publication, so the latest failed result is not hidden behind an older green page.

## Publication bootstrap — pending

1. Confirm ownership/access and create **public** `4ge32/lean-cp-os` only if absent. A 404 from the connector does not exclude a private inaccessible repository. Inspect any existing contents before choosing a branch or integrating changes.
2. Review the source-license choice separately; this repository deliberately has no software license grant yet.
3. Push the local main commit without force. Enable Actions; configure Settings → Pages → source **GitHub Actions** and restrict the `github-pages` environment to main.
4. Run/observe the workflow. Verify the remote SHA, exact target list, every evidence result, artifact/run linkage, history branch and actual returned Pages deployment URL.

This environment cannot complete steps 1–4: the connected repository API lacks create/Pages-settings operations, and browser access for creation was explicitly denied. No remote URL, Actions success or Pages deployment is claimed. The workflow configuration has local structural/scenario checks only; remote behavior remains unexecuted.
