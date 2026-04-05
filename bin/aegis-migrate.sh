#!/usr/bin/env bash
# aegis-migrate.sh — export/import SC-ARCHIVE application data
# Usage:
#   ./bin/aegis-migrate.sh export [output_dir]
#   ./bin/aegis-migrate.sh import <archive.tar.gz>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$HOME/.config/sc-archive"
SETTINGS_FILE="$PROJECT_ROOT/config/settings.json"

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
info()  { echo "[INFO]  $*"; }
ok()    { echo "[OK]    $*"; }
warn()  { echo "[WARN]  $*"; }
die()   { echo "[ERROR] $*" >&2; exit 1; }

require_cmd() { command -v "$1" &>/dev/null || die "Required command not found: $1"; }

read_setting() {
    # read_setting <key> — extracts a top-level string value from settings.json
    python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    d = json.load(f)
print(d.get('$1', ''))
" 2>/dev/null
}

# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
do_export() {
    local output_dir="${1:-$PROJECT_ROOT}"
    require_cmd tar
    require_cmd python3

    local timestamp; timestamp="$(date '+%Y%m%d-%H%M%S')"
    local archive_name="aegis-export-${timestamp}.tar.gz"
    local staging; staging="$(mktemp -d)"
    local bundle="$staging/aegis-export"
    mkdir -p "$bundle"

    info "Staging export to $staging ..."

    # settings.json
    if [[ -f "$SETTINGS_FILE" ]]; then
        cp "$SETTINGS_FILE" "$bundle/settings.json"
        ok "settings.json"
    else
        warn "settings.json not found — skipping"
    fi

    # users.json + groups.json
    for f in users.json groups.json; do
        if [[ -f "$CONFIG_DIR/$f" ]]; then
            cp "$CONFIG_DIR/$f" "$bundle/$f"
            ok "$f"
        else
            warn "$CONFIG_DIR/$f not found — skipping"
        fi
    done

    # blueprints/
    local bp_root; bp_root="$(read_setting blueprints_root)"
    [[ -z "$bp_root" ]] && bp_root="$PROJECT_ROOT/blueprints"
    if [[ -d "$bp_root" ]]; then
        cp -r "$bp_root" "$bundle/blueprints"
        ok "blueprints/ ($(find "$bundle/blueprints" -type f | wc -l) files)"
    else
        warn "blueprints dir not found at $bp_root — skipping"
    fi

    # workspace (archive documents)
    local workspace; workspace="$(read_setting workspace_base)"
    if [[ -n "$workspace" && -d "$workspace" ]]; then
        cp -r "$workspace" "$bundle/workspace"
        ok "workspace/ $workspace ($(find "$bundle/workspace" -type f | wc -l) files)"
    else
        warn "workspace_base not set or directory not found — skipping"
    fi

    # manifest
    cat > "$bundle/manifest.json" <<MANIFEST
{
    "exported_at": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "settings_file": "$SETTINGS_FILE",
    "config_dir": "$CONFIG_DIR",
    "blueprints_root": "${bp_root}",
    "workspace_base": "${workspace}"
}
MANIFEST

    # pack
    local output_path="$output_dir/$archive_name"
    tar -czf "$output_path" -C "$staging" aegis-export
    rm -rf "$staging"

    ok "Archive created: $output_path"
    info "Size: $(du -sh "$output_path" | cut -f1)"
}

# --------------------------------------------------------------------------- #
# import
# --------------------------------------------------------------------------- #
do_import() {
    local archive="${1:-}"
    [[ -z "$archive" ]] && die "Usage: $0 import <archive.tar.gz>"
    [[ -f "$archive" ]]  || die "File not found: $archive"
    require_cmd tar
    require_cmd python3

    local staging; staging="$(mktemp -d)"
    info "Extracting $archive ..."
    tar -xzf "$archive" -C "$staging"

    local bundle="$staging/aegis-export"
    [[ -d "$bundle" ]] || die "Invalid archive: missing aegis-export/ directory"

    # show manifest
    if [[ -f "$bundle/manifest.json" ]]; then
        info "Archive manifest:"
        cat "$bundle/manifest.json"
        echo
    fi

    # settings.json
    if [[ -f "$bundle/settings.json" ]]; then
        mkdir -p "$PROJECT_ROOT/config"
        cp "$bundle/settings.json" "$SETTINGS_FILE"
        ok "settings.json restored"
    fi

    # users.json + groups.json
    mkdir -p "$CONFIG_DIR"
    for f in users.json groups.json; do
        if [[ -f "$bundle/$f" ]]; then
            cp "$bundle/$f" "$CONFIG_DIR/$f"
            ok "$f restored to $CONFIG_DIR/"
        fi
    done

    # blueprints/
    if [[ -d "$bundle/blueprints" ]]; then
        local bp_dest; bp_dest="$(read_setting blueprints_root)"
        [[ -z "$bp_dest" ]] && bp_dest="$PROJECT_ROOT/blueprints"
        read -r -p "[INPUT] Restore blueprints to [$bp_dest]: " bp_input
        [[ -n "$bp_input" ]] && bp_dest="$bp_input"
        mkdir -p "$bp_dest"
        cp -r "$bundle/blueprints/." "$bp_dest/"
        ok "blueprints/ restored to $bp_dest"
    fi

    # workspace
    if [[ -d "$bundle/workspace" ]]; then
        local ws_dest; ws_dest="$(read_setting workspace_base)"
        read -r -p "[INPUT] Restore workspace to [$ws_dest]: " ws_input
        [[ -n "$ws_input" ]] && ws_dest="$ws_input"
        if [[ -z "$ws_dest" ]]; then
            ws_dest="$HOME/sc-archive"
            warn "No workspace_base configured — defaulting to $ws_dest"
        fi
        mkdir -p "$ws_dest"
        cp -r "$bundle/workspace/." "$ws_dest/"
        ok "workspace/ restored to $ws_dest"

        # update settings.json with new path if changed
        if [[ "$ws_dest" != "$(read_setting workspace_base)" ]]; then
            python3 - "$SETTINGS_FILE" "$ws_dest" <<'PYEOF'
import json, sys
path = sys.argv[1]
new_ws = sys.argv[2]
with open(path) as f:
    d = json.load(f)
d["workspace_base"] = new_ws
with open(path, "w") as f:
    json.dump(d, f, indent=4)
PYEOF
            ok "settings.json updated: workspace_base = $ws_dest"
        fi
    fi

    rm -rf "$staging"
    ok "Import complete."
    info "Start the application with: ./bin/launch.sh"
}

# --------------------------------------------------------------------------- #
# entrypoint
# --------------------------------------------------------------------------- #
case "${1:-}" in
    export) do_export "${2:-}" ;;
    import) do_import "${2:-}" ;;
    *)
        echo "Usage:"
        echo "  $0 export [output_dir]     — create migration archive"
        echo "  $0 import <archive.tar.gz> — restore from archive"
        exit 1
        ;;
esac
