# YouTube to Podcast Converter for "Kochen im Tal"
This script downloads audio from YouTube videos, filters them by keyword "Dumm gefragt", converts them to MP3, generates an RSS feed, and uploads the files via SFTP to a web server. It is designed to run periodically as a cron job.

## Features
- Downloads only videos matching a specific keyword
- Converts audio to MP3 format
- Generates an RSS feed for podcast consumption
- Skips already downloaded files
- Uploads audio files and RSS feed to an SFTP server

## Dependencies
The script requires the following dependencies:

### **Python Packages** (install via pip):
```sh
pip install yt-dlp mutagen paramiko pyyaml
```
- `yt-dlp` → Downloads YouTube videos and extracts audio.
- `mutagen` → Reads metadata from MP3 files.
- `paramiko` → Handles SFTP uploads.
- `pyyaml` → Parses YAML configuration files.

### **System Packages** (install via apt):
```sh
sudo apt install -y ffmpeg openssh-client
```
- `ffmpeg` → Required for audio extraction.
- `openssh-client` → Provides SSH/SFTP functionality.

## Configuration
All settings are now stored in a `config.yaml` file. Below is an example configuration:

```yaml
sftp:
  host: "your.sftp.server"
  port: 22
  user: "your_username"
  password: "your_password"
  remote_dir: "/path/to/remote/dir"

youtube:
  url: "https://www.youtube.com/@KochenimTal"
  output_dir: "podcast"
  filter_keyword: "Dumm gefragt"

rss:
  base_url: "https://webermann.net/kochen_im_tal/podcast/"
  rss_file: "podcast.xml"
  icon_url: "https://i.scdn.co/image/ab67656300005f1f82eab0f574e6b3d3679c3b97"

ffmpeg:
  path: "/usr/bin/ffmpeg"
```
## Running the Script Manually
To execute the script manually:
```sh
python3 yt2podcast.py
```

## Setting up a Cron Job
To run the script daily at 03:00 h, add the following cron job:
```sh
0 3 * * * /usr/bin/python3 /path/to/yt2podcast.py >> /path/to/log.txt 2>&1
```
This ensures the script runs automatically and logs output for debugging.

## Notes
- The script will **skip already downloaded files** to avoid duplicates.
- Any **unavailable videos** will be ignored.
- Ensure that `ffmpeg` is installed and accessible at the specified path.

## License
MIT

