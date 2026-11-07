#!/usr/bin/env bash
# Reset one existing contributor's password: new hash, nginx group, marker.
#
#   set_password.sh [--root DIR] <user>
#
# For a user whose files already exist (add_contributor.sh refuses those).
# The password is asked on the terminal, or read from stdin when stdin is a
# pipe. The forced-first-change marker is written, so the contributor lands
# on the change page at next login.
# The hash flags here must stay identical to add_contributor.sh (bcrypt cost
# 5): a parity test asserts both scripts emit $2y$05$ hashes.
set -euo pipefail

root=""
if [[ "${1:-}" == "--root" ]]; then
    root="${2:?--root needs a directory}"
    shift 2
fi

user="${1:?usage: set_password.sh [--root DIR] <user>}"

# Same rule as add_contributor.sh.
if [[ ! "$user" =~ ^[a-z][a-z0-9_]{0,31}$ ]]; then
    echo "refused: the user must be lower-case letters, digits or _, starting with a letter" >&2
    exit 1
fi

nginx_dir="$root/etc/nginx/dpd"
htpasswd_file="$nginx_dir/$user.htpasswd"

# Reset only what exists; creation is add_contributor.sh's job.
if [[ ! -f "$htpasswd_file" ]]; then
    echo "refused: $htpasswd_file does not exist" >&2
    exit 1
fi

# The hash must never be readable, even for the instant before chmod.
umask 077
htpasswd_flags=(-B -C 5)
if [[ ! -t 0 ]]; then
    htpasswd_flags+=(-i)
fi
htpasswd "${htpasswd_flags[@]}" "$htpasswd_file" "$user"
chmod 640 "$htpasswd_file"

# Same nginx-group dance as add_contributor.sh: 640 root:root makes the URL
# answer 500. HTPASSWD_GROUP overrides detection. Never fatal.
htpasswd_group="${HTPASSWD_GROUP:-}"
if [[ -z "$htpasswd_group" ]] && command -v nginx >/dev/null 2>&1; then
    htpasswd_group="$(nginx -T 2>/dev/null | sed -n 's/^user[[:space:]]\{1,\}\([^ ;]*\).*/\1/p' | head -1)"
fi
if [[ -n "$htpasswd_group" ]] && getent group "$htpasswd_group" >/dev/null 2>&1; then
    chgrp "$htpasswd_group" "$htpasswd_file" 2>/dev/null \
        || echo "WARNING: chgrp $htpasswd_group $htpasswd_file failed" >&2
else
    echo "WARNING: could not give $htpasswd_file to nginx's group." >&2
    echo "WARNING: run chgrp <nginx group> $htpasswd_file or the URL answers 500." >&2
fi

# Arm the forced first change: the contributor lands on the password page at
# next login. Mode 600; the only reader is the root-run password service.
marker_file="$nginx_dir/$user.initial"
touch "$marker_file"
chmod 600 "$marker_file"

echo "Reset $user's password. The marker is armed: the next login lands on"
echo "the change page. Old password stops working at the next login prompt"
echo "(an editor tab already open can keep the old login for up to an hour)."
