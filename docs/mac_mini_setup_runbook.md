# Mac mini setup runbook

> **Status: commissioning in progress.** The repositories and private research
> vault were migrated to the Mac mini on 25 September 2026 UTC and verified on
> that host. The encrypted local Restic backup and independent local restore
> gate passed on 25 September 2026 UTC. B2, scheduling, monitoring, full
> Tailscale access and account-separation gates remain open; OPS-001 and OPS-002
> are not yet accepted. Complete the remaining arrival checklist on the Mac mini
> and record each result below.

This is the canonical operating plan for the shared Mac mini. The first half is
the general host baseline; the second half applies it to the Incantation Bowl
Index. Hardware-specific values are intentionally recorded only after the
machine and external drive are present.

## Target architecture

- The Mac mini is the primary always-on research host.
- A dedicated **1 TB encrypted APFS external SSD** is the fast local recovery
  destination. It is a backup destination, not the working copy.
- **Restic** encrypts separate local and off-device repositories. The local
  repository runs every four hours; the **Backblaze B2** repository runs daily,
  giving a target off-device recovery point of no more than 24 hours.
- The two Restic repositories use different passwords. Runtime credentials live
  in macOS Keychain; recovery copies are kept offline and away from the Mac mini
  and external SSD.
- **Healthchecks email** reports missed or failed scheduled jobs. Success pings
  are sent only after the corresponding backup or verification step completes.
- Remote administration uses **Tailscale** plus macOS SSH or Screen Sharing.
  Do not expose SSH, VNC, the research console or a collector directly to the
  public internet.

No item above is complete merely because software is installed. OPS-001 and
OPS-002 require the acceptance evidence and restore tests in this runbook.

## General host baseline

### Accounts and security

1. Create one named administrator account for software installation and recovery.
2. Use a separate standard account for normal research and scheduled user jobs.
   Do not run collectors or the Bowl Index as root.
3. Enable FileVault before depositing the private archive. Store the recovery
   key offline, separate from the Mac mini and its backup disk.
4. Enable automatic security and system-data updates. Apply macOS feature
   updates deliberately after checking development and backup compatibility.
5. Disable automatic login. Require authentication after sleep and restrict
   physical access to the machine and recovery media.
6. Keep service credentials in macOS Keychain. Do not put Restic passwords,
   Backblaze keys, health-check URLs or remote-access credentials in Git,
   shell-history snippets, checked-in environment files or backup receipts.

### Repository and runtime layout

- Keep active repositories under `~/Developer/`; do not place Git working trees
  in iCloud Drive, Dropbox or another file-synchronization folder.
- Treat GitHub as the canonical code-sync layer. Each computer has its own clone
  and pulls reviewed commits; private corpus data is restored or transferred
  through the documented encrypted data path, never through Git.
- Use one branch or worktree per active agent task. Before automated pulls,
  verify that the target checkout is clean and idle; never reset or overwrite an
  active or dirty checkout.
- Install Homebrew and the project-declared Python and Node runtimes only as
  needed. Pin dependencies through each repository's lock or environment files.
- Use `launchd` for recurring jobs. Keep versioned job templates in the relevant
  repository, install machine-specific plists outside Git and run them as the
  standard research account.
- Write service logs to a dedicated user-owned log directory with rotation.
  Logs and receipts must not contain secrets or protected source text.

### Remote access and observability

1. Enroll the Mac mini in the operator's Tailscale network and require account
   authentication and device approval.
2. Enable Remote Login or Screen Sharing only when needed and restrict access to
   named users over Tailscale.
3. Leave the router without inbound port forwards for the Mac mini.
4. Create separate Healthchecks checks for local backup, off-device backup and
   periodic restore verification. Configure email notification and send failure
   or missed-job signals without embedding private paths or credentials.
5. Confirm that every scheduled job has a bounded runtime, an explicit failure
   exit, useful logs, and a documented manual disable procedure.

## Backup and recovery design

### Backup sets and destinations

Use two independent Restic repositories:

| Repository | Destination | Schedule | Purpose |
|---|---|---|---|
| Local | 1 TB encrypted APFS external SSD | Every 4 hours | Fast recovery from corruption or accidental deletion |
| Off-device | Backblaze B2 through its S3-compatible endpoint | Daily | Recovery after loss, theft or failure of the Mac mini and local disk |

