from Parley.Specifications.Artefacts import *
from Parley.Utils.ChordUtils import *
from Parley.Utils.MelodyUtils import *
from Parley.Utils.ExtractionUtils import *
import random


class HarmonisationEditor:

    def __init__(self, edit_spec):
        self.spec = edit_spec

    def apply(self, composition):
        pass

    def add_harmony_track(self, composition, episode):
        for bar in episode.bars:
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == self.spec.track_num_to_harmonise:
                    new_note_sequence = self.get_copy_note_sequence(note_sequence)
                    bar.note_sequences.append(new_note_sequence)

        new_track_notes = ExtractionUtils.get_track_notes_for_episode(composition, episode)[self.spec.new_track_num]
        notes_to_change = self.get_notes_to_change(self, new_track_notes)
        for note in new_track_notes:
            if note in notes_to_change:
                intervals = self.spec.intervals_allowed.copy()
                random.shuffle(intervals)
                new_note_pitch = None
                i = 0
                while i < len(intervals) and new_note_pitch is None:
                    new_note_pitch = note.pitch + intervals[i]
                    if self.spec.fixed_key_sig is not None and not ChordUtils.note_is_in_key(new_note_pitch, self.spec.fixed_key_sig):
                        new_note_pitch = None
                    elif self.spec.pitch_range_low > new_note_pitch or self.spec.pitch_range_high < new_note_pitch:
                        new_note_pitch = None
                    i += 1
                if new_note_pitch is None and self.spec.map_to_key_signature:
                    i = 0
                    while i < len(intervals) and new_note_pitch is None:
                        new_note_pitch = MelodyUtils.map_to_closest_in_key(self.spec.fixed_key_sig, note.pitch + intervals[i])
                        if self.spec.pitch_range_low > new_note_pitch or self.spec.pitch_range_high < new_note_pitch:
                            new_note_pitch = None
                        i += 1
                note.pitch = new_note_pitch
                note.score_colour = "orange"
            else:
                note.pitch = None

    def get_notes_to_change(self, composition, notes_in_new_track):
        notes_to_change = []
        for note in notes_in_new_track:
            is_ok = True
            if note.pitch is None or (note.tie_type is not None and note.tie_type != "start"):
                is_ok = False
            if self.spec.note_types_to_change == "backbone" and not note.is_backbone_note:
                is_ok = False
            if self.spec.note_types_to_change == "passing" and note.is_backbone_note:
                is_ok = False
            if is_ok:
                notes_to_change.append(note)
        return notes_to_change


    def handle_tied_notes(self, composition):
        composition_notes = ExtractionUtils.get_track_notes_for_composition(composition)[self.spec.new_track_num]
        for ind, note in enumerate(composition_notes):
            if note.tie_type == "start":
                note_num = ind + 1
                if note_num < len(composition_notes):
                    next_note = composition_notes[note_num]
                    while note_num < len(composition_notes) and (next_note.tie_type == "mid" or next_note.tie_type == "end"):
                        next_note.pitch = note.pitch
                        next_note.score_colour = "orange"
                        note_num += 1
                        if note_num < len(composition_notes):
                            next_note = composition_notes[note_num]

    def get_copy_note_sequence(self, old_note_sequence):
        new_notes = []
        for note in old_note_sequence.notes:
            new_note = note.__copy__()
            new_notes.append(new_note)
        new_note_sequence = NoteSequence(id=self.spec.id, track_num=self.spec.new_track_num,
                                         channel_num=self.spec.new_channel_num,
                                         instrument_num=self.spec.instrument_num, notes=new_notes,
                                         interestingness_profile=None, parent_bar=old_note_sequence.parent_bar)
        return new_note_sequence
