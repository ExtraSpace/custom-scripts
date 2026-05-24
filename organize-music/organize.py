#!/usr/bin/env python3
"""
music-organizer: Reorganize MP3 files based on ID3 tags.
"""

import argparse
import os
import re
import sys
import shutil
from pathlib import Path

# Force buffering off for immediate output
sys.stdout.reconfigure(line_buffering=True)

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
except ImportError:
    print("Error: 'mutagen' library not found.", file=sys.stderr)
    print("Please run: pip install mutagen", file=sys.stderr)
    sys.exit(1)

def sanitize_filename(name):
    if not name:
        return "Unknown"
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name.strip(' .')

def get_tag(file_path, tag_key, default="Unknown"):
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
            
            # Handle track numbers specifically: "11/12" -> list ["11", "12"]
            if tag_key == 'track' and '/' in val:
                val = val.split('/')
                # If split produces a list, we only want the first element (current track)
                # and ensure it's a string before returning
                if isinstance(val, list):
                    val = val.strip() 
                else:
                    val = val.strip()
            else:
                # Standard case: just strip whitespace
                val = val.strip()
            
            return val

    except Exception as e:
        # Log error to stderr if verbose logic was added, but for now just return default
        return default
    
    return default

def get_distribution_folder(name):
    """
    Determine the distribution folder based on the first character of the name.
    Returns 'A-Z' for letters, '0-9' for digits, and '0-9' for others.
    """
    if not name or name == "Unknown":
        return "0-9"
    
    first_char = name[0].upper()
    
    if first_char.isalpha():
        return first_char
    elif first_char.isdigit():
        return "0-9"
    else:
        return "0-9"

