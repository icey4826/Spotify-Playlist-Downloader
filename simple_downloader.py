#!/usr/bin/env python3
"""
Simple Audio Downloader
Downloads songs from YouTube in their original audio format without requiring FFmpeg.
"""

import os
import sys
import time
import argparse
import traceback
from pathlib import Path
from typing import TypedDict, List, Tuple, Optional
import re
import tkinter as tk
from tkinter import filedialog, messagebox

# Try to import required libraries
try:
    from yt_dlp import YoutubeDL
    import requests
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required dependencies:")
    print("pip install yt-dlp requests")
    sys.exit(1)

try:
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
except ImportError:
    EasyID3 = None
    MP3 = None


class SongInfo(TypedDict):
    """Structure for song information"""
    title: str
    artist: str


class SimpleAudioDownloader:
    """Simple audio downloader using YouTube search"""
    
    def __init__(self, output_dir: str = "./downloads/", audio_format: str = "best"):
        self.output_dir = Path(output_dir)
        self.audio_format = audio_format
        self.downloaded_count = 0
        self.failed_count = 0
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def search_youtube(self, song_info: SongInfo) -> Tuple[str, str]:
        """Search YouTube for the best match of a song"""
        try:
            search_query = f"{song_info['title']} {song_info['artist']} audio"
            print(f"Searching YouTube for: {search_query}")
            
            # Use yt-dlp to search YouTube
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'default_search': 'ytsearch',
                'max_downloads': 1,
                'format': 'bestaudio/best'
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch1:{search_query}", download=False)
                
                if results and 'entries' in results and results['entries']:
                    video = results['entries'][0]
                    video_id = video.get('id')
                    title = video.get('title', '')
                    
                    if video_id:
                        return f"https://www.youtube.com/watch?v={video_id}", title
            
        except Exception as e:
            print(f"Error searching YouTube: {e}")
        
        return "", ""
    
    def get_song_urls(self, songs: List[SongInfo]) -> List[str]:
        """Get YouTube URLs for all songs"""
        urls = []
        
        print(f"\nSearching for {len(songs)} songs...")
        
        for i, song_info in enumerate(songs, 1):
            print(f"\n[{i}/{len(songs)}] Searching for: {song_info['title']} - {song_info['artist']}")
            
            url, title = self.search_youtube(song_info)
            
            if url:
                urls.append(url)
                print(f"[OK] Matched: {title}")
                self.downloaded_count += 1
            else:
                print(f"X Failed to find match for: {song_info['title']}")
                self.failed_count += 1
            
            # Rate limiting
            time.sleep(2)
        
        return urls
    
    def download_songs(self, urls: List[str], title_first: bool = False) -> None:
        """Download songs using yt-dlp and convert to MP3"""
        if not urls:
            print("No URLs to download")
            return
        
        print(f"\nStarting download of {len(urls)} songs...")
        
        # Use the original song list for filenames
        song_map = getattr(self, '_current_song_map', None)
        if not song_map:
            print("[WARN] No song map found, using default naming.")
        # Download to temp names, then rename and fix tags
        temp_dir = self.output_dir / "_temp_dl"
        temp_dir.mkdir(exist_ok=True)
        filename = f'{temp_dir}/%(id)s.%(ext)s'
        options = {
            'format': 'bestaudio/best',
            'fragment_retries': 10,
            'ignoreerrors': 'only_download',
            'outtmpl': {'default': filename, 'pl_thumbnail': ''},
            'retries': 10,
            'writethumbnail': True,
            'writeinfojson': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'keepvideo': False
        }
        try:
            with YoutubeDL(options) as ydl:
                ydl.download(urls)
        except Exception as e:
            print(f"\nX Download failed: {e}")
            return
        # Map video IDs to song info
        for url, song in song_map.items():
            video_id = url.split('v=')[-1]
            mp3_path = temp_dir / f"{video_id}.mp3"
            if not mp3_path.exists():
                print(f"[WARN] MP3 not found for {song['artist']} - {song['title']}")
                continue
            clean_artist = safe_filename(song['artist'])
            clean_title_str = safe_filename(song['title'])
            out_name = f"{clean_title_str} - {clean_artist}.mp3"
            out_path = self.output_dir / out_name
            mp3_path.replace(out_path)
            # Clean up metadata
            if EasyID3 is None or MP3 is None:
                print("[WARN] mutagen not installed, skipping tag cleanup. Run: pip install mutagen")
                continue
            try:
                audio = MP3(out_path, ID3=EasyID3)
                audio['artist'] = song['artist']
                audio['title'] = clean_title(song['title'])
                audio.save()
            except Exception as e:
                print(f"[WARN] Failed to update tags for {out_name}: {e}")
        # Remove temp dir
        for f in temp_dir.iterdir():
            f.unlink()
        temp_dir.rmdir()
        print("\n[SUCCESS] Download and tag cleanup completed!")
    
    def download_from_songs(self, songs: List[SongInfo], title_first: bool = False, verbose: bool = False) -> None:
        # Build a map from url to song info
        urls = []
        song_map = {}
        failed_songs = []
        for i, song_info in enumerate(songs, 1):
            url, _ = self.search_youtube(song_info)
            if url:
                urls.append(url)
                song_map[url] = song_info
                print(f"[OK] Matched: {song_info['title']} - {song_info['artist']}")
                self.downloaded_count += 1
            else:
                print(f"X Failed to find match for: {song_info['title']}")
                self.failed_count += 1
                failed_songs.append(f"{song_info['artist']} - {song_info['title']}")
            time.sleep(2)
        self._current_song_map = song_map
        if not urls:
            print("No songs could be matched to YouTube. Nothing to download.")
            if failed_songs:
                print("Failed to match the following songs:")
                for s in failed_songs:
                    print(f"  - {s}")
            return
        self.download_songs(urls, title_first)
        if failed_songs:
            print(f"\nSummary: {len(failed_songs)} songs could not be matched and were skipped.")
            for s in failed_songs:
                print(f"  - {s}")


