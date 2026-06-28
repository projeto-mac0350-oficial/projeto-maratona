#!/usr/bin/env bash
#
# Collect backend code metrics and print a Markdown report on stdout.
#
#   radon  -> cyclomatic complexity (cc), maintainability index (mi),
#             raw metrics (raw) and Halstead (hal)
#   pylint -> a 0-10 quality score
#
# Usage:
#   bash scripts/metrics.sh [target_dir]            # default target: backend
#   bash scripts/metrics.sh backend > report.md     # save a report for the wiki
#
# The virtualenv and __pycache__ are always excluded.
set -uo pipefail

TARGET="${1:-backend}"
EXCLUDE='*/venv/*,*/__pycache__/*'

# Python files under the target, skipping the virtualenv and caches.
mapfile -t PYFILES < <(find "$TARGET" -name '*.py' \
    -not -path '*/venv/*' -not -path '*/__pycache__/*' | sort)

echo "# Code metrics — \`$TARGET\`"
echo
echo "_Generated $(date -u +'%Y-%m-%d %H:%M UTC')_ · Python files analysed: ${#PYFILES[@]}_"
echo
echo "Collected with **radon** (complexity & maintainability) and **pylint** (quality score)."
echo

echo "## Cyclomatic complexity — \`radon cc -s -a\`"
echo "Lower is simpler. Each block is graded A (best) to F; the average is at the end."
echo '```'
radon cc "$TARGET" -s -a -e "$EXCLUDE"
echo '```'
echo

echo "## Maintainability index — \`radon mi -s\`"
echo "0-100, higher is more maintainable. A = very maintainable, C = hard to maintain."
echo '```'
radon mi "$TARGET" -s -e "$EXCLUDE"
echo '```'
echo

echo "## Raw metrics — \`radon raw -s\`"
echo "Lines of code (LOC), logical (LLOC) and source (SLOC) lines, comments, blanks."
echo '```'
radon raw "$TARGET" -s -e "$EXCLUDE"
echo '```'
echo

echo "## Halstead complexity — \`radon hal\`"
echo "Volume / difficulty / effort derived from operators and operands."
echo '```'
radon hal "$TARGET" -e "$EXCLUDE"
echo '```'
echo

echo "## Quality score — \`pylint\`"
echo "Static analysis with a final score \"rated at X/10\"."
echo '```'
if [ "${#PYFILES[@]}" -gt 0 ]; then
    pylint "${PYFILES[@]}" --exit-zero
else
    echo "no Python files found under $TARGET"
fi
echo '```'