Each repository has its own password and credentials. Mounting the encrypted
external volume must require the operator's secret; do not store an unlock secret
on the same disk. Give the B2 application key access only to the dedicated backup
bucket and only the permissions required by Restic.

Back up the working data needed to reproduce each project, including private
data that is deliberately excluded from Git. Exclude transient environments,
dependency caches, build outputs, temporary restores, logs, mounted backup
destinations and Restic cache data. Maintain explicit include and exclude files
with the scheduled job templates so the backup boundary is reviewable.

### Retention and safety

- Apply retention independently to each repository only after a new snapshot is
  successfully written and the repository passes `restic check`.
- Never prune both repositories in the same job or maintenance window.
- Keep the existing eleven unencrypted Bowl Index SQLite snapshots until both
  encrypted repositories have passed the restore acceptance test below.
- Do not delete the last known-good snapshot or rely on retention policy as a
  substitute for restore verification.
- A missed destination, failed check or incomplete backup is an alert condition,
  not a reason to silently prune or report success.

### Restore acceptance gate

Before OPS-002 can be marked done, restore one current snapshot independently
from each repository into a new temporary directory. For the Bowl Index restore:

1. Run SQLite `integrity_check`, `quick_check` and `foreign_key_check`.
2. Verify the byte length and SHA-256 of every retained capture against the
   restored database.
3. Validate every restored private rich-text package.
4. Run the repository's normal tests and corpus-state check against the restored
   working data without altering the production database.
5. Record repository, snapshot ID, UTC time, restored counts, checks performed,
   result and operator in a receipt that contains no secret or protected text.
6. Remove the temporary restore only after the receipt is reviewed.

The first successful tests authorize later review of the legacy snapshot count;
they do not automatically delete any snapshot.

## Incantation Bowl Index overlay

The repository lives at `~/Developer/incantation-bowl-index`. Its private-data
rules remain governed by [the project rules](project-rules.md), and its rich-text
package contract remains governed by
[the private rich-text vault guide](private_rich_text_vault.md).

### Included private data

The Bowl Index backup set must include:

- the authoritative SQLite database and `data/db-state.json`;
- `data/private/archive/`, including retained source captures;
- `data/private/rich_text/`, including manifests and TEI files;
- private capture and transformation manifests required to verify those files;
- machine-readable backup and restore receipts that do not contain secrets; and
- any other ignored private input that the reproducibility audit identifies.

Git already protects the versioned source, tests, migrations, public
documentation and research manifests. Do not use that fact to omit private data
that cannot be recreated lawfully or reliably.

Exclude `.git/`, `.venv/`, dependency caches, generated temporary restores,
logs, mounted backup repositories and disposable build products from the Restic
payload. Generated corpus reports may be included when convenient, but they are
not a substitute for the database and manifests.

### Interim readiness command

`ibi backup-readiness` is a read-only **interim GPG-oriented prototype**. It
records useful facts about the current private tree, destinations, legacy
encrypted bundles, restore receipts and snapshot count, but it is not the target
Mac mini backup implementation. During commissioning, replace or extend it with
Restic-aware checks for:

- both initialized repositories and distinct repository passwords;
- the encrypted APFS local destination and dedicated B2 bucket;
- recent local and daily off-device snapshots;
- successful repository checks and Healthchecks delivery;
- current restore receipts from both destinations; and
- the explicit Bowl Index include/exclude boundary above.

Until that replacement is implemented, a passing legacy GPG check must not mark
OPS-002 complete. Conversely, the present failing audit is expected and should
not be "fixed" on the temporary workstation.

### Rich-text pilot gate

ACCESS-002 remains in progress. Do not create the first real TEI package until
the local and B2 restores both pass. The first transformation stays limited to
one bounded article or one bowl edition and must pass the existing package
validator and page-image review before any larger batch begins.

## Arrival-day checklist

Complete these items on the Mac mini; attach non-secret evidence to the
acceptance record.

### Host

- [ ] Record the hardware model, a non-secret asset reference, hostname and
      macOS version. Do not commit the full hardware serial number.
- [ ] Create and test the separate administrator and standard research accounts.
- [ ] Enable FileVault and place its recovery key offline.
- [ ] Apply current security updates and disable automatic login.
- [ ] Confirm sleep, restart and unattended power-recovery behavior.

### Development and access

