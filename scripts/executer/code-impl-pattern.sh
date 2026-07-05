#!/usr/bin/env bash
# Orchestrates the lifecycle (install, build, metrics, run, collect) for a target.
ACTION=$1
TARGET_DIR=$2

cd "$TARGET_DIR"

# Helper to execute a hook only if it exists in metadata AND is not empty
execute_hook() {
    local hook_name=$1
    HOOK_CMD=$(python3 -c "import json; print(json.load(open('metadata.json')).get('hooks', {}).get('$hook_name', ''))")
    
    if [[ -n "$HOOK_CMD" && "$HOOK_CMD" != "None" ]]; then
        echo "-> Executing hook: $hook_name..."
        eval "$HOOK_CMD"
    fi
}

# Lifecycle handling
case "$ACTION" in
    "run")
        execute_hook "install"
        execute_hook "build"
        
        # 1. Metrics & Performance
        "$OLDPWD/scripts/metrics.sh"
        RUN_CMD=$(python3 -c "import json; print(json.load(open('metadata.json'))['run_cmd'])")
        "$OLDPWD/scripts/hyperfine-run.sh" "$RUN_CMD" "$TARGET_DIR"
        
        # 2. Automatically collect to root report after run
        # We go back to project root to run the collector
        cd "$OLDPWD" && ./scripts/collect.sh
        
        # 3. Clean up implementation-specific artifacts
        cd "$TARGET_DIR"
        execute_hook "clean"
        ;;
    "metrics")
        "$OLDPWD/scripts/metrics.sh"
        ;;
    "collect")
        # Direct call to trigger global collection
        cd "$OLDPWD" && ./scripts/collect.sh
        ;;
esac
