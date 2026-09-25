#!/bin/zsh

set -euo pipefail

readonly repository="s3:https://s3.us-east-005.backblazeb2.com/archive-9f4c72d1e6b8/restic/incantation-bowl-index"
readonly live_bowl_root="/Users/mikesexton/Developer/incantation-bowl-index"
readonly live_ivritelite_root="/Users/mikesexton/Developer/ivritelite"
readonly restic_bin="/Users/mikesexton/.local/bin/restic"
readonly node_bin="/Users/mikesexton/.local/bin/node"
readonly keychain_account="$(id -un)"
readonly key_id_service="org.incantation-bowl-index.b2.key-id"
readonly app_key_service="org.incantation-bowl-index.b2.application-key"
readonly password_service="org.incantation-bowl-index.restic.b2"
readonly password_command="/usr/bin/security find-generic-password -w -a ${keychain_account} -s ${password_service}"
readonly receipt_dir="${live_bowl_root}/data/private/backup-receipts"
readonly timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
readonly receipt="${receipt_dir}/b2-restic-restore-${timestamp}.log"
readonly restore_root="$(mktemp -d /private/tmp/ibi-b2-restic-restore.XXXXXX)"
readonly restored_bowl_root="${restore_root}${live_bowl_root}"
readonly restored_ivritelite_root="${restore_root}${live_ivritelite_root}"

export AWS_ACCESS_KEY_ID="$(/usr/bin/security find-generic-password -w -a "${keychain_account}" -s "${key_id_service}")"
export AWS_SECRET_ACCESS_KEY="$(/usr/bin/security find-generic-password -w -a "${keychain_account}" -s "${app_key_service}")"
export AWS_DEFAULT_REGION="us-east-005"
trap 'unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION' EXIT

mkdir -p "${receipt_dir}"
print -r -- "${restore_root}" > "${receipt_dir}/latest-b2-restore-path.txt"

restic=(
  "${restic_bin}"
  --repo "${repository}"
  --password-command "${password_command}"
  --option s3.region=us-east-005
  --option s3.bucket-lookup=path
)

{
  print "Backblaze B2 Restic restore acceptance test"
  print "UTC start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  print "Repository: private Backblaze B2 bucket through the S3-compatible API"

  snapshot_id="$("${restic[@]}" snapshots --latest 1 --json | /usr/bin/python3 -c 'import json, sys; rows = json.load(sys.stdin); print(rows[-1]["id"] if rows else "")')"
  if [[ -z "${snapshot_id}" ]]; then
    print -u2 "No B2 Restic snapshot exists."
    exit 1
  fi
  print "Snapshot: ${snapshot_id}"
  print "Restore root: ${restore_root}"

  "${restic[@]}" restore "${snapshot_id}" --target "${restore_root}"

  restored_db="${restored_bowl_root}/data/private/ibi.sqlite3"
  if [[ ! -f "${restored_db}" ]]; then
    print -u2 "The restored Bowl Index database is missing."
    exit 1
  fi

  print "SQLite integrity and quick checks:"
  /usr/bin/sqlite3 "${restored_db}" 'PRAGMA integrity_check; PRAGMA quick_check;'
  foreign_key_rows="$(/usr/bin/sqlite3 "${restored_db}" 'PRAGMA foreign_key_check;' | /usr/bin/wc -l | /usr/bin/tr -d ' ')"
  print "SQLite foreign-key violations: ${foreign_key_rows}"
  if [[ "${foreign_key_rows}" != "0" ]]; then
    exit 1
  fi

  print "Restored database SHA-256:"
  /usr/bin/shasum -a 256 "${restored_db}"

  cd "${restored_bowl_root}"
  print "Archive verification:"
  PYTHONPATH="${restored_bowl_root}/src" "${live_bowl_root}/.venv/bin/python" \
    -m bowl_index.cli --db "${restored_db}" verify-archive

  print "Corpus-state verification:"
  PYTHONPATH="${restored_bowl_root}/src" "${live_bowl_root}/.venv/bin/python" \
    -m bowl_index.cli --db "${restored_db}" state

  print "Bowl Index tests:"
  PYTHONPATH="${restored_bowl_root}/src" "${live_bowl_root}/.venv/bin/python" \
    -m unittest discover -s "${restored_bowl_root}/tests" -q

  cd "${restored_ivritelite_root}"
  print "IvritElite tests:"
  "${node_bin}" --test --test-reporter=dot

  print "UTC finish: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  print "RESULT: PASS"
  print "The temporary restore remains in place pending receipt review."
} 2>&1 | /usr/bin/tee "${receipt}"
