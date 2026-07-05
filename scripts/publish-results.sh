#!/usr/bin/env bash
# Publishes benchmark artifacts and generated reports to the benchmark-results branch.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGETS_FILE="${1:-}"
RESULTS_BRANCH="${RESULTS_BRANCH:-benchmark-results}"
SOURCE_SHA="$(git rev-parse HEAD)"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ -z "$TARGETS_FILE" ] || [ ! -f "$TARGETS_FILE" ]; then
    echo "Usage: publish-results.sh <targets-file>" >&2
    exit 1
fi

STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT

while IFS= read -r target; do
    [ -z "$target" ] && continue
    if [ ! -d "$target/artifacts" ]; then
        continue
    fi

    dest="$STAGING/published/$target/artifacts"
    mkdir -p "$dest"
    cp -a "$target/artifacts/." "$dest/"
done < "$TARGETS_FILE"

cat > "$STAGING/manifest.json" <<EOF
{
  "generated_at": "$TIMESTAMP",
  "source_commit": "$SOURCE_SHA",
  "results_branch": "$RESULTS_BRANCH"
}
EOF

git config user.name "${GIT_AUTHOR_NAME:-github-actions[bot]}"
git config user.email "${GIT_AUTHOR_EMAIL:-github-actions[bot]@users.noreply.github.com}"

WORKTREE="$(mktemp -d)"
trap 'git worktree remove --force "$WORKTREE" 2>/dev/null || true; rm -rf "$STAGING"' EXIT

if git show-ref --verify --quiet "refs/remotes/origin/$RESULTS_BRANCH"; then
    git fetch origin "$RESULTS_BRANCH"
    git worktree add "$WORKTREE" "$RESULTS_BRANCH"
elif git show-ref --verify --quiet "refs/heads/$RESULTS_BRANCH"; then
    git worktree add "$WORKTREE" "$RESULTS_BRANCH"
else
    git worktree add -B "$RESULTS_BRANCH" "$WORKTREE" HEAD
    find "$WORKTREE" -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +
fi

rsync -a "$STAGING/" "$WORKTREE/"

cd "$WORKTREE"
BENCHMARK_ROOT="$WORKTREE" python3 "$ROOT/scripts/generate-reports.py"

git add -f manifest.json
[ -d reports ] && git add -f reports
[ -d published ] && git add -f published

if git diff --cached --quiet; then
    echo "No benchmark result changes to publish."
    exit 0
fi

git commit -m "$(cat <<EOF
Update benchmark results ($TIMESTAMP)

Source commit: $SOURCE_SHA
EOF
)"

git push origin "$RESULTS_BRANCH"

echo "✔ Published benchmark results to $RESULTS_BRANCH"
