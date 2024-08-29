# flask --app index run
# OR
# python3 index.py
from flask import Flask, render_template
import pytubefix
from pytubefix import YouTube
import xmltodict
from pydub import AudioSegment
from pydub.playback import play

# sudo apt-get install gir1.2-gst-plugins-base-1.0 gir1.2-polkit-1.0 gpicview gstreamer1.0-alsa gstreamer1.0-libav gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x

# yt = YouTube('https://www.youtube.com/watch?v=vq-FE8bEtcE')

# caption = yt.captions['a.es']

# streams = yt.streams.filter(only_audio=True)[:10]
# print(streams[:10])
# streams[0].download(output_path="audio/", filename="tmp")
# sound = AudioSegment.from_file("audio/tmp")[10000:20000]
# play(sound)
# captions_dict = xmltodict.parse(caption.xml_captions)

# examples = captions_dict['transcript']['text']
# print(examples[:10])

app = Flask(__name__, template_folder='templates')

def get_caption_sound_pairs(video_url, lang='a.es'):
    yt = YouTube(video_url)
    caption = yt.captions[lang]
    captions_dict = xmltodict.parse(caption.xml_captions)
    examples = captions_dict['transcript']['text']
    yt.streams.filter(only_audio=True)[0].download(output_path="audio/", filename="tmp")
    video_sound = AudioSegment.from_file("audio/tmp")

    captions, sounds = [], []
    for example in examples:
        if example['#text'].find("[Música]") != -1:
            start = int(float(example['@start']) * 1000)
            dur = int(float(example['@dur']) * 1000)
            end = start + dur

            capt = example['#text']
            sound = video_sound[start:end]
            
            captions.append(capt)
            sounds.append(sound)
    return captions, sounds


captions, sounds = get_caption_sound_pairs('https://www.youtube.com/watch?v=vq-FE8bEtcE')
current_index = 0
print(captions[6])
play(sounds[6])

@app.route("/")
def hello_world():
    return render_template('index.html', message=examples[0]["#text"])

@app.route("/play", methods=['POST'])
def play_audio():
    play(sounds[current_index])

if __name__ == '__main__':
   app.run()