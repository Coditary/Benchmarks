#!/usr/bin/env bash
# Main entry point for the benchmark suite.
set -e

# --- Colors and Styles ---
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[36m"
MAGENTA="\033[35m"
DIM="\033[2m"

ACTION=${1:-"run"}
FILTER=${2:-""}

# Print Header
clear
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║              ⚡ CODE-IMPL-PATTERN BENCHMARK SUITE ⚡             ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════════╝${RESET}"
echo -e "  ${BOLD}Action:${RESET} ${MAGENTA}${ACTION^^}${RESET} | ${BOLD}Scope:${RESET} ${DIM}benchmarks/${FILTER:-"all"}${RESET}\n"

find "benchmarks/$FILTER" -mindepth 1 -maxdepth 4 -name "metadata.json" | sort | while read -r meta_path; do
    TARGET_DIR=$(dirname "$meta_path")
    
    # Extract hierarchy for styling
    DOMAIN=$(echo "$TARGET_DIR" | cut -d'/' -f2)
    TASK=$(echo "$TARGET_DIR" | cut -d'/' -f3)
    
    echo -e "${BOLD}${CYAN}◈ Domain:${RESET} $DOMAIN ${DIM}❯${RESET} ${BOLD}${MAGENTA}Task:${RESET} $TASK"
    echo -e "  ${DIM}└─ Target:${RESET} ${BOLD}$TARGET_DIR${RESET}"
    
    # Delegate to PatternExecutor
    "./scripts/executer/code-impl-pattern.sh" "$ACTION" "$TARGET_DIR"

    echo -e "${DIM}──────────────────────────────────────────────────────────────────${RESET}"
done

echo -e "\n${BOLD}${CYAN}✔ All tasks completed successfully.${RESET}\n"
