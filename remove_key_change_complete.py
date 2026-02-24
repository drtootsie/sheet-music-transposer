#!/usr/bin/env python3
"""
Complete automated workflow to remove key changes from sheet music.

This script:
1. Converts PDF to images
2. Runs OCR on each page to extract MusicXML
3. Combines all pages into one score
4. Removes key changes by:
   - Replacing 5+ sharp key signatures with F minor (4 flats)
   - Transposing notes in those sections down a semitone
5. Adds lyrics to the vocal line
6. Exports to PDF

Usage:
    python3 remove_key_change_complete.py input.pdf output.pdf

Requirements:
    pip install music21 oemer pdf2image pytesseract
    apt install musescore3 tesseract-ocr poppler-utils
"""

import sys
import os
import glob
from pathlib import Path

# Add music21 to path if using virtual environment
sys.path.insert(0, '/tmp/music_env/lib/python3.12/site-packages')

from music21 import converter, interval, key, note, chord
from pdf2image import convert_from_path
import subprocess


def pdf_to_images(pdf_path, output_dir):
    """Convert PDF pages to PNG images."""
    print(f"Converting {pdf_path} to images...")
    os.makedirs(output_dir, exist_ok=True)

    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []

    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f'page_{i+1:02d}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
        print(f"  Saved page {i+1}")

    return image_paths


def ocr_images_to_musicxml(image_paths, output_dir):
    """Run OCR on images to extract MusicXML."""
    print("\nRunning OCR on all pages...")
    os.makedirs(output_dir, exist_ok=True)

    xml_files = []

    # Skip first page (cover)
    for img_path in image_paths[1:]:
        page_num = os.path.basename(img_path).replace('.png', '')
        page_output_dir = os.path.join(output_dir, page_num)
        os.makedirs(page_output_dir, exist_ok=True)

        print(f"  Processing {os.path.basename(img_path)}...")

        # Run oemer
        subprocess.run([
            'oemer', img_path,
            '-o', page_output_dir
        ], capture_output=True, timeout=600)

        # Find the generated MusicXML file
        xml_pattern = os.path.join(page_output_dir, '*.musicxml')
        found_files = glob.glob(xml_pattern)
        if found_files:
            xml_files.append(found_files[0])

    return sorted(xml_files)


def combine_musicxml_pages(xml_files, output_path):
    """Combine multiple MusicXML pages into one score."""
    print(f"\nCombining {len(xml_files)} pages...")

    if not xml_files:
        raise ValueError("No MusicXML files to combine!")

    # Load first page
    combined = converter.parse(xml_files[0])

    # Append remaining pages
    for xml_file in xml_files[1:]:
        score = converter.parse(xml_file)

        for part_idx, part in enumerate(score.parts):
            if part_idx < len(combined.parts):
                measures = part.getElementsByClass('Measure')
                for measure in measures:
                    combined.parts[part_idx].append(measure)

    combined.write('musicxml', fp=output_path)
    print(f"  ✅ Saved to {output_path}")
    return output_path


def remove_key_change(input_musicxml, output_musicxml):
    """Remove key change by replacing sharp signatures and transposing notes."""
    print("\nRemoving key change...")

    score = converter.parse(input_musicxml)
    transpose_interval = interval.Interval('-m2')  # Down a semitone

    for part_idx, part in enumerate(score.parts):
        measures = part.getElementsByClass('Measure')

        in_modulation = False
        key_sigs_replaced = 0
        measures_transposed = 0

        for m_idx, measure in enumerate(measures):
            # Replace 5+ sharp key signatures with F minor (4 flats)
            ks_list = list(measure.getElementsByClass('KeySignature'))

            for ks in ks_list:
                if ks.sharps >= 5:
                    measure.remove(ks)
                    measure.insert(0, key.KeySignature(-4))  # F minor
                    in_modulation = True
                    key_sigs_replaced += 1

            # Transpose notes in modulated sections
            if in_modulation:
                for element in measure.flatten():
                    if isinstance(element, note.Note):
                        element.transpose(transpose_interval, inPlace=True)
                    elif isinstance(element, chord.Chord):
                        element.transpose(transpose_interval, inPlace=True)
                measures_transposed += 1

        print(f"  Part {part_idx + 1}: Replaced {key_sigs_replaced} key sigs, " +
              f"transposed {measures_transposed} measures")

    score.write('musicxml', fp=output_musicxml)
    print(f"  ✅ Saved to {output_musicxml}")
    return output_musicxml


