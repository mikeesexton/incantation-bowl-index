#!/bin/zsh

set -euo pipefail

readonly backup_volume="/Volumes/IBI Backup"
readonly repository="${backup_volume}/restic/incantation-bowl-index"
readonly restic_bin="/Users/mikesexton/.local/bin/restic"
readonly project_root="/Users/mikesexton/Developer/incantation-bowl-index"
readonly ivritelite_root="/Users/mikesexton/Developer/ivritelite"
readonly exclude_file="${project_root}/config/restic-local-excludes.txt"
readonly keychain_service="org.incantation-bowl-index.restic.local"
readonly keychain_account="$(id -un)"
readonly password_command="/usr/bin/security find-generic-password -w -a ${keychain_account} -s ${keychain_service}"

if [[ ! -x "${restic_bin}" ]]; then
  print -u2 "Restic is not installed at ${restic_bin}."
  exit 1
fi

if [[ ! -d "${backup_volume}" ]]; then
  print -u2 "The encrypted IBI Backup volume is not mounted."
  exit 1
fi

if ! /usr/sbin/diskutil info "${backup_volume}" | /usr/bin/grep -q '^ *FileVault: *Yes'; then
  print -u2 "The IBI Backup volume is not reported as encrypted."
  exit 1
fi

if [[ ! -d "${project_root}" || ! -d "${ivritelite_root}" ]]; then
  print -u2 "One or both project directories are missing."
  exit 1
fi

if [[ ! -f "${exclude_file}" ]]; then
  print -u2 "The reviewed Restic exclude file is missing."
  exit 1
fi

mkdir -p "${repository}"

restic=(
  "${restic_bin}"
  --repo "${repository}"
  --password-command "${password_command}"
)

if [[ ! -f "${repository}/config" ]]; then
  print "Initializing the local encrypted Restic repository…"
  "${restic[@]}" init
fi

print "Backing up the Bowl Index, its complete private vault, and IvritElite…"
"${restic[@]}" backup \
  "${project_root}" \
  "${ivritelite_root}" \
  --exclude-file "${exclude_file}" \
  --exclude-caches \
  --tag mac-mini-local

print "Checking every stored data pack…"
"${restic[@]}" check --read-data

print "Latest local snapshot:"
"${restic[@]}" snapshots --latest 1
