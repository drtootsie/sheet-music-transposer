#!/usr/bin/env python3
"""
Script to remove key change from "It Is Well With My Soul"
Transposes measures 20 onwards down by a semitone (F# major -> F minor)
"""

import sys
import os

try:
    from music21 import converter, interval, stream
except ImportError:
    print("Error: music21 library not found")
    print("Install with: pip install music21")
    sys.exit(1)


def transpose_key_change(input_file, output_file, start_measure=20):
    """
    Load a MusicXML file and transpose from start_measure onwards down by a semitone.

    Args:
        input_file: Path to input MusicXML file
        output_file: Path to save transposed MusicXML file
        start_measure: Measure number where key change occurs (default 20)
    """
    print(f"Loading {input_file}...")
    score = converter.parse(input_file)

    print(f"Processing score...")
    print(f"  Total parts: {len(score.parts)}")

    # Create interval for transposition (down a minor 2nd = down 1 semitone)
    transpose_interval = interval.Interval('-m2')

    # Process each part (SA, Men, Piano RH, Piano LH)
    for part_idx, part in enumerate(score.parts):
        print(f"  Processing part {part_idx + 1}: {part.partName if part.partName else 'Unnamed'}")

        measures = part.getElementsByClass('Measure')
        total_measures = len(measures)
        print(f"    Total measures: {total_measures}")

        # Find and transpose measures from start_measure onwards
        transposed_count = 0
        for measure in measures:
            if measure.number >= start_measure:
                # Transpose all notes and chords in this measure
                for element in measure.recurse():
                    if 'Note' in element.classes or 'Chord' in element.classes:
                        element.transpose(transpose_interval, inPlace=True)

                # Update key signature if present
                for ks in measure.getElementsByClass('KeySignature'):
                    # F# major (6 sharps) -> F minor (4 flats)
                    # music21 will handle this automatically when we transpose
                    ks.transpose(transpose_interval, inPlace=True)

                transposed_count += 1

        print(f"    Transposed {transposed_count} measures (from measure {start_measure} onwards)")

    print(f"\nSaving to {output_file}...")
    score.write('musicxml', fp=output_file)
    print("Done!")
    print(f"\nYou can now open {output_file} in MuseScore and export to PDF")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transpose_key_change.py <input.musicxml> [output.musicxml] [start_measure]")
        print("\nExample:")
        print("  python transpose_key_change.py well_soul.musicxml well_soul_fixed.musicxml 20")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output_transposed.musicxml"
    start_measure = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)

    transpose_key_change(input_file, output_file, start_measure)
