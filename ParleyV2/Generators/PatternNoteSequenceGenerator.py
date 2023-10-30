import copy, random
from ParleyV2.Utils.RhythmUtils import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Utils.VolumeUtils import *

@dataclass
class MelodyPattern:
    intervals: [] = None
    timing_fractions: [] = None
    rests: [] = None


class PatternNoteSequenceGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        bar_start_volume = None
        patterns_hash = {}
        patterns = []
        for letter in self.gen_spec.get_value("pattern_form"):
            if letter in patterns_hash:
                patterns.append(patterns_hash[letter])
            else:
                patterns.append(self.get_pattern())
        previous_spec = None
        num_patterns = len(patterns)
        for bar in composition.bars:
            pattern = patterns[bar.bar_num % num_patterns]
            spec = self.gen_spec.instantiate_me(composition, bar)

            bar_end_volume = int(spec["volume"])
            volume_diff = 0 if bar_start_volume is None else bar_end_volume - bar_start_volume
            if bar.note_sequences is None:
                bar.note_sequences = []
            volume = bar_end_volume if bar_start_volume is None else bar_start_volume + (
                        (chord.timing.start64th / 64) * volume_diff)
            volume = int(volume)

            note_sequence = NoteSequence(note_sequence_num=NoteSequence.next_note_sequence_num,
                                         instrument_num=spec["instrument_num"], voice_id=spec["voice_id"],
                                         track_num=spec["track_num"], channel_num=spec["channel_num"],
                                         notes=[], bar_num=bar.bar_num)
            composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
            bar.note_sequences.append(note_sequence)

            for chord_num in bar.chord_nums:
                chord = composition.chords_hash[chord_num]
                notes = self.get_notes_for_pattern(spec, note_sequence.note_sequence_num, note_sequence.bar_num,
                                                   chord, pattern, volume)
                note_sequence.notes.extend(notes)

            VolumeUtils.change_volumes(spec, previous_spec, bar, note_sequence)

            bar_start_volume = bar_end_volume
            NoteSequence.next_note_sequence_num += 1
            previous_spec = spec

        return composition

    def get_pattern(self):
        pattern = MelodyPattern([], [], [])
        num_notes = self.gen_spec.get_value("num_notes_in_pattern")
        while len(pattern.intervals) < num_notes:
            interval = random.randint(0, 7)
            diff = 0 if len(pattern.intervals) == 0 else abs(pattern.intervals[-1] - interval)
            if diff <= 8 and (len(pattern.intervals) == 0 or interval != pattern.intervals[-1]):
                pattern.intervals.append(interval)
        pattern.timing_fractions = [1/len(pattern.intervals) for i in range(0, len(pattern.intervals))]
        num_rests = self.gen_spec.get_value("num_pattern_rests")
        while len(pattern.rests) < num_rests:
            rest_pos = random.randint(0, len(pattern.intervals))
            if rest_pos not in pattern.rests:
                pattern.rests.append(rest_pos)
        return pattern

    def get_notes_for_pattern(self, spec, note_sequence_num, bar_num, chord, pattern, volume):
        notes = []
        s64 = 0
        focal_pitch = spec["focal_pitch"]
        for note_num in range(0, len(pattern.intervals)):
            pitch = MusicUtils.get_note_from_chord_interval(chord, focal_pitch, pattern.intervals[note_num])
            d64 = int(pattern.timing_fractions[note_num] * chord.timing.duration64ths)
            timing = Timing(chord.timing.start64th + s64, d64)
            note = Note(pitch=pitch, volume=volume, note_type="backbone",
                        timing=timing, chord_num=chord.chord_num,
                        note_sequence_num=note_sequence_num, bar_num=bar_num, track_note_num=None)
            s64 += d64
            if note_num not in pattern.rests:
                notes.append(note)
        return notes