def organize_music(source_path, dest_path=None, dry_run=True, verbose=False, action='default', distribute=False):
    source_root = Path(source_path).resolve()
    
    if not source_root.is_dir():
        print(f"Error: Source '{source_root}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Determine action
    final_action = action
    if dest_path is not None and action == 'default':
        final_action = 'copy'
    
    dest_root = None
    if dest_path:
        dest_root = Path(dest_path).resolve()
        if not dest_root.exists():
            if dry_run:
                print(f"[DRY RUN] Destination '{dest_root}' does not exist. Would create it.")
                # In dry run, we don't create it, so we can't proceed to move files into it
                # But we should warn the user
                if not verbose:
                    print("Note: Destination does not exist. Use --live to create it.", file=sys.stderr)
            else:
                try:
                    dest_root.mkdir(parents=True, exist_ok=True)
                    print(f"Created destination: {dest_root}")
                except PermissionError as e:
                    print(f"Error: Permission denied creating destination '{dest_root}'.", file=sys.stderr)
                    print(f"Details: {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"Error creating destination '{dest_root}': {e}", file=sys.stderr)
                    sys.exit(1)
        else:
            if verbose:
                print(f"Destination '{dest_root}' already exists.")
    else:
        dest_root = source_root
        final_action = 'move'

    mode_str = "DRY RUN" if dry_run else "LIVE"
    action_str = "MOVE" if final_action == 'move' else "COPY"
    distribute_str = " (DISTRIBUTED)" if distribute else ""
    
    print(f"Source: {source_root}")
    if dest_path:
        print(f"Destination: {dest_root}")
    else:
        print("Destination: In-place (source)")
    print(f"Action: {action_str}{distribute_str}")
    print(f"Mode: {mode_str}")
    print("-" * 60)

    # Scan for files
    if verbose:
        print(f"Scanning for .mp3 files in {source_root}...")
    
    mp3_files = list(source_root.rglob("*.mp3"))
    
    if not mp3_files:
        print(f"CRITICAL: No MP3 files found in {source_root}", file=sys.stderr)
        print("Please check the source path and file extensions.", file=sys.stderr)
        return

    moved_count = 0
    skipped_count = 0
    error_count = 0

    for file in mp3_files:
        album_artist = sanitize_filename(get_tag(file, 'album_artist'))
        album = sanitize_filename(get_tag(file, 'album'))
        artist = sanitize_filename(get_tag(file, 'artist'))
        title = sanitize_filename(get_tag(file, 'title'))

        raw_track = get_tag(file, 'track', default=None)
        
        # Robust Track Parsing
        include_track = False
        track_str = "00"

        if raw_track and raw_track != "Unknown":
            # Step 1: Normalize to a simple string
            # If raw_track is a list (e.g. ['11', '12'] or ['11/12']), join it
            if isinstance(raw_track, list):
                # Join list elements with '/' if they are separate, or just take the first if it's a list of one
                # Most common case: mutagen returns ['11/12'] -> join gives "11/12"
                # Edge case: mutagen returns ['11', '12'] -> join gives "11/12"
                raw_track = '/'.join(str(x) for x in raw_track)
            
            # Step 2: Now raw_track is definitely a string like "11/12" or "11"
            # Split by '/' to get the current track number
            track_parts = str(raw_track).split('/')
            
            # Step 3: Get the first part
            current_track_str = track_parts[0].strip() # Strip whitespace just in case
            
            try:
                track_val = raw_track.split('/')
                track_num = int(track_val[0])
                track_str = f"{track_num:02d}"
                include_track = True
            except (ValueError, IndexError):
                # Fallback if parsing fails
                include_track = False
                track_str = "00"

        if include_track:
            new_filename = f"{artist}-{track_str}-{title}.mp3"
        else:
            new_filename = f"{artist}-{title}.mp3"

        # Determine the directory structure
        if distribute:
            dist_folder = get_distribution_folder(album_artist)
            new_dir = dest_root / dist_folder / album_artist / album
        else:
            new_dir = dest_root / album_artist / album
        
        new_path = new_dir / new_filename

        if new_path.exists() and new_path != file:
            if verbose:
                print(f"[SKIP] Exists: {new_path}")
            skipped_count += 1
            continue

        if file == new_path:
            if verbose:
                print(f"[SAME] Already correct: {file}")
            continue

        if verbose:
            print(f"Processing: {file.name}")
            if distribute:
                dist_folder = get_distribution_folder(album_artist)
                print(f"  -> {dist_folder} / {album_artist} / {album}")
            else:
                print(f"  -> {album_artist} / {album}")
            print(f"  -> New: {new_path.name} ({action_str})")

        if not dry_run:
            try:
                new_dir.mkdir(parents=True, exist_ok=True)
                
                if final_action == 'move':
                    shutil.copy2(file, new_path)
                    file.unlink()
                    moved_count += 1
                else:
                    shutil.copy2(file, new_path)
                    moved_count += 1
                    
            except Exception as e:
                print(f"  [ERROR] {e}", file=sys.stderr)
                error_count += 1
        else:
            if verbose:
                print("  (Would process here)")
            moved_count += 1

    print("-" * 60)
    print(f"Done. Processed: {moved_count}, Skipped: {skipped_count}, Errors: {error_count}")
    
    if dry_run:
        print("\n[INFO] Run with '--live' to actually execute.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Organize MP3 files.")
    parser.add_argument("source", help="Source directory")
    parser.add_argument("destination", nargs="?", default=None, help="Optional destination directory")
    parser.add_argument("--live", action="store_true", help="Execute changes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--move", action="store_true", help="Force MOVE")
    parser.add_argument("--copy", action="store_true", help="Force COPY")
    parser.add_argument("--distribute", "-d", action="store_true", help="Distribute files into folders by first letter: A/album-artist/album/... , B/album-artist/album/... , etc.")

    args = parser.parse_args()
    
    action = 'default'
    if args.move: action = 'move'
    elif args.copy: action = 'copy'
    
    dry_run = not args.live
    
    organize_music(args.source, args.destination, dry_run=dry_run, verbose=args.verbose, action=action, distribute=args.distribute)

if __name__ == "__main__":
    main()