def parse_song_line(line):
    """Parse a line into title and artist, supporting both 'Title:Artist' and 'Title - Artist' formats"""
    line = line.strip()
    if not line:
        return None
    if ':' in line:
        parts = line.split(':', 1)
    elif ' - ' in line:
        parts = line.split(' - ', 1)
    else:
        return None
    if len(parts) == 2:
        return {'title': parts[0].strip(), 'artist': parts[1].strip()}
    return None


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(
        description="Download songs in original audio format using YouTube search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_downloader.py --songs "Song1:Artist1,Song2:Artist2"
  python simple_downloader.py --file songs.txt
  python simple_downloader.py -o ./my_music --songs "Song:Artist"
        """
    )
    
    parser.add_argument(
        "--songs",
        help="Comma-separated list of songs in format 'Title:Artist'"
    )
    
    parser.add_argument(
        "--file",
        help="Text file with songs (one per line, format: Title:Artist)"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        default="./downloads/",
        help="Output directory for downloaded files (default: ./downloads/)"
    )
    
    parser.add_argument(
        "--title-first",
        action="store_true",
        help='Save as "title - artist.ext" instead of "artist - title.ext"'
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Simple Audio Downloader v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Parse songs
    songs = []
    
    if args.songs:
        # Parse comma-separated songs
        song_list = args.songs.split(',')
        for song_str in song_list:
            if ':' in song_str:
                title, artist = song_str.split(':', 1)
                songs.append({'title': title.strip(), 'artist': artist.strip()})
            else:
                print(f"Warning: Invalid song format '{song_str}', expected 'Title:Artist'")
    
    elif args.file:
        # Read songs from file
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    song = parse_song_line(line)
                    if song:
                        songs.append(song)
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    
    else:
        print("Error: Please provide either --songs or --file argument")
        print("Example: python simple_downloader.py --songs \"Song1:Artist1,Song2:Artist2\"")
        return
    
    if not songs:
        print("No valid songs found")
        return
    
    # Create downloader instance
    downloader = SimpleAudioDownloader(
        output_dir=args.output_dir
    )
    
    # Download songs
    downloader.download_from_songs(songs, args.title_first, args.verbose)


def gui_main():
    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select Song List File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            entry_file.delete(0, tk.END)
            entry_file.insert(0, file_path)

    def start_download():
        file_path = entry_file.get().strip()
        if not file_path:
            messagebox.showerror("Error", "Please select a song list file.")
            return
        songs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    song = parse_song_line(line)
                    if song:
                        songs.append(song)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return
        if not songs:
            messagebox.showerror("Error", "No valid songs found in the file.")
            return
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        # Start download in a new window
        top = tk.Toplevel(root)
        top.title("Download Progress")
        text = tk.Text(top, width=60, height=20)
        text.pack()
        def log(msg):
            text.insert(tk.END, msg + '\n')
            text.see(tk.END)
            top.update()
        class GUISimpleAudioDownloader(SimpleAudioDownloader):
            def search_youtube(self, song_info):
                log(f"Searching YouTube for: {song_info['title']} - {song_info['artist']}")
                return super().search_youtube(song_info)
            def download_songs(self, urls, title_first=False):
                log(f"\nStarting download of {len(urls)} songs...")
                super().download_songs(urls, title_first)
                log("\nDownload completed!")
        downloader = GUISimpleAudioDownloader(output_dir=output_dir)
        downloader.download_from_songs(songs)
        messagebox.showinfo("Done", "Download and conversion completed!")
    root = tk.Tk()
    root.title("Song List to MP3 Downloader")
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack()
    tk.Label(frame, text="Song List File:").grid(row=0, column=0, sticky="e")
    entry_file = tk.Entry(frame, width=40)
    entry_file.grid(row=0, column=1, padx=5)
    btn_browse = tk.Button(frame, text="Browse...", command=select_file)
    btn_browse.grid(row=0, column=2)
    btn_start = tk.Button(frame, text="Start Download", command=start_download)
    btn_start.grid(row=1, column=0, columnspan=3, pady=10)
    root.mainloop()


def clean_title(title):
    # Remove common YouTube suffixes
    patterns = [
        r'\(.*official.*video.*\)',
        r'\(.*lyrics? video.*\)',
        r'\[.*official.*video.*\]',
        r'\[.*lyrics? video.*\]',
        r'official music video',
        r'official video',
        r'lyrics? video',
        r'\(.*audio.*\)',
        r'\[.*audio.*\]',
        r'\(.*HD.*\)',
        r'\[.*HD.*\]',
        r'\(.*remaster.*\)',
        r'\[.*remaster.*\]',
        r'\(.*live.*\)',
        r'\[.*live.*\]',
        r'\(.*explicit.*\)',
        r'\[.*explicit.*\]',
        r'\(.*visualizer.*\)',
        r'\[.*visualizer.*\]',
        r'\(.*color coded.*\)',
        r'\[.*color coded.*\]',
        r'\(.*audio.*\)',
        r'\[.*audio.*\]',
        r'\(.*video.*\)',
        r'\[.*video.*\]',
        r'\(.*\d{4}.*\)',
        r'\[.*\d{4}.*\]',
    ]
    t = title
    for pat in patterns:
        t = re.sub(pat, '', t, flags=re.IGNORECASE)
    t = re.sub(r'[-_]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip(' -_')

def safe_filename(s):
    return re.sub(r'[^\w\-.,() \[\]]+', '', s).strip()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        gui_main()
    else:
        main() 