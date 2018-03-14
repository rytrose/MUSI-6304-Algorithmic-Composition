import oxford_cred
import requests
from nested_lookup import nested_lookup
import urllib.request
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import *
from pydub.effects import *
from pysndfx import AudioEffectsChain
import numpy as np
import librosa as librosa
import math
import os
import uuid

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
        self.analyzeSoundFile()
        self.generateSong()
        self.cleanFiles()

    def getWordSoundFile(self):
        try:
            found = False
            this_dir = Path('.')
            dirs = [d for d in this_dir.iterdir() if d.is_dir()]

            # Look for directory
            for d in dirs:
                if str(d.name) == self.word:
                    found = True
                    word_dir = Path(self.word)
                    files = [f for f in word_dir.iterdir() if f.is_file()]

                    for f in files:
                        if str(f.name).split('_')[0] == self.word:
                            self.fileName = self.word + '/' + str(f.name)

            if not found:
                Path('./' + self.word).mkdir()

                r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/' + self.word,
                                 headers={'app_id': app_id, 'app_key': app_key})
                fileArray = nested_lookup('audioFile', r.json())
                fileUrl = fileArray[0]
                self.fileName = self.word + '/' + fileUrl.split('/')[-1]

                print("Downloading file.")
                urllib.request.urlretrieve(fileUrl, self.fileName)
            else:
                print("File exists")
        except:
            print("Unable to get a sound file for this word, please try a different word.")

    def analyzeSoundFile(self):
        pass


    def generateSong(self):
        self.master = AudioSegment.silent(0)
        y, sr = librosa.load(self.fileName, 44100)
        y_trim, _ = librosa.effects.trim(y)
        librosa.output.write_wav(self.word + "/trim_" + self.word + ".wav", y_trim, sr)

        s = AudioSegment.from_file(self.word + "/trim_" + self.word + ".wav")
        s_low = self.getSegmentWithEffect(s, librosa.effects.pitch_shift, 22050, n_steps=-12)
        s_slow = self.getSegmentWithEffect(s, librosa.effects.time_stretch, 0.2)
        delay = (AudioEffectsChain().delay())
        s_delay = self.getSegmentWithEffect(s, delay)
        fx = (
            AudioEffectsChain()
                .reverb(room_scale=100)
        )
        s_fx = self.getSegmentWithEffect(s, fx)
        self.addToMaster(s_fx, 0)
        # self.addToMaster(s_low, len(s))
        # self.addToMaster(s_slow, len(s) + len(s_low))
        # self.addToMaster(s_delay, len(s) + len(s_low) + len(s_slow))

        play(self.master)

    def cleanFiles(self):
        word_dir = Path('./' + self.word)
        files = [f for f in word_dir.iterdir() if f.is_file()]
        for f in files:
            if str(f) != self.fileName:
                os.remove(str(f))

    def getSegmentWithEffect(self, segment, effectFunction, *args, **kwargs):
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        temp_affected_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)
        y_affected = effectFunction(y, *args, **kwargs)
        librosa.output.write_wav(temp_affected_filename, y_affected, sr)
        return AudioSegment.from_file(temp_affected_filename)



    def addToMaster(self, segment, position):
        if len(segment) + position > len(self.master):
            self.master = self.master + AudioSegment.silent((len(segment) + position) - len(self.master))

        self.master = self.master.overlay(segment, position=position)


wc = WordComp('cower')