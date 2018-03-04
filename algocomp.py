import oxford_cred
import requests
import json
from nested_lookup import nested_lookup
import urllib.request
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import *

# TODO: replace with your own app_id and app_key
app_id = oxford_cred.app_id
app_key = oxford_cred.app_key

class WordComp:
    def __init__(self, word):
        self.word = word.lower()
        self.fileName = ""
        self.getWordSoundFile()
        self.generateSong()

    def getWordSoundFile(self):
        try:
            r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/' + self.word, headers = {'app_id': app_id, 'app_key': app_key})
            fileArray = nested_lookup('audioFile', r.json())
            fileUrl = fileArray[0]
            self.fileName = fileUrl.split('/')[-1]

            file_path = Path(self.fileName)
            if not file_path.is_file():
                print("Downloading file.")
                urllib.request.urlretrieve(fileUrl, self.fileName)
            else:
                print("File exists")
        except:
            print("Unable to get a sound file for this word, please try a different word.")

    def generateSong(self):
        sound = AudioSegment.from_file(self.fileName, format="mp3")
        play(sound)


wc = WordComp('fave')