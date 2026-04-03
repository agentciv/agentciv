#!/bin/bash
# Usage: ./provenance/stamp.sh [optional tag name]
#
# Stamps the current HEAD commit on the Bitcoin blockchain via OpenTimestamps.
# Optionally creates an annotated git tag for the milestone.
#
# Examples:
#   ./provenance/stamp.sh                     # stamp current commit
#   ./provenance/stamp.sh v1.0-release        # stamp + tag as v1.0-release
#   ./provenance/stamp.sh paper-5-submitted   # stamp + tag for paper submission

set -euo pipefail

COMMIT=$(git rev-parse HEAD)
SHORT=$(git rev-parse --short HEAD)
DATE=$(date +%Y-%m-%d)

echo "Stamping commit $SHORT ($DATE)..."

# Create temp file with commit hash
TMPFILE=$(mktemp)
echo -n "$COMMIT" > "$TMPFILE"

# Submit to OpenTimestamps
ots stamp "$TMPFILE"

# Move proof to provenance directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mv "${TMPFILE}.ots" "${SCRIPT_DIR}/commit_${SHORT}.ots"
rm -f "$TMPFILE"

echo "Proof saved: provenance/commit_${SHORT}.ots"

# Optional: create annotated tag
if [ "${1:-}" != "" ]; then
    git tag -a "$1" -m "Provenance milestone: $1 ($DATE, commit $SHORT)"
    echo "Tag created: $1"
fi

echo ""
echo "Done. Commit $SHORT submitted to 4 Bitcoin calendar servers."
echo "Proof will be confirmed in ~1-2 hours."
echo ""
echo "To verify later:"
echo "  echo -n '$COMMIT' > /tmp/h.txt && ots verify ${SCRIPT_DIR}/commit_${SHORT}.ots -f /tmp/h.txt"
