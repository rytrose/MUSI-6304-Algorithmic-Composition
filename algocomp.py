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
from music21 import *
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

        pos = 0
        # pos = self.intro()
        # pos = self.transition_morph_to_beat(pos, 4)
        # self.club_beat(pos)
        self.chordal(pos)

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
        #         .overdrive(Curve(math.sin, 0.5).val(t))
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
        pos = 4 * self.beat
        self.addToMaster(self.s, pos)
        pos += 4 * self.beat
        for i in range(2):
            self.addToMaster(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-3*i), pos)
            pos += 1 * self.beat
            self.addToMaster(apply_gain_stereo(self.s, left_gain=-3*i, right_gain=1.0), pos)
            pos += 1 * self.beat
        for i in range(2):
            self.addToMaster(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-6 - (3*i)), pos)
            pos += 0.5 * self.beat
            self.addToMaster(apply_gain_stereo(self.s, left_gain=-6 - (3*i), right_gain=1.0), pos)
            pos += 0.5 * self.beat

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

    def transition_morph_to_beat(self, pos, iterations):
        sliceLen = len(self.s) / 4

        i = sliceLen

        while i < self.beat:
            for j in range(3):
                pos = self.addToMaster(self.s[j * len(self.s) / 4:(j + 1) * (len(self.s) / 4)], pos + (i - sliceLen))
            pos = self.addToMaster(AudioSegment.silent(sliceLen), pos + (i - sliceLen))

            i += (self.beat - sliceLen) / iterations

        return pos

    def club_beat(self, pos):
        for i in range(32):
            self.addToMaster(self.kick, pos)
            num_beats = random.randrange(0, 4, 1)

            ind = random.randrange(0, 2, 1)
            note = self.s[ind * len(self.s) / 4:(ind + 1) * (len(self.s) / 4)]
            for j in range(num_beats):
                self.addToMaster(self.getSegmentWithEffect(note, librosa.effects.pitch_shift, 22050, n_steps=random.randrange(-12, 12, 1)), pos + (j * math.floor(self.beat / num_beats)))

            pos += self.beat
        return pos

    def chordal(self, pos):
        bass, _, _ = self.getDense(self.s, self.beat / 2)
        bass = self.getSegmentWithEffect(bass, librosa.effects.pitch_shift, 22050, n_steps=-24)
        lp_fx = (
            AudioEffectsChain()
                .lowpass(1500)
        )
        bass = self.getSegmentWithEffect(bass, lp_fx)
        bass = self.getSegmentWithEffect(bass, librosa.effects.time_stretch, 0.25)
        bass, _, _ = self.getDense(bass, self.beat)
        root = self.estimatePitch(bass)

        for i in [0, 4, 7, -1]:
            note = self.s[0:(1 * (len(self.s))) / 4]
            note = self.matchPitch(note, root, i)
            note = self.getSegmentWithEffect(note, librosa.effects.time_stretch, len(note) / self.beat)
            note = note[0:min(self.beat, len(note) - 1)]
            print(self.beat)
            print(len(note))

            # cmaj7_chord = self.makeChord(note, [-24, -8, 7, 23])
            # dmaj7_chord = self.makeChord(self.matchPitch(note, self.estimatePitch(note), 2), cmaj7.pitchClasses)

            self.addToMaster(bass * 2, pos)
            pos = self.addToMaster(note * 2, pos)
            # self.addToMaster(cmaj7_chord * 4, pos)
            # self.addToMaster(cmaj7_chord * 4, pos + (4 * self.beat))

        note = self.s[0:(1 * (len(self.s))) / 4]
        note = self.matchPitch(note, root, 0)
        note = self.getSegmentWithEffect(note, librosa.effects.time_stretch, len(note) / (4 * self.beat))
        note, _, _ = self.getDense(note, self.beat)
        note = self.getSegmentWithEffect(note, librosa.effects.time_stretch, len(note) / (4 * self.beat))
        note = note[0:min(4*self.beat, 4*(len(note) - 1))]
        self.addToMaster(bass * 4, pos)
        self.addToMaster(self.makeChord(note, [-1, 0, 4, 7]), pos)


        # fmaj7 = chord.Chord(["F3", "A3", "C4", "E4"])
        # print(fmaj7.pitchClasses)

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
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        temp_affected_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)

        chunk_size = math.floor(sr / 4)

        while i < len(y) - 1:
            print("On " + str(i) + " of " + str(len(y)))
            effectFunctionAtTime = effectFunctionOverTime(i / sr)
            y[i:min(i+chunk_size, len(y))] = effectFunctionAtTime(y[i:min(i+chunk_size, len(y))], *args, **kwargs)
            i = i + chunk_size

        librosa.output.write_wav(temp_affected_filename, y, sr)

        return AudioSegment.from_file(temp_affected_filename)

    def makeChord(self, segment, chord_list):
        final_chord = AudioSegment.silent(len(segment))

        root = self.estimatePitch(segment)

        for val in chord_list:
            final_chord = final_chord.overlay(self.matchPitch(segment, root, val))

        return final_chord

    def estimatePitch(self, segment):
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)
        chroma_fb = librosa.feature.chroma_stft(y, sr)
        mean = np.mean(chroma_fb, axis=1)
        ind = np.argmax(mean)

        return ind

    def matchPitch(self, segment, reference, difference):
        i = 0
        segment_pitch = self.estimatePitch(segment)
        dest = (reference + difference) % 12
        while segment_pitch % 12 != dest:
            segment = self.getSegmentWithEffect(segment, librosa.effects.pitch_shift, 22050, n_steps=reference - (segment_pitch - difference))
            segment_pitch = self.estimatePitch(segment)
            if i > 5:
                break
            i += 1

        if i > 5:
            print("Did not converge, off by:" + str(reference - (segment_pitch - difference)))

        return segment

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
        return self.amp * self.func(self.freq * t)

wc = WordComp('cower')
