#!/bin/zsh

set -euo pipefail

readonly repository="s3:https://s3.us-east-005.backblazeb2.com/archive-9f4c72d1e6b8/restic/incantation-bowl-index"
readonly restic_bin="/Users/mikesexton/.local/bin/restic"
readonly project_root="/Users/mikesexton/Developer/incantation-bowl-index"
readonly ivritelite_root="/Users/mikesexton/Developer/ivritelite"
readonly exclude_file="${project_root}/config/restic-b2-excludes.txt"
readonly receipt_dir="${project_root}/data/private/backup-receipts"
readonly timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
readonly receipt="${receipt_dir}/b2-restic-backup-${timestamp}.log"
readonly keychain_account="$(id -un)"
readonly key_id_service="org.incantation-bowl-index.b2.key-id"
readonly app_key_service="org.incantation-bowl-index.b2.application-key"
readonly password_service="org.incantation-bowl-index.restic.b2"
readonly password_command="/usr/bin/security find-generic-password -w -a ${keychain_account} -s ${password_service}"

if [[ ! -x "${restic_bin}" ]]; then
  print -u2 "Restic is not installed at ${restic_bin}."
  exit 1
fi

if [[ ! -d "${project_root}" || ! -d "${ivritelite_root}" ]]; then
  print -u2 "One or both project directories are missing."
  exit 1
fi

if [[ ! -f "${exclude_file}" ]]; then
  print -u2 "The reviewed B2 Restic exclude file is missing."
  exit 1
fi

export AWS_ACCESS_KEY_ID="$(/usr/bin/security find-generic-password -w -a "${keychain_account}" -s "${key_id_service}")"
export AWS_SECRET_ACCESS_KEY="$(/usr/bin/security find-generic-password -w -a "${keychain_account}" -s "${app_key_service}")"
export AWS_DEFAULT_REGION="us-east-005"
trap 'unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION' EXIT

mkdir -p "${receipt_dir}"
exec > >(/usr/bin/tee "${receipt}") 2>&1

restic=(
  "${restic_bin}"
  --repo "${repository}"
  --password-command "${password_command}"
  --option s3.region=us-east-005
  --option s3.bucket-lookup=path
)

print "Backblaze B2 Restic backup"
print "UTC start: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
print "Repository: private Backblaze B2 bucket through the S3-compatible API"

if ! "${restic[@]}" cat config >/dev/null 2>&1; then
  print "Initializing the encrypted B2 Restic repository…"
  "${restic[@]}" init
fi

print "Backing up the Bowl Index, its complete private vault, and IvritElite…"
"${restic[@]}" backup \
  "${project_root}" \
  "${ivritelite_root}" \
  --exclude-file "${exclude_file}" \
  --exclude-caches \
  --tag mac-mini-b2

if [[ "${IBI_RESTIC_FULL_CHECK:-0}" == "1" ]]; then
  print "Checking every stored data pack…"
  "${restic[@]}" check --read-data
else
  print "Checking repository metadata and structure…"
  "${restic[@]}" check
fi

print "Latest B2 snapshot:"
"${restic[@]}" snapshots --latest 1
print "UTC finish: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
print "RESULT: PASS"
