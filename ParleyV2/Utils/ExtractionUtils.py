class ExtractionUtils:

    def get_track_nums(composition):
        track_nums = []
        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num not in track_nums:
                    track_nums.append(note_sequence.track_num)
        track_nums.sort()
        return track_nums

    def get_notes_in_composition(composition):
        all_notes = []
        for track_num in ExtractionUtils.get_track_nums(composition):
            all_notes.extend(ExtractionUtils.get_notes_for_track_num(composition, track_num))
        return all_notes

    def get_notes_for_track_num(composition, track_num):
        notes_for_track_num = []
        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == track_num:
                    notes_for_track_num.extend(note_sequence.notes)
        return notes_for_track_num

    def get_episode_notes_for_track_num(composition, episode_num, track_num):
        episode_notes_for_track_num = []
        for bar in composition.bars:
            if bar.episode_num == episode_num:
                for note_sequence in bar.note_sequences:
                    if note_sequence.track_num == track_num:
                        episode_notes_for_track_num.extend(note_sequence.notes)
        return episode_notes_for_track_num

    def get_note_sequences_for_track_num(composition, track_num):
        note_sequences = []
        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == track_num:
                    note_sequences.append(note_sequence)
        return note_sequences