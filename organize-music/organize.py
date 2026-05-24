#!/usr/bin/env python3
"""
music-organizer: Reorganize MP3 files based on ID3 tags.
Structure: <root>/<Album Artist>/<Album>/<Artist>-<Track>-<Title>.mp3
"""

import argparse
import os
import re
import sys
import shutil
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
except ImportError:
    print("Error: 'mutagen' library not found.")
    print("Please run: pip install mutagen")
    sys.exit(1)

def sanitize_filename(name):
    """Removes invalid characters for filenames and strips whitespace."""
    if not name:
        return "Unknown"
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name.strip(' .')

def get_tag(file_path, tag_key, default="Unknown"):
    """Safely extracts a tag, handling missing tags gracefully."""
    try:
        audio = MP3(file_path, ID3=ID3)
        if not audio.tags:
            return default
        
        tag_map = {
            'artist': 'TPE1',
            'album_artist': 'TPE2',
            'album': 'TALB',
            'title': 'TIT2',
            'track': 'TRCK'
        }
        
        frame = audio.tags.get(tag_map.get(tag_key))
        if frame:
            val = str(frame)
            if tag_key == 'track' and '/' in val:
                val = val.split('/')
            return val.strip()
    except Exception:
        return default
    
    return default

def organize_music(source_path, dest_path=None, dry_run=True, verbose=False):
    source_root = Path(source_path).resolve()
    
    if not source_root.is_dir():
        print(f"Error: Source '{source_root}' is not a valid directory.")
        sys.exit(1)

    # Determine destination root
    if dest_path:
        dest_root = Path(dest_path).resolve()
        # Create destination if it doesn't exist
        if not dest_root.exists():
            if dry_run:
                print(f"[DRY RUN] Would create destination: {dest_root}")
            else:
                try:
                    dest_root.mkdir(parents=True, exist_ok=True)
                    print(f"Created destination: {dest_root}")
                except Exception as e:
                    print(f"Error creating destination: {e}")
                    sys.exit(1)
    else:
        dest_root = source_root

    print(f"Source: {source_root}")
    if dest_path:
        print(f"Destination: {dest_root}")
    else:
        print("Destination: In-place (source)")
    
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("-" * 60)

    mp3_files = list(source_root.rglob("*.mp3"))
    
    if not mp3_files:
        print(f"No MP3 files found in {source_root}")
        return

    moved_count = 0
    skipped_count = 0
    error_count = 0

    for file in mp3_files:
        album_artist = sanitize_filename(get_tag(file, 'album_artist'))
        album = sanitize_filename(get_tag(file, 'album'))
        artist = sanitize_filename(get_tag(file, 'artist'))
        title = sanitize_filename(get_tag(file, 'title'))

        # Logic: Check raw track tag
        raw_track = get_tag(file, 'track', default=None)
        
        include_track = False
        track_str = "00"

        if raw_track and raw_track != "Unknown":
            try:
                track_val = raw_track.split('/')
                track_num = int(track_val)
                track_str = f"{track_num:02d}"
                include_track = True
            except (ValueError, IndexError):
                include_track = False
                track_str = "00"

        if include_track:
            new_filename = f"{artist}-{track_str}-{title}.mp3"
        else:
            new_filename = f"{artist}-{title}.mp3"

        # Construct new path relative to destination root
        new_dir = dest_root / album_artist / album
        new_path = new_dir / new_filename

        # Safety: Don't overwrite existing files
        if new_path.exists() and new_path != file:
            if verbose:
                print(f"[SKIP] Exists: {new_path}")
            skipped_count += 1
            continue

        # If source and destination are the same file, skip
        if file == new_path:
            if verbose:
                print(f"[SAME] Already correct: {file}")
            continue

        if verbose:
            print(f"Processing: {file.name}")
            print(f"  -> {album_artist} / {album}")
            print(f"  -> New: {new_path.name}")

        if not dry_run:
            try:
                new_dir.mkdir(parents=True, exist_ok=True)
                
                if dest_path:
                    # Copy to new location, then delete source? 
                    # Or Move? Let's use copy2 to preserve metadata, then remove source
                    # If you want to MOVE instead of copy, use shutil.move(file, new_path)
                    shutil.copy2(file, new_path)
                    file.unlink() # Delete source
                    moved_count += 1
                else:
                    # In-place move/rename
                    file.rename(new_path)
                    moved_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
                error_count += 1
        else:
            if verbose:
                print(f"  (Would move/copy here: {new_dir})")

    print("-" * 60)
    print(f"Done. Processed: {moved_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    if dry_run:
        print("\n[INFO] Run with '--live' to actually move files.")

def main():
    parser = argparse.ArgumentParser(
        description="Organize MP3 files by ID3 tags."
    )
    parser.add_argument(
        "source", 
        help="Source directory containing music files"
    )
    parser.add_argument(
        "destination", 
        nargs="?", 
        default=None,
        help="Optional destination directory. If omitted, files are reorganized in-place."
    )
    parser.add_argument(
        "--live", 
        action="store_true", 
        help="Actually move/rename files (default is dry run)"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Show detailed output"
    )

    args = parser.parse_args()
    
    dry_run = not args.live
    
    organize_music(args.source, args.destination, dry_run=dry_run, verbose=args.verbose)

if __name__ == "__main__":
    main()

