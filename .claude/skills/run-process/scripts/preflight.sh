#!/usr/bin/env bash
# Usage: preflight.sh <run-id> --scope <slug>
#   e.g. bash .claude/skills/run-process/scripts/preflight.sh 2.4 --scope studio-v1
# Run from the repository root. Non-interactive: prints OK / NOTE / WARN / FAIL lines.
# Exits 1 on FAIL. WARN lines (including the soft gate) are for the agent to put to the user.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Arguments --------------------------------------------------------------
RUN=""
SCOPE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --scope)
      SCOPE="${2:-}"
      [ -n "$SCOPE" ] || { echo "FAIL: --scope requires a slug."; exit 1; }
      shift 2 ;;
    --scope=*) SCOPE="${1#--scope=}"; shift ;;
    -h|--help) echo "Usage: $0 <run-id> --scope <slug>"; exit 0 ;;
    *)
      [ -z "$RUN" ] || { echo "FAIL: unexpected argument '$1'"; exit 1; }
      RUN="$1"; shift ;;
  esac
done

if [ -z "$RUN" ]; then
  echo "Usage: $0 <run-id> --scope <slug>   (e.g. $0 2.4 --scope studio-v1)"
  exit 1
fi

# Infer the scope from a worktree-<slug> branch when not given.
if [ -z "$SCOPE" ]; then
  BR=$(git branch --show-current 2>/dev/null || true)
  case "$BR" in
    worktree-*) SCOPE="${BR#worktree-}"; echo "NOTE: scope inferred from branch $BR" ;;
  esac
fi
if [ -z "$SCOPE" ]; then
  echo "FAIL: no quest scope. Pass --scope <slug> (every run belongs to a quest under sidequests/)."
  exit 1
fi

SCOPE_ROOT="sidequests/${SCOPE}"
if [ ! -d "$SCOPE_ROOT" ]; then
  if [ -d "sidequests/archive/${SCOPE}" ]; then
    echo "FAIL: quest '$SCOPE' is archived. Reopen it first: /sidequest reopen $SCOPE"
  else
    echo "FAIL: quest '$SCOPE' not found at $SCOPE_ROOT/. Open it first: /sidequest open"
  fi
  exit 1
fi
ROLLOUT_FILE="${SCOPE_ROOT}/${SCOPE}-rollout.md"
[ -f "$ROLLOUT_FILE" ] || { echo "FAIL: quest rollout missing: $ROLLOUT_FILE"; exit 1; }
STATUS_DIR="${SCOPE_ROOT}/status"
STATUS_FILE="${STATUS_DIR}/run${RUN}status.md"
echo "=== Pre-flight: Run $RUN (quest: $SCOPE) ==="

# 0. Worktree alignment — a quest that declares a worktree commits on worktree-<slug>.
DECLARED_WT=$(sed -n 's/^worktree:[[:space:]]*//p' "$ROLLOUT_FILE" | head -1 | tr -d '[:space:]')
if [ -n "$DECLARED_WT" ]; then
  CUR_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  if [ "$CUR_BRANCH" = "worktree-${SCOPE}" ]; then
    echo "OK: in the quest's worktree (branch $CUR_BRANCH)"
  else
    echo "WARN: quest '$SCOPE' declares a worktree ($DECLARED_WT, branch worktree-${SCOPE}),"
    echo "      but you're on '$CUR_BRANCH'. This run's commits would land here, not in the worktree."
    echo "      Open Claude Code against $DECLARED_WT/, or confirm you intend to commit on '$CUR_BRANCH'."
  fi
fi

# 1. Working tree clean? Commits go through /commit, so pre-flight never commits.
if [ -n "$(git status --porcelain)" ]; then
  echo "FAIL: working tree is dirty:"
  git status --short
  echo "      Commit it with /commit (or stash) before starting run $RUN."
  exit 1
fi
echo "OK: working tree clean"

# 2. Prior run's status report exists?
#    The prior run is the `Run <id>` heading just before this one in the rollout, so the first run
#    of a milestone finds the last run of the previous milestone (3.1 -> 2.4). A run the rollout does not list
#    falls back to decrementing the minor (2.4 -> 2.3); the first run skips the check.
PRIOR_RUN=""
LISTED=$(sed -n -E 's/^#{2,4} Run ([A-Za-z0-9.]+).*/\1/p' "$ROLLOUT_FILE" | sed -E 's/\.$//' || true)
if printf '%s\n' "$LISTED" | grep -xF -- "$RUN" >/dev/null; then
  PRIOR_RUN=$(printf '%s\n' "$LISTED" | awk -v run="$RUN" '$0 == run { print prev; exit } { prev = $0 }')
