import oxford_cred
import requests
import json
from nested_lookup import nested_lookup
import urllib.request
from pathlib import Path
from pydub import AudioSegment
import numpy as np
from scipy.io.wavfile import write
from pydub.playback import *
from pydub.effects import *
from pydub.generators import *

# TODO: replace with your own app_id and app_key
app_id = oxford_cred.app_id
app_key = oxford_cred.app_key

class WordComp:
    def __init__(self, word):
        self.word = word.lower()
        self.fileName = ""
        self.length = 0
        self.currentLength = 0

        self.getWordSoundFile()
        self.generateSong()

    def getWordSoundFile(self):
        try:
            found = False
            this_dir = Path('.')
            files = [f for f in this_dir.iterdir() if f.is_file()]

            # Look for file
            for f in files:
                wordName = str(f.name).split('_')[0]
                if wordName == self.word:
                    found = True
                    self.fileName = str(f.name)

            if not found:
                r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/' + self.word,
                                 headers={'app_id': app_id, 'app_key': app_key})
                fileArray = nested_lookup('audioFile', r.json())
                fileUrl = fileArray[0]
                self.fileName = fileUrl.split('/')[-1]

                print("Downloading file.")
                urllib.request.urlretrieve(fileUrl, self.fileName)
            else:
                print("File exists")
        except:
            print("Unable to get a sound file for this word, please try a different word.")

    def generateSong(self):
        self.master = AudioSegment.silent(0)

        i = 0
        while i < 21:
            sound = AudioSegment.from_file(self.fileName, format="mp3")
            pan_val = (10 - i) / 10.
            sound = pan(sound, pan_val)
            self.addToMaster(sound, position=i * 50)
            i = i + 1

        play(self.master)

    def addToMaster(self, segment, position):
        if len(segment) + position > len(self.master):
            self.master = self.master + AudioSegment.silent((len(segment) + position) - len(self.master))

        self.master = self.master.overlay(segment, position=position)


wc = WordComp('hail')