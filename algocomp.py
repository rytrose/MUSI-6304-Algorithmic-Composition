import oxford_cred
import requests
from nested_lookup import nested_lookup
import urllib.request
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import *
from pydub.effects import *
from pydub.generators import *
from pysndfx import AudioEffectsChain
import numpy as np
import librosa as librosa
import math
import random
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
        # Establish master segment
        self.master = AudioSegment.silent(0)

        # Trim the collected word file
        y, sr = librosa.load(self.fileName, 44100)
        y_trim, _ = librosa.effects.trim(y)
        librosa.output.write_wav(self.word + "/trim_" + self.word + ".wav", y_trim, sr)

        # Create main word segment
        self.s = AudioSegment.from_file(self.word + "/trim_" + self.word + ".wav")

        # Create percussion segments
        self.closed_hat = AudioSegment.from_file("perc/Closed_Hat_06.wav")
        self.open_hat = AudioSegment.from_file("perc/Open_Hat_19.wav")
        self.snare = AudioSegment.from_file("perc/Snare_09.wav")
        self.kick = AudioSegment.from_file("perc/Kick_016.wav")

        # Set tempo (set in BPM, calculated to mspb)
        bpm_tempo = 134
        self.beat = math.floor(60000 / bpm_tempo)

        # pos = self.intro()
        pos = 0
        self.section1(pos)

        # s_low = self.getSegmentWithEffect(s, librosa.effects.pitch_shift, 22050, n_steps=-12)
        # s_slow = self.getSegmentWithEffect(s, librosa.effects.time_stretch, 0.2)
        # delay = (AudioEffectsChain().delay())
        # s_delay = self.getSegmentWithEffect(s, delay)
        # fx = (
        #     AudioEffectsChain()
        #         .pitch(-2400)
        #         .reverb(room_scale=100)
        # )
        # s_fx = self.getSegmentWithEffect(s + AudioSegment.silent(1000), fx)
        # s_dense, i1, i2 = self.getDense(s, 50)
        # self.addToMaster(s_dense * 90, 0)
        # s_third = self.getSegmentWithEffect(s_dense, (AudioEffectsChain().pitch(400)))
        # self.addToMaster(s_third * 60, len(s_dense) * 30)
        # s_fifth = self.getSegmentWithEffect(s_dense, (AudioEffectsChain().pitch(700)))
        # self.addToMaster(s_fifth * 30, len(s_dense) * 60)
        # self.addToMaster(s_low, len(s))
        # self.addToMaster(s_slow, len(s) + len(s_low))
        # self.addToMaster(s_delay, len(s) + len(s_low) + len(s_slow))

        # s = AudioSegment.from_file("newsheadlines.mp3")
        # fx = lambda t: (
        #     AudioEffectsChain()
        #         .lowpass(800 * Curve(math.sin).val(t))
        # )

        # s_fx = self.getSegmentWithEffectOverTime(s, fx)
        # s_fx = self.getSegmentWithEffect(s, fx)
        # self.addToMaster(s_fx, 0)

        # fx = lambda t: (
        #     AudioEffectsChain()
        #         .lowpass(1000 * Curve(math.sin, 4).val(t))
        # )
        #
        # self.master = self.getSegmentWithEffectOverTime(self.master, fx)

        reverb = (
            AudioEffectsChain()
                .reverb(2)
        )
        self.master = self.getSegmentWithEffect(self.master, reverb)
        play(self.master + AudioSegment.silent(1000))

    def intro(self):
        pos = 0
        self.addToMaster(self.s, 0)
        pos = 4 * self.tempo
        self.addToMaster(self.s, pos)
        pos += 4 * self.tempo
        for i in range(2):
            self.addToMaster(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-3*i), pos)
            pos += 1 * self.tempo
            self.addToMaster(apply_gain_stereo(self.s, left_gain=-3*i, right_gain=1.0), pos)
            pos += 1 * self.tempo
        for i in range(2):
            self.addToMaster(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-6 - (3*i)), pos)
            pos += 0.5 * self.tempo
            self.addToMaster(apply_gain_stereo(self.s, left_gain=-6 - (3*i), right_gain=1.0), pos)
            pos += 0.5 * self.tempo

        for i in range(8):
            for i in range(2):
                self.addToMaster(apply_gain_stereo(self.s, left_gain=-10, right_gain=-18), pos)
                pos += 0.065 * self.beat
                self.addToMaster(apply_gain_stereo(self.s, left_gain=-18, right_gain=-10), pos)
                pos += 0.065 * self.beat

        pos += 3 * self.beat
        self.addToMaster(self.s, pos)
        self.addToMaster(self.getSegmentWithEffect(self.s, librosa.effects.pitch_shift, 22050, n_steps=-12), pos)
        self.addToMaster(self.getSegmentWithEffect(self.s, librosa.effects.pitch_shift, 22050, n_steps=12), pos)
        pos += self.beat
        return pos

    def section1(self, pos):
        for i in range(32):
            self.addToMaster(self.kick, pos)
            num_beats = random.randrange(0, 4, 1)
            print(num_beats)

            ind = random.randrange(0, 2, 1)
            note = self.s[ind * len(self.s) / 4:(ind + 1) * (len(self.s) / 4)]
            for j in range(num_beats):
                self.addToMaster(self.getSegmentWithEffect(note, librosa.effects.pitch_shift, 22050, n_steps=random.randrange(-12, 12, 1)), pos + (j * math.floor(self.beat / num_beats)))

            pos += self.beat

    def inClassSong(self):
        s = AudioSegment.from_file("nggyu.mp3")
        chorus = s[43200:60000]

        front_ptr = 0
        back_ptr = len(chorus)

        master = AudioSegment.silent(0)
        center = 0

        while front_ptr < back_ptr:
            if (front_ptr < (len(chorus) / 6)):
                center = center + 1
            else:
                center = center - 1

            sample_length = np.random.exponential(200)
            sample_length = min(500, sample_length)
            print("Sample Length : " + str(sample_length))

            pitch_shift_front = np.random.normal(center, 2)
            pitch_shift_front = math.floor(pitch_shift_front)
            print("Pitch Front: " + str(pitch_shift_front))

            pitch_shift_back = np.random.normal(center, 2)
            pitch_shift_back = math.floor(pitch_shift_back)
            print("Pitch Back: " + str(pitch_shift_back))

            stutter_n = np.random.exponential(2)
            stutter_n = math.floor(min(5, stutter_n))
            print("Stutter: " + str(stutter_n))

            reverb_val = np.random.geometric(0.05)
            reverb_val = max(1, reverb_val)
            reverb_val = min(100, reverb_val)
            print("Reverb Room Size: " + str(reverb_val))

            fx_front = (
                AudioEffectsChain()
                    .pitch(100 * pitch_shift_front)
                    .reverb(reverb_val)
            )
            front = self.getSegmentWithEffect(chorus[front_ptr:front_ptr + sample_length], fx_front)
            master = master + (front * stutter_n)

            noise = WhiteNoise().to_audio_segment(200, -15)
            master = master + noise

            fx_back = (
                AudioEffectsChain()
                    .pitch(100 * pitch_shift_back)
                    .reverse()
                    .reverb(reverb_val)
            )
            back = self.getSegmentWithEffect(chorus[back_ptr - sample_length:back_ptr], fx_back)
            master = master + (back * stutter_n)
            master = master + noise

            front_ptr = front_ptr + sample_length
            back_ptr = back_ptr - sample_length

        play(master)

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

        return segment[densest*dur:min((densest+1)*dur, len(segment))], densest*dur, (densest+1)*dur

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

    def getSegmentWithEffectOverTime(self, segment, effectFunctionOverTime, *args, **kwargs):
        i = 0
        # y_affected = np.array()
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        temp_affected_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)

        chunk_size = math.floor(sr / 10)

        while i < len(y) - 1:
            print("On " + str(i) + " of " + str(len(y)))
            effectFunctionAtTime = effectFunctionOverTime(i / sr)
            y[i:min(i+chunk_size, len(y))] = effectFunctionAtTime(y[i:min(i+chunk_size, len(y))], *args, **kwargs)
            i = i + chunk_size

        librosa.output.write_wav(temp_affected_filename, y, sr)

        return AudioSegment.from_file(temp_affected_filename)

    def addToMaster(self, segment, position):
        if len(segment) + position > len(self.master):
            self.master = self.master + AudioSegment.silent((len(segment) + position) - len(self.master))

        self.master = self.master.overlay(segment, position=position)

        return len(segment) + position

class Curve:
    def __init__(self, func, freq=2, amp=1):
        self.func = func
        self.freq = freq
        self.amp = amp

    def val(self, t):
        return abs(self.amp * self.func(self.freq * t)) + 0.00001

wc = WordComp('cower')