else
  echo "WARN: no '### Run $RUN' heading in $ROLLOUT_FILE — check the run ID."
  if [[ "$RUN" =~ ^([0-9]+)\.([0-9]+)$ ]] && [ "${BASH_REMATCH[2]}" -gt 1 ]; then
    PRIOR_RUN="${BASH_REMATCH[1]}.$((BASH_REMATCH[2] - 1))"
  fi
fi
if [ -z "$PRIOR_RUN" ]; then
  echo "NOTE: prior-run check skipped (first run of the quest)."
elif [ -f "${STATUS_DIR}/run${PRIOR_RUN}status.md" ]; then
  echo "OK: prior run status found (${STATUS_DIR}/run${PRIOR_RUN}status.md)"
else
  echo "WARN: prior run status not found at ${STATUS_DIR}/run${PRIOR_RUN}status.md"
  echo "      Either run ${PRIOR_RUN} is not complete, or this run starts an independent branch of the graph."
fi

# 2b. Carry-forward ledger — print the routed handoffs this run inherits.
#     Live lines: `- [<from-run>] -> <targets> | <class> | <conclusion>`. Folded residues start
#     with `~` and never match. Printed: lines whose targets include this run, `surface` or `quest`.
LEDGER="${STATUS_DIR}/carry-forward.md"
if [ -f "$LEDGER" ]; then
  TOTAL=$(grep -cE '^- \[.*\] -> ' "$LEDGER" 2>/dev/null || true)
  TOTAL=${TOTAL:-0}
  if [ "$TOTAL" -gt 15 ]; then
    echo "WARN: carry-forward live band holds ${TOTAL} entries (>15) — a fold pass is overdue."
  fi
  MATCHED=$(awk -v run="$RUN" '
    /^- \[.*\] -> / {
      hdr = $0
      sub(/^- \[[^]]*\] -> */, "", hdr)   # drop "- [from] -> "
      sub(/ *\|.*$/, "", hdr)             # keep the target list
      n = split(hdr, t, /,/)
      for (i = 1; i <= n; i++) {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", t[i])
        if (t[i] == run || t[i] == "surface" || t[i] == "quest") { print; next }
      }
    }
  ' "$LEDGER")
  if [ -n "$MATCHED" ]; then
    COUNT=$(printf "%s\n" "$MATCHED" | grep -c '^-' || true)
    echo ""
    echo "-- Carry-forward for run $RUN (${COUNT} of ${TOTAL} ledger entries) --"
    printf "%s\n" "$MATCHED" | sed 's/^/  /'
    echo "  ^ inherited context — read before planning."
    echo ""
  else
    echo "NOTE: carry-forward ledger present, no entries routed to run $RUN."
  fi
else
  echo "NOTE: no carry-forward ledger at $LEDGER yet."
fi

# 3. Re-run?
if [ -f "$STATUS_FILE" ]; then
  echo "WARN: $STATUS_FILE already exists — is this a re-run?"
fi

# 4. Up to date with origin/main?
echo "Branch: $(git branch --show-current)"
git fetch origin main --quiet 2>/dev/null || true
BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo "?")
if [ "$BEHIND" = "?" ]; then
  echo "WARN: could not compare with origin/main (no remote?)"
elif [ "$BEHIND" -gt 0 ]; then
  echo "WARN: $BEHIND commit(s) behind origin/main — consider rebasing"
else
  echo "OK: up to date with origin/main"
fi

# 5. Soft integration gate — done-but-unintegrated quests spawned by this one (parent: <scope>; see soft_gate.py).
#    Never skipped silently: a gate that cannot run says so.
PY="${PYTHON:-python3}"
if PENDING=$("$PY" -I "$SCRIPT_DIR/soft_gate.py" --scope "$SCOPE"); then
  if [ -n "$PENDING" ]; then
    echo ""
    echo "WARN: done-but-unintegrated quests are in scope:"
    printf "%s\n" "$PENDING"
    echo "      For each, satisfy the type-specific condition, then set 'integrated: true' in its"
    echo "      rollout frontmatter. ASK THE USER whether to continue with run $RUN anyway."
  else
    echo "OK: soft integration gate — nothing pending"
  fi
else
  echo "WARN: soft integration gate could not run ($PY or soft_gate.py failed) — gate SKIPPED."
fi

echo ""
echo "Pre-flight complete. Read $ROLLOUT_FILE next."
