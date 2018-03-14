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
                .pitch(-2400)
                .reverb(room_scale=100)
        )
        s_fx = self.getSegmentWithEffect(s + AudioSegment.silent(1000), fx)
        print(len(s_fx))

        s_slow = self.getSegmentWithEffect(s, librosa.effects.time_stretch, 0.2)
        s_tremelo = self.getSegmentWithEffect(s_slow, (AudioEffectsChain().tremolo(800)))
        self.addToMaster(s_tremelo*5, 0)
        # s_dense = self.getDense(s, 50)
        # self.addToMaster(s_dense * 90, 0)
        # s_third = self.getSegmentWithEffect(s_dense, (AudioEffectsChain().pitch(400)))
        # self.addToMaster(s_third * 60, len(s_dense) * 30)
        # s_fifth = self.getSegmentWithEffect(s_dense, (AudioEffectsChain().pitch(700)))
        # self.addToMaster(s_fifth * 30, len(s_dense) * 60)
        # self.addToMaster(s_low, len(s))
        # self.addToMaster(s_slow, len(s) + len(s_low))
        # self.addToMaster(s_delay, len(s) + len(s_low) + len(s_slow))

        play(self.master)

    def getDense(self, segment, dur):
        samples = [abs(s) for s in segment.get_array_of_samples()]
        density = 0
        densest = 0

        i = 0
        while i * dur < len(segment):
            this_sum = sum(samples[math.floor(i*dur*(segment.frame_rate / 1000)):min(math.floor((i+1)*dur*(segment.frame_rate / 1000)), len(samples))])
            if(this_sum > density):
                density = this_sum
                densest = i
            i = i + 1

        return segment[densest*dur:min((densest+1)*dur, len(segment))]

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


wc = WordComp('cat')