# Sheet Music Key Change Removal Workflow

Automated workflow to remove key changes from sheet music PDF files using Optical Music Recognition (OMR) and music21.

## Overview

This project removes an unwanted key change from "It Is Well With My Soul" sheet music. The original arrangement starts in F minor (4 flats) and modulates to F# major (6 sharps) at measure 20. This workflow transposes the F# major section back down to F minor, keeping the entire piece in one key.

## The Problem

Many choral arrangements include key changes for dramatic effect, but sometimes you want the piece to stay in the original key throughout. Manually editing sheet music is time-consuming and error-prone, especially for multi-part choral arrangements with piano accompaniment.

## The Solution

This automated workflow:
1. **Converts PDF to images** (one per page)
2. **Runs OCR** using `oemer` to extract music notation as MusicXML
3. **Combines pages** into a single score using `music21`
4. **Transposes** the key change section down by a semitone
5. **Exports** the result back to PDF using MuseScore

## Requirements

### System Requirements
- Linux or WSL2 (tested on Ubuntu)
- Python 3.8+
- 8GB+ RAM (OCR is memory-intensive)
- 30GB+ free disk space (for model downloads)

### Software Dependencies

```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv musescore3 poppler-utils

# Create virtual environment
python3 -m venv music_env
source music_env/bin/activate

# Install Python packages
pip install oemer pdf2image music21
```

## Usage

### Quick Start

```bash
./sheet_music_transpose_workflow.sh "input.pdf" ./output
```

### Running Overnight

The OCR process takes several hours. To run overnight:

```bash
# Use nohup to keep running after logout
nohup ./sheet_music_transpose_workflow.sh "input.pdf" ./output > workflow.log 2>&1 &

# Check progress
tail -f workflow.log
```

## Performance

Expect 10-15 minutes per page for OCR. For an 11-page score, total time is approximately 2-3 hours.

## Credits

- **[oemer](https://github.com/BreezeWhite/oemer)** - Optical Music Recognition
- **[music21](https://github.com/cuthbertLab/music21)** - Music processing toolkit
- **[MuseScore](https://musescore.org/)** - Music notation software

## License

MIT License - See LICENSE file
