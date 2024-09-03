# speakr

setup:

1. git clone
2. ```sudo apt install ffmpeg```
3. ```source env/bin/activate```
4. ```cd env```
5. Get an API key for the youtube-v3 api (random tutorial: https://blog.hubspot.com/website/how-to-get-youtube-api-key), then
For linux: ```export YOUTUBE_API_KEY="your-api-key"```
For windows: ```setx YOUTUBE_API_KEY "your-api-key"```
6. ```python3 index.py```