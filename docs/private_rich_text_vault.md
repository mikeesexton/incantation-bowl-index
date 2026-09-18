# Private rich-text vault

This is the package contract for OCR and corrected scholarly text kept in the
private research layer. It does not authorize publication, licensing, sharing or
corpus import. The text packages live under `data/private/rich_text/`, which is
Git-ignored, encrypted at rest with the research machine's storage controls and
included in the private backup set.

## Package layout

Each transformed document gets one directory:

```text
data/private/rich_text/<package-id>/
├── manifest.json
└── text.tei.xml
```

Copy `research/templates/private_rich_text_package_manifest.json` to begin a
package. The manifest binds the TEI file to one source, one retained capture and
the capture's document SHA-256. It separately records:

- the lawful acquisition basis and source-specific copying/download limits;
- the transformation state, method, UTC date and reviewer;
- the TEI file's own SHA-256; and
- an unconditional private-layer flag with `public_release` set to `false`.

Use `unknown — follow up required` when an item-specific restriction is not yet
known. An empty value is invalid because silence is not permission.

## TEI profile

The text is UTF-8, Unicode NFC and TEI P5 XML. Preserve ancient scripts as
Unicode characters rather than transliterating them for storage. Use ordinary
TEI editorial markup, including `unclear`, `gap`, `supplied`, `choice`, `sic`,
`corr`, `add` and `del`, so uncertainty and intervention remain explicit.

Every printed-page transition uses `pb`. Its `n` value preserves the printed
page label exactly, including roman numerals or an explicit unnumbered label.
Its `facs` value points back to the retained capture's PDF-image coordinate:

```xml
<pb n="23" facs="capture:CAP-ABC123#page=31"/>
```

The PDF page number is one-based, unique and increasing. It is deliberately
separate from printed pagination, which may restart or skip. Packages without
page-image anchors are invalid for this profile.

Validate a package without importing or printing its protected text:

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli \
  validate-rich-text-package data/private/rich_text/<package-id>
```

After the package passes review, a new append-only document assessment may
supersede the current holding assessment and bind the TEI path and SHA-256 with
`text_state: corrected_rich_text`. The package itself remains ignored by Git and
excluded from public exports.

## Pilot gate

Do not transform a complete edition until all of these are true:

1. The source and capture already have a complete holding assessment.
2. The manifest records item-specific access and copying terms.
3. Encrypted local and off-device backup destinations have both passed a sampled
   restore.
4. The package validates and a reviewer has compared the pilot against page
   images, including ancient script, gaps, restorations and page transitions.

The first pilot should be one bounded article or one bowl edition, not an entire
multi-hundred-page corpus. Scaling waits until the pilot's correction rate and
review burden are known.

## Backup boundary

The required backup set is the SQLite database, `data/private/archive/`,
`data/private/rich_text/`, and a machine-readable receipt listing hashes and
restore results. The present working copy has local compressed SQLite snapshots,
but they are unencrypted, exclude the private source archive, and are not an
off-device copy. They therefore do not satisfy OPS-002. The target backup and
restore design is defined in the
[Mac mini setup runbook](mac_mini_setup_runbook.md); deployment waits for that
machine.

An acceptable OPS-002 configuration must have two encrypted copies: one local
and one on a physically or administratively separate destination. Encryption
keys must not be stored beside either backup. A scheduled job must fail closed
when a destination is unavailable, retain a dated receipt, and alert rather than
silently pruning the last known-good copy. At least one sampled restore must:

- decrypt into a temporary directory;
- pass SQLite `integrity_check`, `quick_check` and `foreign_key_check`;
- verify every capture byte length and SHA-256 against the restored database;
- validate every restored rich-text package; and
- record the restored counts and hashes before the temporary copy is removed.

The approved off-device destination is a dedicated Backblaze B2 repository,
paired with a separate Restic repository on an encrypted external SSD. This
repository does not create either repository or its secrets automatically.
Those remain operator-controlled and are commissioned only on the Mac mini.

The read-only readiness check measures the current workstation state without
creating or deleting anything:

```sh
PYTHONPATH=src .venv/bin/python -m bowl_index.cli backup-readiness
```

It expects `IBI_BACKUP_GPG_RECIPIENT`, `IBI_LOCAL_BACKUP_DIR` and
`IBI_OFFDEVICE_BACKUP_DIR`. Both destinations must be writable absolute paths
outside the repository, and the off-device destination must resolve to a
different filesystem device. The check also requires encrypted bundles and at
least one restore receipt before reporting ready.

This command is an interim GPG-oriented prototype, not the approved Mac mini
implementation. Commissioning replaces or extends it with Restic-aware checks
for the encrypted APFS and B2 repositories, schedules, repository checks,
Healthchecks delivery and independent restore receipts. A passing legacy audit
alone cannot complete OPS-002.
