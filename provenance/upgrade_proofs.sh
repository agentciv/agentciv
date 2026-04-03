#!/bin/bash
# Run this ~2 hours after stamping to upgrade pending proofs to full Bitcoin proofs.
# After upgrading, the .ots files are fully self-contained and don't need
# calendar servers to verify — they verify directly against Bitcoin.
#
# Usage: ./provenance/upgrade_proofs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UPGRADED=0

echo "Upgrading pending attestations to full Bitcoin proofs..."
echo ""

for f in "$SCRIPT_DIR"/*.ots; do
    [ -f "$f" ] || continue
    echo "  $(basename "$f")..."
    if ots upgrade "$f" 2>&1 | grep -q "Timestamp complete"; then
        echo "    -> upgraded to full Bitcoin proof"
        UPGRADED=$((UPGRADED + 1))
    else
        echo "    -> still pending (try again later)"
    fi
done

echo ""
if [ $UPGRADED -gt 0 ]; then
    echo "$UPGRADED proof(s) upgraded. Commit the updated .ots files:"
    echo "  git add provenance/*.ots && git commit -m 'Upgrade proofs to full Bitcoin attestations' && git push"
else
    echo "No proofs ready yet. Bitcoin confirmation typically takes 1-2 hours."
    echo "Run this script again later."
fi
