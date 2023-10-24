import copy

from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.RhythmUtils import *


class TiedNotesUtils:

    def get_tied_duration64ths(note_sequence, note):
        duration64ths = note.timing.duration64ths
        does_end = False
        for i in range(note_sequence.notes.index(note) + 1, len(note_sequence.notes)):
            n = note_sequence.notes[i]
            if n.tie_type == "mid" or n.tie_type == "end":
                duration64ths += n.timing.duration64ths
            if n.tie_type == "end":
                does_end = True
                break
        return duration64ths, does_end

    def simplify_tied_notes(composition, track_num):
        # Join together tied notes in a bar
        note_sequences = ExtractionUtils.get_note_sequences_for_track_num(composition, track_num)
        for note_sequence in note_sequences:
            new_notes = []
            for ind, note in enumerate(note_sequence.notes):
                if ind == 0 or note.tie_type is None or note.tie_type == "start":
                    new_notes.append(note)
                if note.tie_type == "start" or (ind == 0 and note.tie_type == "mid"):
                    duration24ths, does_end = TiedNotesUtils.get_tied_duration64ths(note_sequence, note)
                    note.timing.duration64ths = duration24ths
                if note.tie_type == "start" and ind < len(note_sequence.notes) - 1:
                    note.tie_type = None if does_end else "start"
                if note.tie_type == "mid":
                    note.tie_type = "end" if does_end else "mid"
            note_sequence.notes = new_notes

        # Split awkward fractions into two or more notes

        for note_sequence in note_sequences:
            new_notes = []
            for note in note_sequence.notes:
                dur_dot_pairs = RhythmUtils.get_note_quantization_split(note.timing.duration64ths)
                if len(dur_dot_pairs) == 1:
                    new_notes.append(note)
                else:
                    split_notes = TiedNotesUtils.get_split_notes(note, dur_dot_pairs)
                    new_notes.extend(split_notes)
            note_sequence.notes = new_notes

    def get_split_notes(note, dur_dot_pairs):
        split_notes = []
        dur_dot_pairs = RhythmUtils.get_best_beat_ordering(dur_dot_pairs, note.timing.start64th)
        original_tie_type = note.tie_type
        start64th = note.timing.start64th
        for ind, (duration64ths, num_dots) in enumerate(dur_dot_pairs):
            new_note = copy.deepcopy(note)
            split_notes.append(new_note)
            new_note.timing.start64th = start64th
            dot_mult = [1, 1.5, 1.75][num_dots]
            new_note.timing.duration64ths = int(duration64ths * dot_mult)
            if ind == 0:
                if original_tie_type is None:
                    new_note.tie_type = "start"
                elif original_tie_type == "end":
                    new_note.tie_type = "mid"
            else:
                if original_tie_type is None:
                    new_note.tie_type = "end"
                elif original_tie_type == "mid" or original_tie_type == "start":
                    new_note.tie_type = "mid"
            start64th += new_note.timing.duration64ths
        return split_notes
