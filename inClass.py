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
        front = self.get_segment_with_effect(chorus[front_ptr:front_ptr + sample_length], fx_front)
        master = master + (front * stutter_n)

        noise = WhiteNoise().to_audio_segment(200, -15)
        master = master + noise

        fx_back = (
            AudioEffectsChain()
                .pitch(100 * pitch_shift_back)
                .reverse()
                .reverb(reverb_val)
        )
        back = self.get_segment_with_effect(chorus[back_ptr - sample_length:back_ptr], fx_back)
        master = master + (back * stutter_n)
        master = master + noise

        front_ptr = front_ptr + sample_length
        back_ptr = back_ptr - sample_length

    play(master)