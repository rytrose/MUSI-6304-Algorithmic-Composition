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
import re

app_id = oxford_cred.app_id
app_key = oxford_cred.app_key

class WordComp:
    def __init__(self, word, poem=False):
        self.word = word.lower()
        self.file_name = ""
        self.poem = poem

        if self.poem:
            self.file_name = self.word
            self.word = self.word[:-4]
            self.voices = []
            self.current_voices = {}
            self.get_poem_sound_files()
            self.generate_poem_song()
        else:
            self.get_word_sound_file()
            self.generate_song()

        try:
            self.clean_files()
        except:
            pass

    # --------------------------------------------------------------------------------
    # get_word_sound_file()
    #   Retrieves the pronunciation file for the given word if not already downloaded
    # --------------------------------------------------------------------------------
    def get_word_sound_file(self):
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
                            self.file_name = self.word + '/' + str(f.name)

            # Download file and make new directory
            if not found:
                r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/' + self.word,
                                 headers={'app_id': app_id, 'app_key': app_key})
                file_array = nested_lookup('audioFile', r.json())
                file_url = file_array[0]
                self.file_name = self.word + '/' + file_url.split('/')[-1]

                print("Downloading file.")
                Path('./' + self.word).mkdir()
                urllib.request.urlretrieve(file_url, self.file_name)
            else:
                print("File exists")
        except:
            print("Unable to get a sound file for this word, please try a different word.")

    # --------------------------------------------------------------------------------
    # get_poem_sound_files()
    #   Retrieves the pronunciation files for the given words if not already downloaded
    # --------------------------------------------------------------------------------
    def get_poem_sound_files(self):

        # Parse poem into words
        poem = []
        with open(self.file_name, 'r') as poem_file:
            poem = poem_file.read()
            poem = re.findall(r'\b[^\W\d_]+\b', str(poem))
            poem = [w.lower() for w in poem]
            self.words = poem

        # Get sound files for all words
        if self.words:
            self.poem_file_names = []

            # Look for this poem directory
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
                            if str(f.name).split('_')[0] in self.words:
                                self.poem_file_names.append(self.word + '/' + str(f.name))

                if not found:
                    # Make poem directory
                    Path('./' + self.word).mkdir()

                    # Download all word sound files
                    for w in self.words:
                        try:
                            r = requests.get('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/' + w,
                                             headers={'app_id': app_id, 'app_key': app_key})
                            file_array = nested_lookup('audioFile', r.json())
                            file_url = file_array[0]
                            self.poem_file_names.append(self.word + '/' + file_url.split('/')[-1])

                            print("Downloading word: " + w)
                            urllib.request.urlretrieve(file_url, self.poem_file_names[-1])
                        except:
                            print("Unable to find the word {}, continuing on.".format(w))
                else:
                    print("Files exist.")

            except:
                print("Unable to access file system.")

    # --------------------------------------------------------------------------------
    # generate_poem_song()
    #   Establishes master track, calls the various sections and transitions
    # --------------------------------------------------------------------------------
    def generate_poem_song(self):
        # Establish master segment
        self.master = AudioSegment.silent(0)

        # Trim the collected word file
        for i, s in enumerate(self.poem_file_names):
            word = s.split('/')[1].split('_')[0]
            y, sr = librosa.load(s, 44100)
            y_trim, _ = librosa.effects.trim(y)
            librosa.output.write_wav(self.word + "/trim_" + word + ".wav", y_trim, sr)

        # Create first word segment
        self.current_word_index = -1
        self.change_main_segment(0)

        # Set tempo (set in BPM, calculated to mspb)
        bpm_tempo = 134
        self.beat = math.floor(60000 / bpm_tempo)

        # Generate the voices used throughout
        self.generate_voices(None)

        # Call the sections and transitions of the piece
        pos = 0

        # Play intro
        pos = self.intro_poem(pos)

        # Play word exploration sections
        for i in range(len(self.words)):
            self.change_main_segment(i)
            pos = self.explore_word(pos)

        # Play the main sections of the piece
        pos = self.beef_1(pos)
        pos = self.beef_2(pos)
        pos = self.beef_3(pos)

        # Play the outro
        pos = self.outro(pos)

        # Play the master track
        # play(self.master + AudioSegment.silent(1000))
        self.master.export("change.wav", format="wav")

    # --------------------------------------------------------------------------------
    # intro_poem()
    #   Plays all words of the poem in succession
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def intro_poem(self, pos):
        for i in range(len(self.words)):
            self.change_main_segment(i)
            self.add_to_master(self.s.fade_out(10), pos)
            pos += len(self.s) - 200

        return pos

    # --------------------------------------------------------------------------------
    # generate_voices()
    #   Generates three types of voices (sustain, bass, drone, note) from each of the
    #       words of the poem
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def generate_voices(self, pos):
        for i in range(len(self.words)):
            self.change_main_segment(i)
            # Create 3 beat sustain_voice
            sustain_voice = self.s[math.floor(len(self.s) / 4): 2 * math.floor(len(self.s) / 4)]
            sustain_voice = self.get_segment_with_effect(sustain_voice, librosa.effects.pitch_shift, 22050, n_steps=12)
            sustain_voice = self.get_segment_with_effect(sustain_voice, librosa.effects.time_stretch, 0.05)
            sustain_voice, _, _ = self.get_dense(sustain_voice, self.beat * 8)
            sustain_voice = self.get_segment_with_effect(sustain_voice, librosa.effects.time_stretch, 2)
            sustain_voice, _, _ = self.get_dense(sustain_voice, self.beat / 32)
            sustain_voice = sustain_voice.fade_in(2).fade_out(2)*32*4
            sustain_voice = self.get_segment_with_effect(sustain_voice + AudioSegment.silent(4000), (AudioEffectsChain().lowpass(4000).highpass(500).reverb(80)))
            sustain_voice = sustain_voice[1800:3200].fade_in(40).fade_out(600)
            sustain_voice = sustain_voice[0:min(len(sustain_voice), self.beat * 3)]
            sustain_voice = sustain_voice.fade_in(10).fade_out(10)

            # Eighth note voice
            note_voice = self.s.reverse()
            note_voice, _, _ = self.get_dense(note_voice, self.beat)
            note_voice = self.get_segment_with_effect(note_voice, librosa.effects.time_stretch, 0.5)
            note_voice = self.get_segment_with_effect(note_voice, (AudioEffectsChain().lowpass(4000, q=4)))
            note_voice, _, _ = self.get_dense(note_voice, self.beat / 4)
            note_voice = self.get_segment_with_effect(note_voice, librosa.effects.time_stretch, 0.5)
            note_voice = note_voice.fade_in(10).fade_out(10)
            note_voice = self.match_pitch(note_voice, self.estimate_pitch(self.s), 0)

            # 8 beat drone
            drone_voice = self.s[(len(self.s)) / 4:(2 * (len(self.s))) / 4]
            drone_voice = self.get_segment_with_effect(drone_voice, librosa.effects.time_stretch, len(drone_voice) / (4 * self.beat))
            drone_voice, _, _ = self.get_dense(drone_voice, self.beat)
            drone_voice = self.get_segment_with_effect(drone_voice, librosa.effects.time_stretch, len(drone_voice) / (8 * self.beat))
            drone_voice = self.get_segment_with_effect(drone_voice, (AudioEffectsChain().lowpass(3000).phaser().overdrive(gain=5)))
            crossfade = 500
            drone_voice = drone_voice[math.floor(2 * self.beat) - (crossfade / 4):math.floor(6 * self.beat) + (crossfade / 4)]
            drone_voice = drone_voice.append(drone_voice, crossfade=crossfade)
            drone_voice = drone_voice.fade_in(10).fade_out(10)

            # Creating the bass
            # Grab the densest eighth note of the word
            bass_voice, _, _ = self.get_dense(self.s, self.beat / 2)
            # Drop it two octaves
            bass_voice = self.get_segment_with_effect(bass_voice, librosa.effects.pitch_shift, 22050, n_steps=-24)
            # Restrict frequencies to 100-1500 Hz
            filter_fx = (
                AudioEffectsChain()
                    .lowpass(1500)
                    .highpass(100)
            )
            bass_voice = self.get_segment_with_effect(bass_voice, filter_fx)
            # Stretch it out 4x
            bass_voice = self.get_segment_with_effect(bass_voice, librosa.effects.time_stretch, 0.25)
            # Get the densest beat from this latest stretch
            bass_voice, _, _ = self.get_dense(bass_voice, self.beat)
            # Ensure it's a full beat long
            if (len(bass_voice) < self.beat):
                bass_voice = bass_voice + AudioSegment.silent(self.beat - len(bass_voice))
            bass_voice = bass_voice.fade_in(10).fade_out(10) + 4

            # Pitch all the voices to the note, which has the cleanest defined
            root = self.estimate_pitch(note_voice)
            bass_voice = self.match_pitch(bass_voice, root, 0)
            sustain_voice = self.match_pitch(sustain_voice, root, 0)
            drone_voice = self.match_pitch(drone_voice, root, 0)

            self.voices.append({
                "note_voice": note_voice,
                "bass_voice": bass_voice,
                "sustain_voice": sustain_voice,
                "drone_voice": drone_voice
            })

            # SOUND DEMO
            # self.add_to_master(bass_voice * 4, pos)
            # pos += self.beat * 4
            # self.add_to_master((sustain_voice + AudioSegment.silent(self.beat)) * 2, pos)
            # pos += self.beat * 8
            # self.add_to_master(note_voice * 8, pos)
            # pos += self.beat * 4
            # self.add_to_master(drone_voice, pos)
            # pos += self.beat * 8

        return pos

    # --------------------------------------------------------------------------------
    # explore_word()
    #   Uses panning and features some of the voices generated from this word.
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def explore_word(self, pos):
        pos, word_rhythm = self.explore_word_section_1(pos)
        # pos = self.explore_word_section_2(pos, word_rhythm, bass_voice, sustain_voice, note_voice, drone_voice)
        return pos

    # --------------------------------------------------------------------------------
    # explore_word_section_1()
    #   Establishes a rhythmic pattern for the word, and demonstrates the derived voices
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def explore_word_section_1(self, pos):
        bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()

        rhythm_length = 8
        word_rhythm = [random.choice([1, 2, 3, 4]) for _ in range(rhythm_length)]
        rhythm_sum = sum(word_rhythm)

        while rhythm_sum > rhythm_length:
            word_rhythm = word_rhythm[0:-1]
            rhythm_sum = sum(word_rhythm)

        word_pos = 0
        for i in range(3):
            for ind, b in enumerate(word_rhythm):
                self.add_to_master(pan(self.s, (((2 * ind) / (len(word_rhythm) - 1)) * 0.8 - 0.8)), pos + (word_pos * self.beat))
                word_pos += b

            if word_pos % rhythm_length != 0:
                word_pos += (rhythm_length - (word_pos % rhythm_length))

        bass_pos = rhythm_length * self.beat
        for i in range(2):
            self.add_to_master(bass_voice, pos + bass_pos)
            bass_pos += 4 * self.beat
        for i in range(4):
            self.add_to_master(bass_voice, pos + bass_pos)
            bass_pos += 2 * self.beat

        drone_pos = rhythm_length * 2 * self.beat
        self.add_to_master(drone_voice.fade_in(7 * self.beat), pos + drone_pos)

        note_pos = 0
        note_line = AudioSegment.silent(0)
        for i in range(rhythm_length * 2):
            note_line += note_voice + self.get_segment_with_effect(note_voice, librosa.effects.pitch_shift, 22050, n_steps=2) + \
                         self.get_segment_with_effect(note_voice, librosa.effects.pitch_shift, 22050, n_steps=random.choice([4, 5, 7, 9]))
        note_line = note_line - 16

        self.add_to_master(note_line.fade_in(rhythm_length * 4 * self.beat), pos + note_pos)

        pos += rhythm_length * 3 * self.beat
        return pos, word_rhythm

    # # NOT USED
    # def explore_word_section_2(self, pos, word_rhythm):
    #     bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
    #
    #     original_chord_array = [-1, 0, 4, 7]
    #     chord1, chord1_notes = self.make_chord(drone_voice, original_chord_array)
    #     chord1 = chord1 - 14
    #     chord1 = chord1.fade_in(40).fade_out(20)
    #     new_root = random.choice([-5, -1, 4, 7])
    #     new_chord_array = [new_root - 1, new_root, new_root + 4, new_root + 7]
    #     chord2, chord2_notes = self.make_chord(drone_voice, new_chord_array)
    #     chord2 = chord2 - 14
    #     chord2 = chord2.fade_in(40).fade_out(20)
    #
    #     eight_bar_word = self.get_segment_with_effect(self.s, librosa.effects.time_stretch, len(self.s) / (self.beat * 8))
    #     word1 = self.match_pitch(eight_bar_word, self.estimate_pitch(chord1_notes[1]), 0)
    #     word2 = self.match_pitch(eight_bar_word, self.estimate_pitch(chord1_notes[1]), new_root)
    #
    #
    #     self.add_to_master(word1 + (word2.fade_out(self.beat * 2)), pos)
    #     pos = self.add_to_master(chord1 + (chord2.fade_out(self.beat * 2)), pos)
    #
    #     return pos

    # --------------------------------------------------------------------------------
    # beef_1()
    #   Establishes the main melody, via the sustain voice
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def beef_1(self, pos):
        word_pos = pos
        for i in range(4):
            for j in range(len(self.words)):
                self.change_main_segment(j)
                bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
                if i == 0:
                    self.add_to_master(self.s, word_pos)
                elif i == 1:
                    self.add_to_master(self.s - (j * 2), word_pos)
                elif i == 2:
                    self.add_to_master(self.s - 12, word_pos)

                self.add_to_master(sustain_voice, word_pos)
                word_pos += 2 * self.beat

        self.change_main_segment(len(self.words) - 1)
        bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
        drone_line = drone_voice[0:5 * self.beat] - 6
        for i in range(len(self.words) - 1):
            self.change_main_segment(len(self.words) - (i + 2))
            bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
            drone_line = drone_line.append(drone_voice[0:5 * self.beat] - 6, crossfade=self.beat)

        self.add_to_master(drone_line.fade_out(self.beat), pos)

        pos += (8 * self.beat * len(self.words))

        return pos

    # --------------------------------------------------------------------------------
    # beef_2()
    #   Uses the sustain melody, bass, and stuttering words
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def beef_2(self, pos):
        note_line = AudioSegment.silent(0)
        for i in range(len(self.words)):
            self.change_main_segment(i)
            bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
            note = self.match_pitch(note_voice, self.estimate_pitch(sustain_voice), 0)
            note_line += note + AudioSegment.silent(math.floor((4/3) * self.beat) - len(note))

        sustain_pos = pos
        for k in range(8):
            for i in range(len(self.words)):
                self.change_main_segment(i)
                bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
                self.add_to_master(sustain_voice, sustain_pos)
                sustain_pos += 2 * self.beat

        bass_pos = pos
        total_beats = len(self.words) * 2 * 8
        for k in range(math.floor(total_beats / 8)):
            for i in range(6):
                if i % 3 == 2:
                    bass_pos += 2 * self.beat
                ind = i % len(self.words)
                self.change_main_segment(ind)
                bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
                self.add_to_master(bass_voice, bass_pos)
                bass_pos += math.floor(self.beat / 2)
            bass_pos += self.beat

        voice_pos = pos + ((self.beat * total_beats) / 2)
        word_ind = 0
        chunks = []
        repeats = []
        while voice_pos < pos + (total_beats * self.beat):
            self.change_main_segment(word_ind)
            if len(chunks) < word_ind + 1:
                num_chunks = random.choice([1, 2, 3])
                chunks.append(num_chunks)
                repeats.append([random.choice([1, 1, 2, 3]) for _ in range(num_chunks)])
            for i in range(chunks[word_ind]):
                for j in repeats[word_ind]:
                    self.add_to_master(self.s[i * math.floor(len(self.s) / chunks[word_ind]):(i + 1) * math.floor(len(self.s) / chunks[word_ind])], voice_pos)
                    voice_pos += math.floor(self.beat * 0.25)
                voice_pos += math.floor(self.beat * random.choice([0.5, 0.5, 0.5, 0.25]))
            word_ind = (word_ind + 1) % len(self.words)

        note_line = note_line - 12
        len_sus = sustain_pos - pos
        num_note_line = math.ceil(len_sus / len(note_line))
        pos = self.add_to_master(note_line * num_note_line, pos)
        return pos

    # --------------------------------------------------------------------------------
    # beef_3()
    #   Stretches out the words as texture, uses sustain and bass rhythmically
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def beef_3(self, pos):
        pitches = []
        words = []
        for i in range(len(self.words)):
            self.change_main_segment(i)
            _, _, end = self.get_dense(self.s, 20)
            v = self.s[0:end]
            words.append(self.get_segment_with_effect(v, librosa.effects.time_stretch, len(v) / (self.beat * 6)))
            bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
            pitches.append(self.estimate_pitch(sustain_voice))

        num_beats = 64
        word_pos = pos
        w_1 = 0
        w_2 = 1 % len(self.words)
        p = 0

        while word_pos < (pos + (num_beats * self.beat)):
            self.add_to_master(self.get_segment_with_effect(words[w_1], librosa.effects.pitch_shift, 22050, n_steps=p - self.estimate_pitch(words[w_1])) - 4, word_pos)
            word_pos += self.beat * 2
            self.add_to_master(self.get_segment_with_effect(words[w_2], librosa.effects.pitch_shift, 22050, n_steps=(p - self.estimate_pitch(words[w_2])) + random.choice([6, 7])) - 4, word_pos)
            word_pos += self.beat * 4
            p = (p + 1) % len(pitches)
            w_1 = (w_1 + 2) % len(self.words)
            w_2 = (w_2 + 2) % len(self.words)

        sustain_bass_pos = pos
        word_ind = 0
        while sustain_bass_pos < (pos + (num_beats * self.beat)):
            self.change_main_segment(word_ind)
            bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
            self.add_to_master(sustain_voice[0:self.beat].fade_out(20), sustain_bass_pos)
            sustain_bass_pos += self.beat
            self.add_to_master(bass_voice, sustain_bass_pos)
            sustain_bass_pos += self.beat * 2
            word_ind = (word_ind + 1) % len(self.words)

        pos += num_beats * self.beat

        return pos

    # --------------------------------------------------------------------------------
    # outro()
    #   Draws back the texture and restates each word, finishes with the intro
    #   pos: position at which to start this section
    # --------------------------------------------------------------------------------
    def outro(self, pos):
        for i in range(len(self.words)):
            self.change_main_segment(i)
            bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
            sustain_voice_ext = sustain_voice[0:self.beat] + (sustain_voice[self.beat:2*self.beat].fade_in(10).fade_out(10) * 7)
            self.add_to_master(sustain_voice_ext.fade_out(self.beat), pos)
            self.add_to_master(bass_voice, pos)
            pos += self.beat * 2
            self.add_to_master(bass_voice, pos)
            pos += self.beat * 2
            self.add_to_master(self.s, pos)
            pos += self.beat * 4

        self.change_main_segment(0)
        bass_voice, sustain_voice, note_voice, drone_voice = self.get_current_voices()
        self.add_to_master(self.get_segment_with_effect(sustain_voice, librosa.effects.time_stretch, len(sustain_voice) / (self.beat * 16)), pos)
        self.intro_poem(pos)

        return pos

    # --------------------------------------------------------------------------------
    # get_current_voices()
    #   Returns the proper voices for the currently operating word
    # --------------------------------------------------------------------------------
    def get_current_voices(self):
        voices = self.voices[self.current_word_index]
        return voices["bass_voice"], voices["sustain_voice"], voices["note_voice"], voices["drone_voice"]

    # NOT USED
    # # --------------------------------------------------------------------------------
    # # generate_song()
    # #   Establishes master track, calls the various sections and transitions
    # # --------------------------------------------------------------------------------
    # def generate_song(self):
    #     # Establish master segment
    #     self.master = AudioSegment.silent(0)
    #
    #     # Trim the collected word file
    #     y, sr = librosa.load(self.file_name, 44100)
    #     y_trim, _ = librosa.effects.trim(y)
    #     librosa.output.write_wav(self.word + "/trim_" + self.word + ".wav", y_trim, sr)
    #
    #     # Create main word segment
    #     self.s = AudioSegment.from_file(self.word + "/trim_" + self.word + ".wav")
    #     # Add minimal reverb on word sample
    #     reverb = (
    #         AudioEffectsChain()
    #             .reverb(2)
    #     )
    #     self.s = self.get_segment_with_effect(self.s, reverb)
    #
    #     # Create percussion segments
    #     self.closed_hat = AudioSegment.from_file("perc/Closed_Hat_Ana_01.wav")
    #     self.open_hat = AudioSegment.from_file("perc/Open_Hat_19.wav")
    #     self.snare = AudioSegment.from_file("perc/Snare_09.wav")
    #     self.kick = AudioSegment.from_file("perc/Kick_016.wav")
    #     self.crash = AudioSegment.from_file("perc/Crash_13b.wav")
    #
    #     # Set tempo (set in BPM, calculated to mspb)
    #     bpm_tempo = 134
    #     self.beat = math.floor(60000 / bpm_tempo)
    #
    #     # Call the sections and transitions of the piece
    #     pos = 0
    #
    #     # pos = self.intro(pos)
    #     # pos = self.transition_morph_to_beat(pos, 4)
    #     # pos = self.club_beat(pos)
    #     # pos = self.transition_stretch(pos, 8, 4)
    #     pos = self.chordal(pos)
    #
    #     # WARNING: adding this reverb to the master sounded nice, but removed the ability to pan
    #     # reverb = (
    #     #     AudioEffectsChain()
    #     #         .reverb(2)
    #     # )
    #     # self.master = self.get_segment_with_effect(self.master, reverb)
    #
    #     # Play the master track
    #     play(self.master + AudioSegment.silent(1000))
    #     # self.master.export("draft.wav", format="wav")

    # # NOT USED
    # # --------------------------------------------------------------------------------
    # # intro()
    # #   Uses panning and repetition to get the listener acquainted with the word
    # #   pos: position at which to start this section
    # # --------------------------------------------------------------------------------
    # def intro(self, pos):
    #     # Play the word normally twice
    #     self.add_to_master(self.s, pos)
    #     pos += 4 * self.beat
    #     self.add_to_master(self.s, pos)
    #     pos += 4 * self.beat
    #
    #     # Speed up and pan
    #     for i in range(2):
    #         self.add_to_master(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-3 * i), pos)
    #         pos += 1 * self.beat
    #         self.add_to_master(apply_gain_stereo(self.s, left_gain=-3 * i, right_gain=1.0), pos)
    #         pos += 1 * self.beat
    #     for i in range(2):
    #         self.add_to_master(apply_gain_stereo(self.s, left_gain=1.0, right_gain=-6 - (3 * i)), pos)
    #         pos += 0.5 * self.beat
    #         self.add_to_master(apply_gain_stereo(self.s, left_gain=-6 - (3 * i), right_gain=1.0), pos)
    #         pos += 0.5 * self.beat
    #
    #     for i in range(8):
    #         for i in range(2):
    #             self.add_to_master(apply_gain_stereo(self.s, left_gain=-10, right_gain=-18), pos)
    #             pos += 0.065 * self.beat
    #             self.add_to_master(apply_gain_stereo(self.s, left_gain=-18, right_gain=-10), pos)
    #             pos += 0.065 * self.beat
    #
    #     # Play the word in three octaves
    #     pos += 3 * self.beat
    #     self.add_to_master(self.s, pos)
    #     self.add_to_master(self.get_segment_with_effect(self.s, librosa.effects.pitch_shift, 22050, n_steps=-12), pos)
    #     self.add_to_master(self.get_segment_with_effect(self.s, librosa.effects.pitch_shift, 22050, n_steps=12), pos)
    #     pos += self.beat
    #     return pos

    # # NOT USED
    # # --------------------------------------------------------------------------------
    # # transition_morph_to_beat()
    # #   Transitions from the pronunciation to beat-wise split of the word
    # #   pos: position at which to start this section
    # #   iterations: how many times to separate the syllables of the word before each
    # #       syllable is on a beat
    # # --------------------------------------------------------------------------------
    # def transition_morph_to_beat(self, pos, iterations):
    #     # Split the track in 4, even though we only use the first 3 chunks, as the last is often silent
    #     slice_len = len(self.s) / 4
    #
    #     i = slice_len
    #
    #     # Gradually spread apart the playback of the chunks
    #     while i < self.beat:
    #         for j in range(3):
    #             pos = self.add_to_master(self.s[j * len(self.s) / 4:(j + 1) * (len(self.s) / 4)], pos + (i - slice_len))
    #         pos = self.add_to_master(AudioSegment.silent(slice_len), pos + (i - slice_len))
    #
    #         i += (self.beat - slice_len) / iterations
    #
    #     return pos

    # # NOT USED
    # # --------------------------------------------------------------------------------
    # # transition_stretch()
    # #   Transitions by stretching the word out
    # #   pos: position at which to start this section
    # #   iterations: how many times to say the word
    # #   length: how many beats long the last iteration should be
    # # --------------------------------------------------------------------------------
    # def transition_stretch(self, pos, iterations, length):
    #     # Time stretch relative to the desired end length and the number of times to play the sound
    #     for i in range(iterations):
    #         pos = self.add_to_master(self.get_segment_with_effect(self.s, librosa.effects.time_stretch, len(self.s) / ((length / (iterations - i)) * len(self.s))), pos)
    #
    #     return pos

    # # NOT USED
    # # --------------------------------------------------------------------------------
    # # club_beat()
    # #   Section with a driving kick drum and randomly pitched and repeated words
    # #   pos: position at which to start this section
    # # --------------------------------------------------------------------------------
    # def club_beat(self, pos):
    #     # Play for 32 beats
    #     for i in range(32):
    #         # Kick on every beat
    #         self.add_to_master(self.kick, pos)
    #         # Between 0 and 3 repetitions of the word chunk per beat
    #         num_beats = random.randrange(0, 4, 1)
    #
    #         # Choose either the first or second chunk out of fourths of the word
    #         ind = random.randrange(0, 2, 1)
    #         note = self.s[ind * len(self.s) / 4:(ind + 1) * (len(self.s) / 4)]
    #         # Play the chunk num_beats times, at a random pitch between two octaves
    #         for j in range(num_beats):
    #             self.add_to_master(self.get_segment_with_effect(note, librosa.effects.pitch_shift, 22050, n_steps=random.randrange(-12, 12, 1)), pos + (j * math.floor(self.beat / num_beats)))
    #
    #         pos += self.beat
    #     return pos

    # # NOT USED
    # # --------------------------------------------------------------------------------
    # # chordal()
    # #   Section that uses chords built from portions of the word stretched as well as
    # #       a walking bass line derived from the word set in the chord notes
    # #   pos: position at which to start this section
    # # --------------------------------------------------------------------------------
    # def chordal(self, pos):
    #     # Creating the bass voice
    #     # Grab the densest eighth note of the word
    #     bass, _, _ = self.get_dense(self.s, self.beat / 2)
    #     # Drop it two octaves
    #     bass = self.get_segment_with_effect(bass, librosa.effects.pitch_shift, 22050, n_steps=-24)
    #     # Restrict frequencies to 100-1500 Hz
    #     lp_fx = (
    #         AudioEffectsChain()
    #             .lowpass(1500)
    #             .highpass(100)
    #     )
    #     bass = self.get_segment_with_effect(bass, lp_fx)
    #     # Stretch it out 4x
    #     bass = self.get_segment_with_effect(bass, librosa.effects.time_stretch, 0.25)
    #     # Get the densest beat from this latest stretch
    #     bass, _, _ = self.get_dense(bass, self.beat)
    #     # Ensure it's a full beat long
    #     if(len(bass) < self.beat):
    #         bass = bass + AudioSegment.silent(self.beat - len(bass))
    #     # Pitch detect the bass
    #     root = self.estimate_pitch(bass)
    #     # Create a 2-beat bass sample
    #     bass_half_note = self.get_segment_with_effect(bass, librosa.effects.time_stretch, 0.5)
    #     bass_half_note = bass_half_note[0:min(self.beat * 2, len(bass_half_note))]
    #     if (len(bass_half_note) < (2 * self.beat)):
    #         bass_half_note = bass_half_note + AudioSegment.silent(2 * self.beat - len(bass))
    #
    #     # Creating the chord voice
    #     # Take the first fourth of the word file
    #     note = self.s[0:(1 * (len(self.s))) / 4]
    #     # Repitch it to the bass
    #     note = self.match_pitch(note, root, 0)
    #     # Stretch the note over four beats
    #     note = self.get_segment_with_effect(note, librosa.effects.time_stretch, len(note) / (4 * self.beat))
    #     # Get the densest beat from this stretch
    #     note, _, _ = self.get_dense(note, self.beat)
    #
    #     # Stretch the note to the chord length
    #     chord_length = 16
    #     note = self.get_segment_with_effect(note, librosa.effects.time_stretch, len(note) / (chord_length * self.beat))
    #     note = note[0:min(chord_length*self.beat, chord_length*(len(note) - 1))]
    #
    #     # Specify the type of chord (major seventh chord)
    #     chord_vals = [-1, 0, 4, 7]
    #     # Make the first chord (reduce by 8dB as the layered voices make it loud
    #     chord_one = self.make_chord(note, chord_vals)[0] - 8
    #     if(len(chord_one) < chord_length * self.beat):
    #         chord_one = chord_one + AudioSegment.silent((chord_length * self.beat) - len(chord_one))
    #     # Shift the chord a fourth up
    #     chord_two = self.get_segment_with_effect(chord_one, librosa.effects.pitch_shift, 22050, n_steps=5)
    #
    #     # Transition by slowly adding three notes of the chord
    #     self.add_to_master(note.fade_in(10).fade_out(1000), pos)
    #     pos += math.floor(len(note) / 3)
    #     self.add_to_master(self.make_chord(note, [-1, 0])[0].fade_in(10).fade_out(1000)[0:math.floor((2 * len(note)) / 3)] - 4, pos)
    #     pos += math.floor(len(note) / 3)
    #     self.add_to_master(self.make_chord(note, [-1, 0, 7])[0].fade_in(10).fade_out(1000)[0:math.floor((len(note)) / 3)] - 8, pos)
    #     pos += math.floor(len(note) / 3)
    #
    #     # Copy the position for the bass
    #     bass_pos = pos
    #
    #     for section in range(2):
    #         # On the first pass, hi-hat pickup bar
    #         if (section == 0):
    #             hi_hat_pos = pos + (((chord_length * 2) - 4) * self.beat)
    #             self.add_to_master(self.closed_hat, hi_hat_pos)
    #             hi_hat_pos += self.beat
    #             self.add_to_master(self.closed_hat, hi_hat_pos)
    #             hi_hat_pos += self.beat
    #             for i in range(2):
    #                 self.add_to_master(self.closed_hat, hi_hat_pos)
    #                 hi_hat_pos += (self.beat / 2)
    #             for i in range(3):
    #                 self.add_to_master(self.closed_hat, hi_hat_pos)
    #                 hi_hat_pos += (self.beat / 3)
    #         # Hi-hat line with randomly placed triplet and quarter note bars
    #         else:
    #             trip_beat = np.random.choice(range(4))
    #             quarter_beat = np.random.choice(range(4))
    #             hi_hat_pos = pos
    #             for i in range(math.floor(chord_length / 4)):
    #                 hi_hat_pos += self.beat * trip_beat
    #                 for j in range(3):
    #                     self.add_to_master(self.closed_hat, hi_hat_pos)
    #                     hi_hat_pos += math.floor(self.beat / 3)
    #                 hi_hat_pos += self.beat * (3 - trip_beat)
    #
    #                 hi_hat_pos += self.beat * quarter_beat
    #                 self.add_to_master(self.closed_hat, hi_hat_pos)
    #                 hi_hat_pos += self.beat
    #                 hi_hat_pos += self.beat * (3 - quarter_beat)
    #
    #         # Walk the bass in half notes within the chord context
    #         for i in range(math.floor(chord_length / 2)):
    #             self.add_to_master(self.get_segment_with_effect(bass_half_note, librosa.effects.pitch_shift, 22050, n_steps=np.random.choice(chord_vals)).fade_in(10), bass_pos)
    #             bass_pos += len(bass_half_note)
    #         for i in range(math.floor(chord_length / 2)):
    #             self.add_to_master(self.get_segment_with_effect(bass_half_note, librosa.effects.pitch_shift, 22050, n_steps=np.random.choice([v + 5 for v in chord_vals])).fade_in(10), bass_pos)
    #             bass_pos += len(bass_half_note)
    #
    #         # Add the chords
    #         pos = self.add_to_master(chord_one.fade_in(200), pos)
    #         self.add_to_master(self.crash - 8, pos)
    #         pos = self.add_to_master(chord_two.fade_in(200), pos)


    # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #
    # MY API FUNCTIONS
    #
    #  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


    # --------------------------------------------------------------------------------
    # get_dense()
    #   Gets the "densest" portion of an input segment, where density is the section
    #       with the highest sum over an input duration
    #   segment: the AudioSegment to get the densest portion of
    #   dur: how long the returned segment should be
    # --------------------------------------------------------------------------------
    def get_dense(self, segment, dur):
        # Get a list of the samples
        samples = [abs(s) for s in segment.get_array_of_samples()]
        density = 0
        densest = 0

        i = 0
        # Iterate through all possible arrays of the given duration and return the one with the highest
        #   sum of the absolute value of the samples
        while i * dur < len(segment):
            this_sum = sum(samples[math.floor(i*dur*(segment.frame_rate / 1000)):min(math.floor((i+1)*dur*(segment.frame_rate / 1000)), len(samples))])
            if(this_sum > density):
                density = this_sum
                densest = i
            i = i + 1

        # Return the timestamp indices as well
        return segment[densest*dur:min((densest+1)*dur, len(segment))], densest*dur, (densest+1)*dur

    # --------------------------------------------------------------------------------
    # get_segment_with_effect()
    #   Applies a pseudo-arbitrary effect to an AudioSegment
    #   segment: the AudioSegment to be affected
    #   effect_function: the effect function, works with librosa and pysndfx
    #   *args: any arguments needed for the effect function
    #   **kwargs: any keyword arguments needed for the effect function
    # --------------------------------------------------------------------------------
    def get_segment_with_effect(self, segment, effect_function, *args, **kwargs):
        # Convert the AudioSegment to .wav for effect processing via temp files
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        temp_affected_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        # Process effect
        y, sr = librosa.load(temp_segment_filename)
        y_affected = effect_function(y, *args, **kwargs)
        librosa.output.write_wav(temp_affected_filename, y_affected, sr)
        # Return as AudioSegment
        return AudioSegment.from_file(temp_affected_filename)

    # --------------------------------------------------------------------------------
    # get_segment_with_effect_over_time()
    #   Applies a pseudo-arbitrary effect to an AudioSegment over time
    #   segment: the AudioSegment to be affected
    #   effect_function: the effect function, works with librosa and pysndfx
    #       this is a lambda function that takes t and returns an effect function
    #   *args: any arguments needed for the effect function
    #   **kwargs: any keyword arguments needed for the effect function
    # --------------------------------------------------------------------------------
    def get_segment_with_effect_over_time(self, segment, effect_function_over_time, *args, **kwargs):
        i = 0
        # Convert the AudioSegment to .wav for effect processing via temp files
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        temp_affected_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)

        # This chunk size is the block over which changing effect values are applied
        # The smaller the chunk_size, the longer processing takes
        chunk_size = math.floor(sr / 4)

        while i < len(y) - 1:
            # Print status
            print("On " + str(i) + " of " + str(len(y)))
            # Get the effect function at time t
            effect_function_at_time = effect_function_over_time(i / sr)
            # Process effect
            y[i:min(i+chunk_size, len(y))] = effect_function_at_time(y[i:min(i+chunk_size, len(y))], *args, **kwargs)
            # Iterate chunk
            i = i + chunk_size

        librosa.output.write_wav(temp_affected_filename, y, sr)
        # Return as AudioSegment
        return AudioSegment.from_file(temp_affected_filename)

    # --------------------------------------------------------------------------------
    # make_chord()
    #   Creates a chord segment from a segment and a list of semitone intervals
    #       segment: the AudioSegment to be chordified
    #       chord_list: the semitone list of intervals for the chord
    # --------------------------------------------------------------------------------
    def make_chord(self, segment, chord_list):
        final_chord = AudioSegment.silent(len(segment))
        notes_of_chord = []

        # Estimate the pitch of the input segment for building the chord with
        #   that pitch as the root
        root = self.estimate_pitch(segment)

        for val in chord_list:
            note = self.match_pitch(segment, root, val)
            notes_of_chord.append(note)
            final_chord = final_chord.overlay(note)

        return final_chord, notes_of_chord

    # --------------------------------------------------------------------------------
    # match_pitch()
    #   Returns an AudioSegment repitched to the interval difference relative to a
    #       given pitch class
    #   segment: the AudioSegment to be repitched
    #   reference: the reference pitch class for the repitching
    #   difference: the amount of steps to repitch
    # --------------------------------------------------------------------------------
    def match_pitch(self, segment, reference, difference):
        i = 0
        # Get the pitch of the input segment
        segment_pitch = self.estimate_pitch(segment)
        # Compute the desired final pitch class
        dest = (reference + difference) % 12

        # Because the librosa pitch shifting effect doesn't do the best job, test using the pitch detect
        #   to see if it's actually detected as the right pitch class, and iterate until it converges
        #   at the pitch we want, or if it tries to converge 6 times
        while segment_pitch % 12 != dest:
            segment = self.get_segment_with_effect(segment, librosa.effects.pitch_shift, 22050, n_steps=reference - (segment_pitch - difference))
            segment_pitch = self.estimate_pitch(segment)
            if i > 5:
                break
            i += 1

        # If it did not converge, print how much it is off
        if i > 5:
            print("Did not converge, off by:" + str(reference - (segment_pitch - difference)))

        return segment

    # --------------------------------------------------------------------------------
    # estimate_pitch()
    #   Uses librosa's pitch chroma to estimate a pitch class
    #   segment: the AudioSegment to be pitch estimated
    # --------------------------------------------------------------------------------
    def estimate_pitch(self, segment):
        temp_segment_filename = self.word + "/" + str(uuid.uuid4()) + ".wav"
        segment.export(temp_segment_filename, format="wav")
        y, sr = librosa.load(temp_segment_filename)
        # Pitch is the highest chroma value from the mean over time of the segment
        # This is meant to be used on short snippets or it isn't accurate
        chroma_fb = librosa.feature.chroma_stft(y, sr)
        mean = np.mean(chroma_fb, axis=1)
        ind = np.argmax(mean)

        return ind

    # --------------------------------------------------------------------------------
    # change_main_segment()
    #   Changes the file in self.s to be the desired from the poem
    #   index: the index of the word in the poem to be changed to
    # --------------------------------------------------------------------------------
    def change_main_segment(self, index):
        if index == self.current_word_index:
            return
        if index < len(self.words):
            self.s = AudioSegment.from_file(self.word + "/trim_" + self.words[index] + ".wav")
            # Add minimal reverb on word sample
            reverb = (
                AudioEffectsChain()
                    .reverb(2)
            )
            self.s = self.get_segment_with_effect(self.s, reverb)
            if len(self.voices) == len(self.words):
                self.change_voices(index)
            self.current_word_index = index
            print("Word is now '{}'".format(self.words[index]))
        else:
            print("Word index out of range.")

    # --------------------------------------------------------------------------------
    # change_voices()
    #   Helper to change the voices to the current word
    #   index: the index of the word in the poem to be changed to
    # --------------------------------------------------------------------------------
    def change_voices(self, index):
        self.current_word_index = index
        self.current_voices = self.voices[index]

    # --------------------------------------------------------------------------------
    # add_to_master()
    #   Adds a given segment to the master AudioSegment at the given position,
    #       allocating silence if need be
    #   segment: the AudioSegment to be added to the master track
    #   position: the position on the master track to place the input segment
    # --------------------------------------------------------------------------------
    def add_to_master(self, segment, position):
        # If adding the segment increases the length of master, allocate the silence needed
        if len(segment) + position > len(self.master):
            self.master = self.master + AudioSegment.silent((len(segment) + position) - len(self.master))

        # Overlay the segment on master
        self.master = self.master.overlay(segment, position=position)

        return len(segment) + position

    # --------------------------------------------------------------------------------
    # clean_files()
    #   Deletes the temp .wav files used when adding effects
    # --------------------------------------------------------------------------------
    def clean_files(self):
        word_dir = Path('./' + self.word)
        files = [f for f in word_dir.iterdir() if f.is_file()]
        for f in files:
            if self.poem:
                if str(f) not in self.poem_file_names:
                    os.remove(str(f))
            else:
                if str(f) != self.file_name:
                    os.remove(str(f))

# --------------------------------------------------------------------------------
# Curve
#   Defines a function that returns a value given a time
#   func: the equation of the curver
# --------------------------------------------------------------------------------
class Curve:
    def __init__(self, func, freq=2, amp=1):
        self.func = func
        self.freq = freq
        self.amp = amp

    # Returns the value of func at time t
    def val(self, t):
        return self.amp * self.func(self.freq * t)

# This builds and plays the song
# Try changing the word!
wc = WordComp('change_quote.txt', poem=True)
# wc = WordComp('garlic')