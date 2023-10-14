import copy
from Utils.VolumeUtils import *
from Utils.TimingUtils import *
from Utils.MusicUtils import *


class PassingNotesGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        previous_note_sequence = None
        previous_spec = None
        for bar in composition.bars:
            spec = self.gen_spec.instantiate_me(composition, bar)
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == spec["track_num"]:
                    self.add_passing_notes(spec, previous_spec, note_sequence, previous_note_sequence)
                    VolumeUtils.change_volumes(spec, previous_spec, bar, note_sequence)
                    previous_note_sequence = note_sequence
            previous_spec = spec
        return composition

    def add_passing_notes(self, spec, previous_spec, note_sequence, previous_note_sequence):
        if previous_note_sequence is not None:
            pitch = note_sequence.notes[0].pitch
            end_notes = self.get_expanded_notes(note=previous_note_sequence.notes[-1], target_pitch=pitch, spec=previous_spec)
            previous_note_sequence.notes.remove(previous_note_sequence.notes[-1])
            previous_note_sequence.notes.extend(end_notes)
        new_notes = []
        for note_ind in range(0, len(note_sequence.notes) - 1):
            pitch = note_sequence.notes[note_ind + 1].pitch
            note = note_sequence.notes[note_ind]
            expanded_notes = self.get_expanded_notes(note=note, target_pitch=pitch, spec=spec)
            new_notes.extend(expanded_notes)
        new_notes.append(note_sequence.notes[-1])
        note_sequence.notes = new_notes

    def get_expanded_notes(self, note, target_pitch, spec):
        expanded_notes = []
        passing_notes_policy = spec["passing_notes"]
        fixed_scale = spec["fixed_scale"]
        min_duration64ths = spec["min_duration64ths"]
        if passing_notes_policy == "none":
            return [note]
        expanded_pitches = MusicUtils.get_passing_note_pitches(note, target_pitch, fixed_scale, passing_notes_policy)
        av_note_duration = note.timing.duration64ths/len(expanded_pitches)
        while av_note_duration < min_duration64ths:
            del expanded_pitches[random.randint(1, len(expanded_pitches) - 1)]
            av_note_duration = note.timing.duration64ths/len(expanded_pitches)
        timings = TimingUtils.get_quantized_timings(len(expanded_pitches), note.timing.duration64ths)
        start64th = note.timing.start64th
        for ind, timing in enumerate(timings):
            new_note = copy.deepcopy(note)
            if ind > 0:
                new_note.tie_type = None
                new_note.note_type = "passing"
            new_note.pitch = expanded_pitches[ind]
            new_note.timing = Timing(start64th=start64th, duration64ths=timing.duration64ths)
            expanded_notes.append(new_note)
            start64th += timing.duration64ths
        return expanded_notes
