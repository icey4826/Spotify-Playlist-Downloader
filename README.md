# Spotify Playlist Downloader

A Python-based tool to download songs from Spotify playlists as MP3 files using YouTube as the source. Features a clean GUI interface and automatic metadata tagging.

## Features

- **GUI Interface**: Easy-to-use graphical interface for browsing and selecting song lists
- **Flexible Input**: Supports both `Title:Artist` and `Title - Artist` formats
- **Clean Filenames**: Uses your original song list for clean, consistent filenames (`Title - Artist.mp3`)
- **Metadata Tagging**: Automatically cleans and sets MP3 metadata tags
- **Batch Processing**: Download entire playlists with one click
- **Error Handling**: Comprehensive error reporting and failed song summaries

## Installation

### Prerequisites

1. **Python 3.7+**
2. **FFmpeg** (for audio conversion)
   ```bash
   # Windows (using winget)
   winget install Gyan.FFmpeg
   
   # Or download from https://ffmpeg.org/download.html
   ```

### Python Dependencies

```bash
pip install yt-dlp requests mutagen
```

## Usage

### GUI Mode (Recommended)

1. Run the script without arguments:
   ```bash
   python simple_downloader.py
   ```

2. In the GUI:
   - Click "Browse..." to select your song list file
   - Click "Start Download" and choose output directory
   - Watch the progress window for updates

### Command Line Mode

```bash
# Using a text file
python simple_downloader.py --file songs.txt

# Using comma-separated songs
python simple_downloader.py --songs "Song1:Artist1,Song2:Artist2"

# Specify output directory
python simple_downloader.py --file songs.txt -o ./my_music
```

## Input Format

Your song list file should contain one song per line in either format:

```
Wake Me Up - Avicii
Tsunami - DVBBS, Borgeous
All Around The World - R3HAB, A Touch Of Class
```

OR

```
Wake Me Up:Avicii
Tsunami:DVBBS, Borgeous
All Around The World:R3HAB, A Touch Of Class
```

## Output

- **Filenames**: `Title - Artist.mp3` (clean, filesystem-safe)
- **Metadata**: Artist and cleaned title tags
- **Quality**: 192kbps MP3
- **Location**: User-selected output directory

## Features in Detail

### Clean Filenames
- Removes duplicate artist names (e.g., "Avicii - Avicii - Wake Me Up" → "Wake Me Up - Avicii")
- Uses your original song list, not YouTube metadata
- Filesystem-safe character filtering

### Metadata Cleaning
- Removes YouTube suffixes like "Official Video", "Lyric Video", etc.
- Sets clean artist and title tags
- Preserves audio quality while cleaning metadata

### Error Handling
- Detailed logging of failed matches
- Summary of skipped songs
- Graceful handling of network issues

## Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   - Install FFmpeg: `winget install Gyan.FFmpeg`
   - Restart your terminal after installation

2. **"mutagen not installed"**
   - Install mutagen: `pip install mutagen`
   - This enables metadata tag editing

3. **No songs matched**
   - Check your song list format
   - Try different search terms or artist names
   - Some songs may not be available on YouTube

### Getting Your Song List

Use the included `spotify_playlist_exporter.user.js` userscript to export playlists from Spotify:

1. Install Tampermonkey browser extension
2. Add the userscript to Tampermonkey
3. Navigate to a Spotify playlist
4. Click "Export Songs" button
5. Use the downloaded `.txt` file with this downloader

## License

This project is open source. Feel free to modify and distribute.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests. 