def add_lyrics(input_musicxml, output_musicxml):
    """Add lyrics to the vocal line."""
    print("\nAdding lyrics...")

    # Standard "It Is Well With My Soul" lyrics
    lyrics = [
        # Verse 1
        "When", "peace,", "like", "a", "riv", "-", "er,", "at", "-", "tend", "-", "eth", "my",
        "way,", "When", "sor", "-", "rows", "like", "sea", "bil", "-", "lows", "roll—",
        "What", "-", "ev", "-", "er", "my", "lot,", "Thou", "hast", "taught", "me", "to", "say,",
        "\"It", "is", "well,", "it", "is", "well", "with", "my", "soul.\"",

        # Verse 2
        "Though", "Sat", "-", "an", "should", "buf", "-", "fet,", "though",
        "tri", "-", "als", "should", "come,",
        "Let", "this", "blest", "as", "-", "sur", "-", "ance", "con", "-", "trol:",
        "That", "Christ", "hath", "re", "-", "gard", "-", "ed", "my",
        "help", "-", "less", "es", "-", "tate",
        "And", "hath", "shed", "His", "own", "blood", "for", "my", "soul.",

        # Refrains and remaining verses...
        "It", "is", "well", "with", "my", "soul;",
        "It", "is", "well", "with", "my", "soul;",
        "It", "is", "well,", "it", "is", "well", "with", "my", "soul.",
    ]

    score = converter.parse(input_musicxml)

    # Add lyrics to first part (usually vocal)
    for part_idx, part in enumerate(score.parts[:1]):
        notes_list = [n for n in part.flatten().notes if isinstance(n, note.Note)]

        for i, lyric in enumerate(lyrics):
            if i < len(notes_list):
                notes_list[i].lyric = lyric

        print(f"  ✅ Added {min(len(lyrics), len(notes_list))} lyrics to part {part_idx + 1}")

    score.write('musicxml', fp=output_musicxml)
    return output_musicxml


def export_to_pdf(musicxml_path, pdf_path):
    """Export MusicXML to PDF using MuseScore."""
    print(f"\nExporting to PDF...")

    result = subprocess.run([
        'musescore3',
        musicxml_path,
        '-o', pdf_path
    ], capture_output=True, text=True, timeout=120)

    if result.returncode == 0:
        print(f"  ✅ Exported to {pdf_path}")
        return pdf_path
    else:
        raise RuntimeError(f"MuseScore export failed: {result.stderr}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]

    if not os.path.exists(input_pdf):
        print(f"Error: Input file not found: {input_pdf}")
        sys.exit(1)

    # Create working directory
    work_dir = Path('/tmp/sheet_music_work')
    work_dir.mkdir(exist_ok=True)

    print("="*70)
    print("SHEET MUSIC KEY CHANGE REMOVER")
    print("="*70)

    # Step 1: Convert PDF to images
    images_dir = work_dir / 'images'
    image_paths = pdf_to_images(input_pdf, str(images_dir))

    # Step 2: OCR images to MusicXML
    musicxml_dir = work_dir / 'musicxml'
    xml_files = ocr_images_to_musicxml(image_paths, str(musicxml_dir))

    # Step 3: Combine pages
    combined_xml = work_dir / 'combined.musicxml'
    combine_musicxml_pages(xml_files, str(combined_xml))

    # Step 4: Remove key change
    fixed_xml = work_dir / 'fixed.musicxml'
    remove_key_change(str(combined_xml), str(fixed_xml))

    # Step 5: Add lyrics
    final_xml = work_dir / 'final.musicxml'
    add_lyrics(str(fixed_xml), str(final_xml))

    # Step 6: Export to PDF
    export_to_pdf(str(final_xml), output_pdf)

    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"\nOutput file: {output_pdf}")


if __name__ == '__main__':
    main()
