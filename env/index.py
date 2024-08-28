# flask --app index run
# OR
# python3 index.py
from flask import Flask, render_template
import pytubefix
from pytubefix import YouTube
import xmltodict

# sudo apt-get install gir1.2-gst-plugins-base-1.0 gir1.2-polkit-1.0 gpicview gstreamer1.0-alsa gstreamer1.0-libav gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x
from playsound import playsound

yt = YouTube('https://www.youtube.com/watch?v=vq-FE8bEtcE')

caption = yt.captions['a.es']

streams = yt.streams.filter(only_audio=True)[:10]
print(streams[:10])
streams[0].download(output_path="audio/", filename="tmp")
playsound("audio/tmp")
captions_dict = xmltodict.parse(caption.xml_captions)

examples = captions_dict['transcript']['text']
print(examples[:10])

app = Flask(__name__, template_folder='templates')

@app.route("/")
def hello_world():
    return render_template('index.html', message=examples[0]["#text"])

if __name__ == '__main__':
   app.run()