- [ ] Install the required runtimes and clone repositories under `~/Developer/`.
- [ ] Verify GitHub authentication without placing tokens in repository files.
- [ ] Enroll and approve Tailscale; test SSH or Screen Sharing over Tailscale.
- [ ] Confirm that no public inbound port or router port-forward is enabled.
- [ ] Run the Bowl Index tests and confirm the recorded corpus digest before any
      private-data work.

### Backup and monitoring

- [ ] Attach, erase and encrypt the dedicated 1 TB APFS external SSD.
- [ ] Create separate local and B2 Restic repositories and recovery secrets.
- [ ] Store runtime secrets in Keychain and recovery copies offline.
- [ ] Install disabled-by-default `launchd` jobs, inspect their paths and
      include/exclude lists, then enable them deliberately.
- [ ] Configure Healthchecks email for local, off-device and restore jobs.
- [ ] Complete one local and one B2 backup without errors.
- [ ] Complete and record independent restore tests from both repositories.
- [ ] Confirm the eleven legacy SQLite snapshots are still present; authorize
      any later retention cleanup as a separate reviewed action.

## Acceptance record

Leave unknown fields blank until verified on the Mac mini.

| Field | Recorded value / evidence |
|---|---|
| Commissioning date (UTC) | 2026-09-25 (migration and first host verification) |
| Operator | Mike Sexton; Codex-assisted migration over local SSH |
| Hardware model / non-secret asset reference | Mac mini (Mac18,5), Apple M6, 24 GB memory |
| Hostname | `Mikes-Mac-Mini.local` |
| macOS version and build | macOS 27.0 (26A428), arm64 |
| FileVault enabled and recovery copy stored offline | FileVault On; offline recovery copy not verified |
| Administrator account tested | `mikesexton` is an administrator; SSH key login passed |
| Standard research account tested | Not yet created or verified separately from the administrator account |
| Internal storage / free space | 926 GiB volume; 827 GiB available at 2026-09-25T00:22:27Z |
| External SSD model, capacity and APFS encryption status | 2 TB USB `Mobile Drive`; GUID partition map; encrypted APFS (`FileVault: Yes`); mounted as `IBI Backup`. The USB enclosure does not expose SMART status, so retain B2 as the independent failure-domain copy. |
| Tailscale device and remote-access test | `mikes-mac-mini` connected; `mikes-laptop` enrolled but last observed offline. SSH over the local network passed with a dedicated Ed25519 key; Tailscale SSH path not yet tested end to end. |
| Public inbound ports confirmed absent | Not verified; router configuration was not examined |
| Repository path and Git revision | `~/Developer/incantation-bowl-index` content baseline `20f738e` plus subsequent acceptance-record commits; `~/Developer/ivritelite` at `3d75f04`; both clean and aligned with `origin/main` |
| Bowl Index corpus digest | `591faac7157c136e969ec739fbb557881b340298e0662ab564c7d6f7a5bb2ec8` (`ibi state`: match) |
| Local Restic repository and latest snapshot ID | Restic 0.19.1; encrypted repository on `IBI Backup`; snapshot `6b5ec6e564e4cf874ce38c46a464ee52fb8fd1f0e3d26558a455dafba4c2e0e1` |
| B2 bucket/repository and latest snapshot ID | Not configured |
| Local schedule and last successful run | First manual snapshot completed 2026-09-25T01:35:53Z; four-hour schedule not configured |
| Off-device schedule and last successful run | Not configured |
| Healthchecks email delivery tested | Not configured |
| Local restore receipt | `data/private/backup-receipts/local-restic-restore-20260925T014137Z.log`: PASS; restored 1.746 GiB / 1,664 files and directories, then reviewed and removed the temporary copy |
| B2 restore receipt | Not available |
| SQLite and capture verification result | `integrity_check` and `quick_check`: `ok`; foreign-key check empty; archive verification valid for 56 captures; all 556 private files matched the source aggregate SHA-256 `0717f4cca418b22da320d1eef9ad9f23cf91997409401e818d028ba3c5774b7f` |
| Rich-text package validation result | No private rich-text package is present (`rich_text_packages: 0`); no package validation required for this migration |
| Outstanding blockers / deviations | Separate standard account; B2 Restic repository and distinct recovery secret; laptop Tailscale connectivity and end-to-end remote-access test; router/public-port audit; launchd schedules; Healthchecks; B2 restore test. Seventeen legacy SQLite snapshots are retained. |
| OPS-001 accepted by/date | |
| OPS-002 accepted by/date | |
