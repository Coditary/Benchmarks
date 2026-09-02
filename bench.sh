#!/usr/bin/env bash
# Main entry point for the benchmark suite.
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# --- Colors and Styles ---
RESET="\033[0m"
BOLD="\033[1m"
CYAN="\033[36m"
MAGENTA="\033[35m"
DIM="\033[2m"
GREEN="\033[32m"

ACTION=${1:-"run"}
FILTER=${2:-""}

print_header() {
    if [ -t 1 ]; then
        clear
    fi
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║              ⚡ CODE-IMPL-PATTERN BENCHMARK SUITE ⚡             ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════════╝${RESET}"
    echo -e "  ${BOLD}Action:${RESET} ${MAGENTA}${ACTION^^}${RESET} | ${BOLD}Scope:${RESET} ${DIM}benchmarks/${FILTER:-"all"}${RESET}\n"
}

if [ "$ACTION" = "clean" ]; then
    print_header
    echo -e "${BOLD}${CYAN}-> Cleaning build artifacts via per-task clean hooks...${RESET}\n"
fi

if [ "$ACTION" = "reports" ]; then
    print_header

    if [ -n "$FILTER" ]; then
        echo -e "${BOLD}${CYAN}-> Generating reports incrementally for:${RESET} ${BOLD}benchmarks/$FILTER${RESET}\n"
        python3 scripts/generate-reports.py "$FILTER"
    else
        echo -e "${BOLD}${CYAN}-> Generating reports for all tasks...${RESET}\n"
        python3 scripts/generate-reports.py
    fi

    echo -e "\n${BOLD}${GREEN}✔ Report generation completed.${RESET}"
    if [ -n "$FILTER" ]; then
        echo -e "${DIM}Open reports/$FILTER/index.html${RESET}\n"
    else
        echo -e "${DIM}Open reports/index.html${RESET}\n"
    fi
    exit 0
fi

print_header

SEARCH_ROOT="benchmarks"
if [ -n "$FILTER" ]; then
    SEARCH_ROOT="benchmarks/$FILTER"
fi

find "$SEARCH_ROOT" -name "metadata.json" | sort | while read -r meta_path; do
    TARGET_DIR=$(dirname "$meta_path")

    DOMAIN=$(echo "$TARGET_DIR" | cut -d'/' -f2)
    TASK=$(echo "$TARGET_DIR" | cut -d'/' -f3)

    echo -e "${BOLD}${CYAN}◈ Domain:${RESET} $DOMAIN ${DIM}❯${RESET} ${BOLD}${MAGENTA}Task:${RESET} $TASK"
    echo -e "  ${DIM}└─ Target:${RESET} ${BOLD}$TARGET_DIR${RESET}"

    if [ "$ACTION" = "clean" ]; then
        "./scripts/executer/code-impl-pattern.sh" "$ACTION" "$TARGET_DIR" || true
    else
        "./scripts/executer/code-impl-pattern.sh" "$ACTION" "$TARGET_DIR"
    fi

    echo -e "${DIM}──────────────────────────────────────────────────────────────────${RESET}"
done

if [ "$ACTION" = "clean" ]; then
    echo -e "\n${BOLD}${CYAN}-> Cleaning repo-root build caches...${RESET}\n"
    bash "./scripts/clean-repo-build-caches.sh"
    echo -e "\n${BOLD}${GREEN}✔ Build artifacts cleaned.${RESET}"
    echo -e "${DIM}Source code, datasets, and benchmark results were not touched.${RESET}\n"
    exit 0
fi

echo -e "\n${BOLD}${CYAN}✔ All tasks completed successfully.${RESET}\n"
