#!/usr/bin/env bash
# Orchestrates the lifecycle (install, build, metrics, run, collect) for a target.
ACTION=$1
TARGET_DIR=$2

cd "$TARGET_DIR"
TARGET_DIR="$(pwd)"

execute_hook() {
    local hook_name=$1
    HOOK_CMD=$(python3 -c "import json; print(json.load(open('metadata.json')).get('hooks', {}).get('$hook_name', ''))")

    if [[ -n "$HOOK_CMD" && "$HOOK_CMD" != "None" ]]; then
        echo "-> Executing hook: $hook_name..."
        eval "$HOOK_CMD"
    fi
}

case "$ACTION" in
    "run")
        execute_hook "install"
        execute_hook "build"

        "$OLDPWD/scripts/metrics.sh"
        RUN_CMD=$(python3 -c "import json; print(json.load(open('metadata.json'))['run_cmd'])")
        "$OLDPWD/scripts/hyperfine-run.sh" "$RUN_CMD"

        python3 "$OLDPWD/scripts/collect.py" "$TARGET_DIR"

        if [ "${CI:-}" != "true" ]; then
            execute_hook "clean"
        fi
        ;;
    "metrics")
        "$OLDPWD/scripts/metrics.sh"
        ;;
    "collect")
        python3 "$OLDPWD/scripts/collect.py" "$TARGET_DIR"
        ;;
esac
