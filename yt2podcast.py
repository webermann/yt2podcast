import os
import sys
import yaml
import xml.etree.ElementTree as ET
import paramiko
from datetime import datetime
from mutagen.mp3 import MP3

try:
    import yt_dlp
except ModuleNotFoundError:
    print("Error: The module 'yt_dlp' is not installed. Install it using 'pip install yt-dlp'.")
    exit(1)

# Load configuration from YAML
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract settings
YOUTUBE_URL = config["youtube"]["url"]
OUTPUT_DIR = config["youtube"]["output_dir"]
FILTER_KEYWORD = config["youtube"]["filter_keyword"]
BASE_URL = config["rss"]["base_url"]
RSS_FILE = config["rss"]["rss_file"]
ICON_URL = config["rss"]["icon_url"]
FFMPEG_PATH = config["ffmpeg"]["path"]

SFTP_HOST = config["sftp"]["host"]
SFTP_PORT = config["sftp"]["port"]
SFTP_USER = config["sftp"]["user"]
SFTP_PASSWORD = config["sftp"]["password"]
SFTP_REMOTE_DIR = config["sftp"]["remote_dir"]

# Create the directory if it does not exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def progress_hook(d):
    if d['status'] == 'downloading' and '_percent_str' in d:
        sys.stdout.write(f"\rDownloading: {d.get('filename', 'Unknown')} - {d['_percent_str']} ({d.get('_speed_str', 'N/A')} | {d.get('_eta_str', 'N/A')})")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        print(f"\nDownload complete: {d['filename']}")

def download_audio(youtube_url):
    existing_files = {f.replace(".mp3", "") for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")}
    
    def filter_existing(info):
        title = info.get('title', '')
        if FILTER_KEYWORD in title:
            if title in existing_files:
                return f"Skipping already existing file: {title}"
            return None
        return 'Video skipped'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': FFMPEG_PATH,
        'nocheckcertificate': True,
        'quiet': False,
        'progress_hooks': [progress_hook],
        'match_filter': filter_existing,
        'ignoreerrors': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return False
    return True

def get_audio_files():
    try:
        return [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3") and FILTER_KEYWORD in f]
    except FileNotFoundError:
        print("Error: Audio file directory not found.")
        return []

def get_duration(file_path):
    try:
        audio = MP3(file_path)
        return int(audio.info.length)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return 0

def get_file_date(file_path):
    try:
        timestamp = os.path.getmtime(file_path)
        return datetime.utcfromtimestamp(timestamp).strftime("%a, %d %b %Y %H:%M:%S GMT")
    except Exception as e:
        print(f"Error retrieving file date {file_path}: {e}")
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def create_rss():
    audio_files = get_audio_files()
    if not audio_files:
        print("No matching audio files found. RSS feed will not be created.")
        return
    
    channel = ET.Element("channel")
    ET.SubElement(channel, "title").text = "Kochen im Tal - Dumm gefragt"
    ET.SubElement(channel, "link").text = BASE_URL
    ET.SubElement(channel, "description").text = "Automatically generated podcast from the 'Dumm gefragt' series"
    ET.SubElement(channel, "language").text = "de"
    image = ET.SubElement(channel, "image")
    ET.SubElement(image, "url").text = ICON_URL
    ET.SubElement(image, "title").text = "Kochen im Tal - Dumm gefragt"
    ET.SubElement(image, "link").text = BASE_URL
    
    for file in audio_files:
        file_path = os.path.join(OUTPUT_DIR, file)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = file.replace(".mp3", "")
        ET.SubElement(item, "enclosure", url=BASE_URL + file, type="audio/mpeg")
        ET.SubElement(item, "guid").text = BASE_URL + file
        ET.SubElement(item, "pubDate").text = get_file_date(file_path)
        ET.SubElement(item, "duration").text = str(get_duration(file_path))
    
    rss = ET.Element("rss", version="2.0")
    rss.append(channel)
    
    tree = ET.ElementTree(rss)
    tree.write(RSS_FILE, encoding="utf-8", xml_declaration=True)
    print(f"RSS feed created: {RSS_FILE}")

def upload_sftp():
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        sftp.put(RSS_FILE, os.path.join(SFTP_REMOTE_DIR, RSS_FILE))
        for file in get_audio_files():
            local_path = os.path.join(OUTPUT_DIR, file)
            remote_path = os.path.join(SFTP_REMOTE_DIR, file)
            sftp.put(local_path, remote_path)
            print(f"Uploaded {file} to {remote_path}")
        
        sftp.close()
        transport.close()
        print("SFTP upload completed.")
    except Exception as e:
        print(f"SFTP upload failed: {e}")

# Run script
if download_audio(YOUTUBE_URL):
    create_rss()
    upload_sftp()
