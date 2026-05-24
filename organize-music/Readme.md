# 🎵 Music Organizer

A robust, self-contained Python CLI tool to reorganize your music library based on ID3 metadata. It intelligently renames and structures your MP3 files, handling duplicate folder nesting, missing tags, and optionally distributing them into alphabetical containers.

**Key Features:**
- **Smart Reorganization**: Converts messy structures (e.g., `Artist/Artist/Album/Track`) into clean hierarchies (`AlbumArtist/Album/Track-Artist-Title.mp3`).
- **Distributed Organization** (NEW): Optionally organize files by first letter/digit into containers: `A/`, `B/`, ..., `0-9/` for scalable library structures.
- **Flexible Modes**: Supports **Dry Run** (preview), **Copy**, and **Move** operations.
- **Safe Defaults**: Automatically handles missing tags, sanitizes filenames, and prevents overwrites.
- **Zero System Dependencies**: Runs in an isolated Python virtual environment (`.venv`), keeping your system Python clean.
- **Cross-Platform**: Works on Linux (Manjaro, Ubuntu, etc.), macOS, and Windows (with WSL).

---

## 📋 Prerequisites

- **Python 3.8+** (Installed on your system)
- **Git** (to clone the repository)
- **Bash** (for the setup and runner scripts)

> **Note**: This tool is designed for **MP3** files. It uses the `mutagen` library to read ID3 tags.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-github-repo-url>
cd music-organizer
```

### 2. Initialize the Environment
Run the setup script to create a virtual environment and install dependencies. This takes about 30 seconds.
```bash
./setup.sh
```

### 3. Run a Dry Run (Safety First!)
Before making any changes, run the tool in **Dry Run** mode to see what it *would* do.
```bash
./run.sh /path/to/your/music --verbose
```
*Output example:*
```text
Source: /path/to/your/music
Destination: In-place (source)
Action: MOVE
Mode: DRY RUN
------------------------------------------------------------
Processing: track1.mp3
  -> Bryan Adams / Anthology
  -> New: Bryan Adams-01-Summer of '69.mp3
  (Would move here)
```

### 4. Execute the Reorganization
Once you are satisfied with the Dry Run, add the `--live` flag to perform the actual moves.
```bash
./run.sh /path/to/your/music --live
```
*This will automatically clean up empty directories after moving files.*

---

## 🛠 Usage Scenarios

### Scenario A: Reorganize in Place
Perfect for fixing nested folders like `Artist/Artist/Album` within the same directory.
```bash
./run.sh /path/to/music --live
```
*Default behavior: Moves files, deletes empty source folders.*

### Scenario B: Copy to a New Location (Backup Safe)
Copies files to a new folder without deleting the originals.
```bash
./run.sh /source/music /destination/music --live --copy
```
*Default behavior for external destinations is `--copy`. Use `--move` to delete originals.*

### Scenario C: Move to a New Location (Migration)
Moves files to a new drive or folder and deletes the source.
```bash
./run.sh /old/music /new/music --live --move
```

### Scenario D: Distribute by First Letter (New)
Organizes files into alphabetical containers for better scalability on large libraries.
```bash
./run.sh /path/to/music /destination/music --live --distribute
```

This creates a structure like:
```
destination/
├── A/
│   └── Adele/
│       └── 25/
│           └── Adele-01-Hello.mp3
├── B/
│   └── Beatles/
│       └── Abbey Road/
│           └── Beatles-01-Come Together.mp3
├── 0-9/
│   └── 10cc/
│       └── Sheet Music/
│           └── 10cc-01-I'm Not In Love.mp3
```

### Scenario E: Custom Filename Format
The tool automatically adjusts filenames based on metadata:
- **With Track Number**: `Artist-05-Title.mp3`
- **Without Track Number**: `Artist-Title.mp3`

---

## 🧩 Command Reference

Run `./run.sh --help` for a full list of options.

| Flag | Description |
| :--- | :--- |
| `--live` | **Required** to execute changes. Default is Dry Run. |
| `--verbose`, `-v` | Show detailed output for every file processed. |
| `--move` | Force **Move** operation (Copy + Delete Source). |
| `--copy` | Force **Copy** operation (Leave source intact). |
| `--distribute`, `-d` | Distribute files into folders by first letter/digit: `A/`, `B/`, ..., `0-9/`. |
| `source` | Path to the directory containing your music files. |
| `destination` | *(Optional)* Path to the new directory. If omitted, reorganizes in-place. |

**Examples:**
```bash
# Preview changes
./run.sh /music --verbose

# Move files to a new folder
./run.sh /music /new_music --live --move

# Copy files to a backup folder
./run.sh /music /backup_music --live --copy

# Distribute files by first letter (preview)
./run.sh /music /distributed_music --verbose --distribute

# Distribute and execute
./run.sh /music /distributed_music --live --distribute
```

---

## 🏗 Architecture

This project is designed to be self-contained:

1.  **`organize.py`**: The core Python logic using `mutagen` for ID3 tag parsing.
2.  **`setup.sh`**: Initializes the virtual environment (`.venv`) and installs `mutagen`.
3.  **`run.sh`**: The launcher script that activates the venv, runs the Python script, and handles post-processing (empty directory cleanup).
4.  **`.venv/`**: The isolated Python environment (ignored by Git).

### Why a Virtual Environment?
- **Safety**: Prevents conflicts with system packages.
- **Portability**: You can move the entire folder to another machine, run `./setup.sh`, and it works immediately.
- **Cleanliness**: No `pip install` required globally.

---

## ⚙️ Customization

### Changing the Filename Format
To change the output format (e.g., `Track - Title` instead of `Artist-Track-Title`), edit the `organize.py` file:

```python
# Find the section around line 140
if include_track:
    new_filename = f"{artist}-{track_str}-{title}.mp3"
else:
    new_filename = f"{artist}-{title}.mp3"
```
Modify the f-string to your preference.

### Modifying Distribution Logic
To customize how files are distributed (e.g., by genre, decade, or custom groupings), edit the `get_distribution_folder()` function:

```python
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
```

### Handling Other Formats
Currently, the script only processes `.mp3` files (via `rglob("*.mp3")`). To support FLAC or M4A:
1.  Change `rglob("*.mp3")` to `rglob("*.mp3")` or `rglob("*.flac")`.
2.  Ensure `mutagen` supports the format (it does for most common formats).

---

## 🐛 Troubleshooting

### "No MP3 files found"
- **Cause**: The source directory contains no `.mp3` files or the path is incorrect.
- **Fix**: Verify the path and file extensions.

### "Permission Denied"
- **Cause**: You don't have write access to the destination folder.
- **Fix**: Run with `sudo` (if safe) or check folder permissions (`chmod`/`chown`).

### "ModuleNotFoundError: No module named 'mutagen'"
- **Cause**: The virtual environment wasn't set up correctly.
- **Fix**: Run `./setup.sh` again.

### Files didn't move?
- **Cause**: You ran without `--live`.
- **Fix**: Add `--live` to the command. The script defaults to **Dry Run** to prevent accidental data loss.

### "Distribute" flag not working?
- **Cause**: You might be using an older version of the script.
- **Fix**: Pull the latest version from the repository and re-run `./setup.sh` if needed.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

> **Disclaimer**: Always backup your music library before running bulk operations. While this tool includes safety checks (Dry Run, overwrite protection), data loss is always a risk when moving files. Use responsibly!
