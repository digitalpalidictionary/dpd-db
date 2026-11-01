#!/usr/bin/env bash
# Build a contributor web server from a fresh clone, or finish one.
#
#   server_setup.sh [clone dir]        default: $HOME/dpd-db
#
# Safe to re-run: each step is skipped when its result is already there.
# Left out on purpose (see README "New server"): swap, nginx, certificate,
# add_contributor.sh, the deploy key, systemctl enable.
set -euo pipefail
# The window and run_script call a bare `uv`; a nohup shell may lack it on PATH.
export PATH="$HOME/.local/bin:$PATH"
clone="${1:-$HOME/dpd-db}"
repo_url="https://github.com/digitalpalidictionary/dpd-db"
uv="$HOME/.local/bin/uv"
data_dir="/var/lib/dpd/contrib_data"
# tipitaka.rte: the frequency setup reads the SYA corpus from it.
submodules=(resources/sc-data resources/dpd_submodules resources/tipitaka.rte)

step() { echo; echo "=== $1 | start $(date '+%F %T')"; step_start=$SECONDS; }
step_done() { echo "=== done in $((SECONDS - step_start)) s"; }

step "apt packages"
if ! dpkg -s pkg-config libicu-dev golang-go >/dev/null 2>&1; then
    sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y pkg-config libicu-dev golang-go
else
    echo "skipped: packages already installed"
fi
step_done

step "uv"
if [[ -x "$uv" ]]; then
    echo "skipped: $uv exists"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
step_done

step "clone"
if [[ -d "$clone/.git" ]] && git -C "$clone" rev-parse HEAD >/dev/null 2>&1; then
    echo "skipped: $clone is a working clone"
elif [[ -e "$clone" ]]; then
    echo "refused: $clone exists but is not a working clone; move it away"
    exit 1
else
    git clone "$repo_url" "$clone"
fi
cd "$clone"
step_done

step "submodules"
git submodule update --init -- "${submodules[@]}"
step_done

step "uv sync"
"$uv" sync --all-groups
step_done

step "config.ini"
if [[ ! -f config.ini ]]; then
    echo "copy config.ini into $clone, then run this script again"
    exit 1
fi
step_done

step "go version"
want="$(awk '/^go /{print $2}' go.mod)"
if [[ -z "$want" ]]; then
    echo "refused: no go line in go.mod"
    exit 1
fi
have="$(go version | awk '{print $3}')"
have="${have#go}"
if [[ "$(printf '%s\n' "$want" "$have" | sort -V | head -1)" != "$want" ]]; then
    echo "refused: go $have is older than go.mod's $want"
    exit 1
fi
step_done

step "initial setup"
if [[ -f logs/initial_setup_done ]]; then
    echo "skipped: logs/initial_setup_done exists"
else
    "$uv" run scripts/bash/initial_setup_run_once.py
    mkdir -p logs
    touch logs/initial_setup_done
fi
step_done

step "audio index"
if [[ -f audio/db/dpd_audio_index.tsv ]]; then
    echo "skipped: audio/db/dpd_audio_index.tsv exists"
else
    "$uv" run audio/index_release_download.py
fi
step_done

step "data dir"
sudo mkdir -p "$data_dir"
step_done

step "systemd unit"
sed -e "s|@USER@|$(id -un)|g" -e "s|@HOME@|$HOME|g" -e "s|@CLONE@|$clone|g" -e "s|@UV@|$uv|g" \
    scripts/server_contrib/dpd-gui@.service | sudo tee /etc/systemd/system/dpd-gui@.service >/dev/null
sudo systemctl daemon-reload
step_done

step "clean tree gate"
dirty="$(git status --porcelain --untracked-files=no)"
if [[ -n "$dirty" ]]; then
    echo "refused: tracked files changed before the first build:"
    echo "$dirty"
    exit 1
fi
step_done

step "first build"
if [[ -f logs/last_built_commit ]]; then
    echo "skipped: logs/last_built_commit exists"
else
    "$uv" run scripts/server_contrib/maintenance_window.py --no-systemd --no-push --data-dir "$data_dir"
fi
step_done

echo "SETUP_DONE"
