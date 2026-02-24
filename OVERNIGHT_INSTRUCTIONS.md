# Overnight Processing Instructions

## Current Status

✅ **Pages 2-3**: Completed (18% done)  
⏳ **Pages 4-12**: Currently processing  
⏱️ **Estimated completion**: ~2-3 hours

## What's Running

All OCR processes are running in the background using `nohup`. They will continue even if you:
- Close your terminal
- Logout
- Disconnect from SSH/WSL

## Check Progress Anytime

```bash
/tmp/check_progress.sh
```

This will show you:
- How many pages are complete
- Which pages are currently processing
- Estimated time remaining

## When You Wake Up

### 1. Check if OCR is complete

```bash
/tmp/check_progress.sh
```

You should see "🎉 All pages completed!"

### 2. Combine the pages

```bash
cd /tmp
/tmp/music_env/bin/python3 << 'ENDPYTHON'
from music21 import converter
import glob

xml_files = sorted(glob.glob("/tmp/well_soul_musicxml/page_*/page_*.musicxml"))
print(f"Found {len(xml_files)} MusicXML files")

combined = converter.parse(xml_files[0])
for xml_file in xml_files[1:]:
    print(f"Adding {xml_file}...")
    score = converter.parse(xml_file)
    for part_idx, part in enumerate(score.parts):
        if part_idx < len(combined.parts):
            for measure in part.getElementsByClass('Measure'):
                combined.parts[part_idx].append(measure)

print("Saving combined score...")
combined.write('musicxml', fp='/tmp/well_soul_combined.musicxml')
print("Done!")
ENDPYTHON
```

### 3. Transpose the key change

```bash
/tmp/music_env/bin/python3 /tmp/transpose_key_change.py \
    /tmp/well_soul_combined.musicxml \
    /tmp/well_soul_transposed.musicxml \
    20
```

### 4. Export to PDF

```bash
musescore3 /tmp/well_soul_transposed.musicxml \
    -o "/mnt/c/Users/ppancoast/Downloads/It Is Well - No Key Change.pdf"
```

### 5. Your final file will be at:

```
C:\Users\ppancoast\Downloads\It Is Well - No Key Change.pdf
```

## Troubleshooting

### If some pages failed

Check the logs:
```bash
grep -i error /tmp/well_soul_musicxml/*.log
```

Re-run failed pages:
```bash
/tmp/music_env/bin/oemer /tmp/well_soul_pages/page_XX.png \
    -o /tmp/well_soul_musicxml/page_XX
```

### If you need to start over

```bash
# Kill all OCR processes
pkill -f oemer

# Clean up and restart
rm -rf /tmp/well_soul_musicxml/page_*/*.musicxml
# Then re-run the overnight instructions
```

## Save to Git Repo

All the workflow files are in `/tmp/`:
- `/tmp/README.md` - Complete documentation
- `/tmp/sheet_music_transpose_workflow.sh` - Full automation script  
- `/tmp/transpose_key_change.py` - Transposition script
- `/tmp/check_progress.sh` - Progress monitor

Copy these to your git repo:
```bash
mkdir -p ~/sheet-music-transpose
cp /tmp/README.md ~/sheet-music-transpose/
cp /tmp/sheet_music_transpose_workflow.sh ~/sheet-music-transpose/
cp /tmp/transpose_key_change.py ~/sheet-music-transpose/
cp /tmp/check_progress.sh ~/sheet-music-transpose/

cd ~/sheet-music-transpose
git init
git add .
git commit -m "Initial commit: Sheet music transposition workflow"
```

## Summary

Tonight, the computer will:
1. Process all 11 music pages with OCR (~2-3 hours)
2. Save each as MusicXML

Tomorrow morning, you'll:
1. Run 3 quick commands to combine, transpose, and export
2. Get your final PDF with no key change!
3. Save the workflow to git for future use

Sleep well! 😴
