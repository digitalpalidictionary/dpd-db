#!/usr/bin/env bash
# Add one contributor to the server: login, env file, nginx location, data folder.
#
#   add_contributor.sh [--root DIR] <user> <port> [extra tabs]
#
# Every user shares one data folder, /var/lib/dpd/contrib_data; give it to
# maintenance_window.py with --data-dir.
# --root puts every file under DIR instead of / (for a test run). The files
# still name the real paths (/etc/nginx/dpd/..., /var/lib/dpd/...).
# The password is asked on the terminal, or read from stdin when stdin is a pipe.
# Extra tabs: comma-separated, e.g. "Bold Search,DB" (see gui2/contributor_tabs.py).
set -euo pipefail

root=""
if [[ "${1:-}" == "--root" ]]; then
    root="${2:?--root needs a directory}"
    shift 2
fi

user="${1:?usage: add_contributor.sh [--root DIR] <user> <port> [tabs]}"
port="${2:?usage: add_contributor.sh [--root DIR] <user> <port> [tabs]}"
tabs="${3:-}"

# A letter first: the username "1" means the maintainer.
if [[ ! "$user" =~ ^[a-z][a-z0-9_]{0,31}$ ]]; then
    echo "refused: the user must be lower-case letters, digits or _, starting with a letter" >&2
    exit 1
fi
# "added" would clash with the *_added review logs the sync scripts skip.
if [[ "$user" == *added* ]]; then
    echo "refused: the user name must not contain 'added'" >&2
    exit 1
fi
# The value goes into an env file between double quotes.
if [[ ! "$tabs" =~ ^[A-Za-z0-9\ ,√]*$ ]]; then
    echo "refused: tabs may hold only letters, digits, spaces, commas and √" >&2
    exit 1
fi
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1024 || port > 65535 )); then
    echo "refused: the port must be a number from 1024 to 65535" >&2
    exit 1
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env_dir="$root/etc/dpd"
nginx_dir="$root/etc/nginx/dpd"
env_file="$env_dir/$user.env"
htpasswd_file="$nginx_dir/$user.htpasswd"
nginx_file="$nginx_dir/$user.conf"
# One flat folder for every user: the nightly window, reconcile and push read a
# single folder, and the file names carry the user (additions_<user>.json).
data_dir="/var/lib/dpd/contrib_data"

for existing in "$env_file" "$htpasswd_file" "$nginx_file"; do
    if [[ -e "$existing" ]]; then
        echo "refused: $existing already exists" >&2
        exit 1
    fi
done
if compgen -G "$env_dir/*.env" > /dev/null; then
    taken="$(grep -l -x "FLET_SERVER_PORT=$port" "$env_dir"/*.env || true)"
    if [[ -n "$taken" ]]; then
        echo "refused: port $port is already used by $taken" >&2
        exit 1
    fi
fi

mkdir -p "$env_dir" "$nginx_dir" "$root$data_dir"

# The hash must never be readable, even for the instant before chmod.
umask 077
htpasswd_flags=(-B -c)
if [[ ! -t 0 ]]; then
    htpasswd_flags+=(-i)
fi
htpasswd "${htpasswd_flags[@]}" "$htpasswd_file" "$user"
chmod 640 "$htpasswd_file"

cat > "$env_file" <<ENV
DPD_GUI2_USERNAME=$user
DPD_GUI2_ROLE=contributor-server
DPD_GUI2_DATA_DIR=$data_dir
DPD_GUI2_TABS="$tabs"
FLET_FORCE_WEB_SERVER=true
FLET_SERVER_PORT=$port
ENV

sed -e "s|@USER@|$user|g" -e "s|@PORT@|$port|g" \
    "$here/nginx_contrib_user.conf.template" > "$nginx_file"

echo "Added $user."
echo "URL to hand over: https://<server name>/$user/"
echo "Next, on the server:"
echo "  sudo systemctl enable --now dpd-gui@$user"
echo "  sudo nginx -t && sudo systemctl reload nginx"
