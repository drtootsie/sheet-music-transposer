#!/bin/bash
# Progress checker for OCR processes

echo "======================================"
echo "Sheet Music OCR Progress Monitor"
echo "======================================"
echo

# Count running processes
RUNNING=$(ps aux | grep "oemer" | grep -v grep | wc -l)
echo "Running OCR processes: $RUNNING"

# Count completed files
COMPLETED=$(ls -1 /tmp/well_soul_musicxml/page_*/page_*.musicxml 2>/dev/null | wc -l)
TOTAL=11  # Pages 2-12
echo "Completed pages: $COMPLETED / $TOTAL"

# Calculate progress
if [ $TOTAL -gt 0 ]; then
    PERCENT=$((COMPLETED * 100 / TOTAL))
    echo "Progress: $PERCENT%"
fi

echo
echo "Detailed status:"
echo "----------------------------------------"

for i in $(seq -f "%02g" 2 12); do
    PAGE_NUM=$(echo $i | sed 's/^0*//')
    XML_FILE="/tmp/well_soul_musicxml/page_$i/page_$i.musicxml"
    LOG_FILE="/tmp/well_soul_musicxml/page_$i.log"

    if [ -f "$XML_FILE" ]; then
        SIZE=$(ls -lh "$XML_FILE" | awk '{print $5}')
        echo "✓ Page $PAGE_NUM - Complete ($SIZE)"
    elif ps aux | grep "page_$i.png" | grep -v grep > /dev/null; then
        if [ -f "$LOG_FILE" ]; then
            LAST_LINE=$(tail -1 "$LOG_FILE" 2>/dev/null)
            echo "⏳ Page $PAGE_NUM - Processing... ($LAST_LINE)"
        else
            echo "⏳ Page $PAGE_NUM - Starting..."
        fi
    else
        echo "⏸ Page $PAGE_NUM - Waiting..."
    fi
done

echo "========================================="
echo

if [ $COMPLETED -eq $TOTAL ]; then
    echo "🎉 All pages completed!"
    echo
    echo "Next steps:"
    echo "  1. Combine pages: python3 /tmp/transpose_key_change.py"
    echo "  2. Export to PDF"
else
    # Estimate remaining time
    if [ $COMPLETED -gt 0 ]; then
        REMAINING=$((TOTAL - COMPLETED))
        EST_MINUTES=$((REMAINING * 12))
        echo "Estimated time remaining: ~$EST_MINUTES minutes"
    fi
fi
