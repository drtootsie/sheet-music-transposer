#!/bin/bash
#
# Sheet Music Key Change Removal Workflow
# Removes key change from "It Is Well With My Soul" (F minor to F# major -> All F minor)
#
# This script automates the process of:
# 1. Converting PDF to images
# 2. Running OCR on each page to extract MusicXML
# 3. Combining all pages into one score
# 4. Transposing measures 20+ down by a semitone
# 5. Exporting back to PDF
#

set -e  # Exit on error

# Configuration
PDF_INPUT="$1"
OUTPUT_DIR="${2:-./output}"
KEY_CHANGE_MEASURE=20  # Measure where key change occurs
TRANSPOSE_INTERVAL="-m2"  # Down a minor 2nd (semitone)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Sheet Music Transposition Workflow${NC}"
echo -e "${GREEN}====================================${NC}"
echo

# Check arguments
if [ -z "$PDF_INPUT" ]; then
    echo -e "${RED}Usage: $0 <input.pdf> [output_directory]${NC}"
    echo
    echo "Example:"
    echo "  $0 'well_soul.pdf' ./output"
    exit 1
fi

if [ ! -f "$PDF_INPUT" ]; then
    echo -e "${RED}Error: File not found: $PDF_INPUT${NC}"
    exit 1
fi

# Create output directories
mkdir -p "$OUTPUT_DIR/pages"
mkdir -p "$OUTPUT_DIR/musicxml"
mkdir -p "$OUTPUT_DIR/logs"

echo -e "${YELLOW}Step 1: Converting PDF to images...${NC}"
python3 << EOF
from pdf2image import convert_from_path
import os

pdf_path = "$PDF_INPUT"
output_folder = "$OUTPUT_DIR/pages"

print(f"Converting {pdf_path}...")
images = convert_from_path(pdf_path, dpi=300)

for i, image in enumerate(images):
    image_path = os.path.join(output_folder, f'page_{i+1:02d}.png')
    image.save(image_path, 'PNG')
    print(f'  Saved page {i+1}')

print(f'Total pages converted: {len(images)}')
EOF

echo -e "${GREEN}✓ PDF converted to images${NC}"
echo

# Count pages (excluding cover page)
TOTAL_PAGES=$(ls -1 "$OUTPUT_DIR/pages"/*.png 2>/dev/null | wc -l)
MUSIC_PAGES=$((TOTAL_PAGES - 1))  # Exclude cover page

echo -e "${YELLOW}Step 2: Running OCR on $MUSIC_PAGES music pages...${NC}"
echo -e "${YELLOW}This will take approximately 10-15 minutes per page${NC}"
echo -e "${YELLOW}Estimated total time: $((MUSIC_PAGES * 12)) minutes${NC}"
echo

# Create subdirectories for each page
for i in $(seq -f "%02g" 2 $TOTAL_PAGES); do
    mkdir -p "$OUTPUT_DIR/musicxml/page_$i"
done

# Process each page (starting from page 2, skipping cover)
for i in $(seq -f "%02g" 2 $TOTAL_PAGES); do
    PAGE_NUM=$(echo $i | sed 's/^0*//')
    echo "Processing page $PAGE_NUM..."

    oemer "$OUTPUT_DIR/pages/page_$i.png" \
        -o "$OUTPUT_DIR/musicxml/page_$i" \
        > "$OUTPUT_DIR/logs/page_$i.log" 2>&1 &

    # Stagger the starts slightly to avoid overwhelming the system
    sleep 10
done

echo "All OCR processes started. Waiting for completion..."
wait  # Wait for all background jobs to finish

echo -e "${GREEN}✓ OCR completed${NC}"
echo

echo -e "${YELLOW}Step 3: Combining MusicXML pages...${NC}"
python3 << 'EOF'
import sys
sys.path.insert(0, '/tmp/music_env/lib/python3.12/site-packages')

from music21 import converter, stream
import os
import glob

musicxml_dir = "$OUTPUT_DIR/musicxml"
output_file = "$OUTPUT_DIR/combined_score.musicxml"

# Find all MusicXML files
xml_files = sorted(glob.glob(f"{musicxml_dir}/page_*/page_*.musicxml"))

if not xml_files:
    print("Error: No MusicXML files found!")
    sys.exit(1)

print(f"Found {len(xml_files)} MusicXML files")

# Load first page as base
print(f"Loading {xml_files[0]}...")
combined = converter.parse(xml_files[0])

# Append remaining pages
for xml_file in xml_files[1:]:
    print(f"Adding {xml_file}...")
    score = converter.parse(xml_file)

    # Append measures from each part
    for part_idx, part in enumerate(score.parts):
        if part_idx < len(combined.parts):
            for measure in part.getElementsByClass('Measure'):
                combined.parts[part_idx].append(measure)

print(f"Saving combined score to {output_file}...")
combined.write('musicxml', fp=output_file)
print("Done!")
EOF

echo -e "${GREEN}✓ Pages combined${NC}"
echo

echo -e "${YELLOW}Step 4: Transposing measures $KEY_CHANGE_MEASURE onwards...${NC}"
python3 << 'EOF'
import sys
sys.path.insert(0, '/tmp/music_env/lib/python3.12/site-packages')

from music21 import converter, interval

input_file = "$OUTPUT_DIR/combined_score.musicxml"
output_file = "$OUTPUT_DIR/transposed_score.musicxml"
start_measure = $KEY_CHANGE_MEASURE

print(f"Loading {input_file}...")
score = converter.parse(input_file)

# Create interval for transposition
transpose_interval = interval.Interval('$TRANSPOSE_INTERVAL')

# Process each part
for part_idx, part in enumerate(score.parts):
    print(f"Processing part {part_idx + 1}...")

    measures = part.getElementsByClass('Measure')
    transposed_count = 0

    for measure in measures:
        if measure.number >= start_measure:
            # Transpose all notes and chords
            for element in measure.recurse():
                if 'Note' in element.classes or 'Chord' in element.classes:
                    element.transpose(transpose_interval, inPlace=True)

            # Update key signature if present
            for ks in measure.getElementsByClass('KeySignature'):
                ks.transpose(transpose_interval, inPlace=True)

            transposed_count += 1

    print(f"  Transposed {transposed_count} measures")

print(f"Saving to {output_file}...")
score.write('musicxml', fp=output_file)
print("Done!")
EOF

echo -e "${GREEN}✓ Transposition completed${NC}"
echo

echo -e "${YELLOW}Step 5: Exporting to PDF...${NC}"
musescore3 "$OUTPUT_DIR/transposed_score.musicxml" \
    -o "$OUTPUT_DIR/final_output.pdf" \
    2>&1 | tee "$OUTPUT_DIR/logs/musescore_export.log"

echo -e "${GREEN}✓ PDF exported${NC}"
echo

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Workflow Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo
echo -e "Output files:"
echo -e "  - Transposed MusicXML: ${GREEN}$OUTPUT_DIR/transposed_score.musicxml${NC}"
echo -e "  - Final PDF: ${GREEN}$OUTPUT_DIR/final_output.pdf${NC}"
echo -e "  - Logs: ${GREEN}$OUTPUT_DIR/logs/${NC}"
echo
