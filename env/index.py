# flask --app index run
# OR
# python3 index.py
from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, emit
import pytubefix
from pytubefix import YouTube
import xmltodict
from pydub import AudioSegment
from pydub.playback import play
from unidecode import unidecode
import os
import random
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# sudo apt-get install gir1.2-gst-plugins-base-1.0 gir1.2-polkit-1.0 gpicview gstreamer1.0-alsa gstreamer1.0-libav gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-x

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app,debug=True, cors_allowed_origins='*')



def get_random_youtube_video(api_key, language='es', max_results=50):
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        # Search for videos with captions in the specified language
        search_response = youtube.search().list(
            q='',
            type='video',
            videoCaption='closedCaption',
            relevanceLanguage=language,
            part='id',
            maxResults=max_results
        ).execute()

        # Get video IDs from the search results
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return None

        # Select a random video ID
        random_video_id = random.choice(video_ids)

        # Get video details to confirm caption language
        video_response = youtube.videos().list(
            part='contentDetails',
            id=random_video_id
        ).execute()

        caption_tracks = video_response['items'][0]['contentDetails'].get('caption', 'false')
        yt = YouTube(f'https://www.youtube.com/watch?v={random_video_id}')
        has_language = language in yt.captions or 'a.' + language in yt.captions
        if caption_tracks == 'true' and has_language:
            return f'https://www.youtube.com/watch?v={random_video_id}'
        else:
            # If no captions, try again (recursively)
            return get_random_youtube_video(api_key, language, max_results)

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return None


api_key = os.environ.get("YOUTUBE_API_KEY")
assert api_key is not None, "You must add your youtube api key as an environment variable (check README)"





def filter_example(example):
    dur = int(float(example['@dur']) * 1000)
    if dur < 1000:
        return False
    if example['#text'].find("[Música]") != -1:
        return False
    if example['#text'].find("[___]") != -1:
        return False
    return True

def get_caption_sound_pairs(video_url, lang='a.es'):
    try:
        yt = YouTube(video_url)
        caption = yt.captions[lang] if lang in yt.captions else yt.captions["a." + lang]
        captions_dict = xmltodict.parse(caption.xml_captions)
        examples = captions_dict['transcript']['text']
        yt.streams.filter(only_audio=True)[0].download(output_path="audio/", filename="tmp")
        video_sound = AudioSegment.from_file("audio/tmp")

        captions, sounds = [], []
        for index, example in enumerate(examples):
            if filter_example(example):
                start = int(float(example['@start']) * 1000)
                dur = int(float(example['@dur']) * 1000)
                if index < len(examples) - 1:
                    end = int(float(examples[index+1]['@start']) * 1000) + 100 # add a little extra time
                else:
                    end = start + dur
                if index > 0 and int(float(examples[index-1]['@dur']) * 1000) > 200:
                    start -= 200
                capt = example['#text']
                sound = video_sound[start:end]
                
                captions.append(capt)
                sounds.append(sound)
        
        return captions, sounds
    except Exception as e:
        print("find video failed with error:", e)
        video_url = get_random_youtube_video(api_key, lang)
        return get_caption_sound_pairs(video_url, lang)


def jaccard_similarity(x,y):
  """ returns the jaccard similarity between two lists """
  intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
  union_cardinality = len(set.union(*[set(x), set(y)]))
  return intersection_cardinality/float(union_cardinality)

def clean_string(string):
    punctuation = ".,:?¿!¡'[];"
    for p in punctuation:
        string = string.replace(p, "")
    string = unidecode(string).lower()
    return string

lang = 'es'
random_video_url = get_random_youtube_video(api_key, language=lang)
captions, sounds = get_caption_sound_pairs(random_video_url, lang=lang)
c = list(zip(captions, sounds))

random.shuffle(c)

captions, sounds = zip(*c)

current_index = 0

def play_sound_client(sound):
    with app.app_context():
        sound.export("audio/client/tmp", format="mp4")
        
        audio_url = url_for('hello_world', filename='audio/client/tmp.mp4', _external=True)
        socketio.emit('play_sound', {'url': audio_url})



@app.route("/", methods=['GET', 'POST'])
def hello_world():
    global current_index
    global captions
    global sounds
    play_sound_client(sounds[0])
    if current_index >= len(captions):
        random_video_url = get_random_youtube_video(api_key, language=lang)
        captions, sounds = get_caption_sound_pairs(random_video_url, lang=lang)
        c = list(zip(captions, sounds))

        random.shuffle(c)

        captions, sounds = zip(*c)
    play_sound = request.form.get("play")
    go_next = request.form.get("go_next")
    guess = request.form.get("guess")
    skip_video = request.form.get("skip_video")
    if play_sound:
        play(sounds[current_index])
        play_sound_client(sounds[current_index])
    if go_next:
        current_index += 1
        play(sounds[current_index])
    if guess:
        print("you guessed:", guess)
        print("correct answer:", unidecode(captions[current_index]).lower())
        similarity = jaccard_similarity(clean_string(guess), clean_string(captions[current_index]))
        print("similarity:", similarity)
        correct = similarity > 0.8
        msg = "---Correct---" if correct else "---Incorrect---"
        print(msg)
        socketio.emit('server', msg + f"\nAnswer: {captions[current_index]}")
        current_index += 1
    if skip_video:
        random_video_url = get_random_youtube_video(api_key, language=lang)
        captions, sounds = get_caption_sound_pairs(random_video_url, lang=lang)
        c = list(zip(captions, sounds))

        random.shuffle(c)

        captions, sounds = zip(*c)
    return render_template('index.html')

if __name__ == '__main__':
   app.run()