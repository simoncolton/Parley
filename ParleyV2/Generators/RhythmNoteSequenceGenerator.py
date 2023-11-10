import copy
from ParleyV2.Utils.RhythmUtils import *
from ParleyV2.Utils.TimingUtils import *


class RhythmNoteSequenceGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        bar_start_volume = None
        for bar in composition.bars:
            spec = self.gen_spec.instantiate_me(composition, bar)
            bar_end_volume = int(spec["volume"])
            volume_diff = 0 if bar_start_volume is None else bar_end_volume - bar_start_volume
            if bar.note_sequences is None:
                bar.note_sequences = []
            rhythm_strings = spec["rhythm"]
            moving64th = 0
            NoteSequence.next_note_sequence_num += 1
            note_sequence = NoteSequence(note_sequence_num=NoteSequence.next_note_sequence_num,
                                         instrument_num=spec["instrument_num"], voice_id=spec["voice_id"],
                                         track_num=spec["track_num"], channel_num=spec["channel_num"],
                                         notes=[], bar_num=bar.bar_num)
            composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
            bar.note_sequences.append(note_sequence)
            if rhythm_strings is not None:
                for rhythm_string in rhythm_strings:
                    timing = TimingUtils.get_timing(rhythm_string)
                    volume = bar_end_volume if bar_start_volume is None else bar_start_volume + ((timing.start64th/64) * volume_diff)
                    volume = int(volume)
                    if timing.start64th > moving64th:
                        rest_timing = Timing(start64th=moving64th, duration64ths=timing.start64th - moving64th)
                        rest = Note(pitch=None, volume=0, note_type="backbone",
                                    timing=rest_timing, note_sequence_num=note_sequence.note_sequence_num,
                                    bar_num=note_sequence.bar_num, track_note_num=None, tags={})
                        note_sequence.notes.append(rest)
                    chord_for_note = None
                    for chord_ind in range(0, len(bar.chord_nums) - 1):
                        chord1_num = bar.chord_nums[chord_ind]
                        chord2_num = bar.chord_nums[chord_ind + 1]
                        chord1 = composition.chords_hash[chord1_num]
                        chord2 = composition.chords_hash[chord2_num]
                        if chord1.timing.start64th <= timing.start64th <= chord2.timing.start64th:
                            chord_for_note = chord1
                    if chord_for_note is None:
                        chord_for_note = composition.chords_hash[bar.chord_nums[-1]]
                    moved_pitches = []
                    mid_pitch = chord_for_note.pitches[1]
                    moved_mid_pitch = MusicUtils.map_pitch_to_focal_pitch(mid_pitch, spec["focal_pitch"])
                    diff1 = chord_for_note.pitches[1] - chord_for_note.pitches[0]
                    diff2 = chord_for_note.pitches[2] - chord_for_note.pitches[1]
                    moved_pitches = [moved_mid_pitch - diff1, moved_mid_pitch, moved_mid_pitch + diff2]
                    pitch_offset = spec["octave_offset"] * 12
                    pitch = moved_pitches[spec["backbone_note"] - 1] + pitch_offset
                    #pitch = MusicUtils.map_pitch_to_focal_pitch(pitch, spec["focal_pitch"])
                    note = Note(pitch=pitch, volume=volume, note_type="backbone",
                                timing=timing, chord_num=chord_for_note.chord_num,
                                note_sequence_num=note_sequence.note_sequence_num, bar_num=note_sequence.bar_num,
                                track_note_num=None, tags={})
                    note_sequence.notes.append(note)
                    moving64th = timing.start64th + timing.duration64ths
                if moving64th < 64:
                    rest_timing = Timing(start64th=moving64th, duration64ths=64 - moving64th)
                    rest = Note(pitch=None, volume=0, note_type="backbone",
                                timing=rest_timing, note_sequence_num=note_sequence.note_sequence_num,
                                bar_num=note_sequence.bar_num,
                                track_note_num=None, tags={})
                    note_sequence.notes.append(rest)
            bar_start_volume = bar_end_volume
        return composition
