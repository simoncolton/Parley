import copy
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Utils.VolumeUtils import *


class BackboneMelodyGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        previous_note_sequence = None
        previous_spec = None
        for bar in composition.bars:
            spec = self.gen_spec.instantiate_me(composition, bar)
            NoteSequence.next_note_sequence_num += 1
            note_sequence = NoteSequence(note_sequence_num=NoteSequence.next_note_sequence_num,
                                         instrument_num=spec["instrument_num"], voice_id=spec["voice_id"],
                                         track_num=spec["track_num"], channel_num=spec["channel_num"],
                                         notes=[], bar_num=bar.bar_num)
            composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
            bar.note_sequences.append(note_sequence)
            self.add_backbone_notes(composition, spec, bar, note_sequence, previous_note_sequence)
            VolumeUtils.change_volumes(spec, previous_spec, bar, note_sequence)
            previous_note_sequence = note_sequence
            previous_spec = spec
        return composition

    def add_backbone_notes(self, composition, spec, bar, note_sequence, previous_note_sequence):
        pitch_offset = int(spec["octave_offset"]) * 12
        backbone_length = int(spec["backbone_length"])
        timings = TimingUtils.get_quantized_timings(backbone_length, 64)
        for t in timings:
            note = Note(pitch=72, volume=100, note_type="backbone",
                        timing=t, note_sequence_num=note_sequence.note_sequence_num,
                        bar_num=note_sequence.bar_num)
            note_sequence.notes.append(note)
        previous_pitch = None if previous_note_sequence is None else previous_note_sequence.notes[-1].pitch
        allows_in_bar_repetition = spec["in_bar_repetition"]
        allows_over_bar_repetition = spec["over_bar_repetition"]
        for ind, note in enumerate(note_sequence.notes):
            chord_for_note = None
            for chord_ind in range(0, len(bar.chord_nums) - 1):
                chord1_num = bar.chord_nums[chord_ind]
                chord2_num = bar.chord_nums[chord_ind + 1]
                chord1 = composition.chords_hash[chord1_num]
                chord2 = composition.chords_hash[chord2_num]
                if chord1.timing.start64th <= note.timing.start64th <= chord2.timing.start64th:
                    chord_for_note = chord1
            if chord_for_note is None:
                chord_for_note = composition.chords_hash[bar.chord_nums[-1]]
            pitch_for_note = None
            if previous_pitch is None:
                pitch_for_note = random.choice(chord_for_note.pitches)
            else:
                plus = pitch_offset - previous_pitch
                repetition_allowed = (ind == 0 and allows_over_bar_repetition) or (ind > 0 and allows_in_bar_repetition)
                least_allowed = 0 if repetition_allowed else 1
                least_pitch_dist = min([abs(p + plus) for p in chord_for_note.pitches if abs(p + plus) >= least_allowed])
                poss_pitches = chord_for_note.pitches
                if spec["backbone_choice"] == "least_distance":
                    poss_pitches = [p for p in chord_for_note.pitches if abs(p + pitch_offset - previous_pitch) == least_pitch_dist]
                pitch_for_note = random.choice(poss_pitches)
            note.pitch = pitch_for_note + pitch_offset
            note.chord_num = chord_for_note.chord_num
            previous_pitch = note.pitch
