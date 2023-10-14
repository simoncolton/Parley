import copy
from Utils.ExtractionUtils import *


class DuplicateNoteRemovalEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        for track_num in self.edit_spec.get_value("track_removal_order"):
            self.remove_repeated_notes(composition, track_num)
        return composition

    def remove_repeated_notes(self, composition, track_num):
        other_track_nums = self.edit_spec.get_value("track_removal_order")
        ind1 = other_track_nums.index(track_num)
        notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
        for note1 in notes:
            bar = composition.bars_hash[note1.bar_num]
            for note_sequence2 in bar.note_sequences:
                track_num2 = note_sequence2.track_num
                ind2 = -10000 if not track_num2 in other_track_nums else other_track_nums.index(track_num2)
                if ind2 > ind1:
                    for note2 in note_sequence2.notes:
                        if self.is_repeated_note(note1, note2):
                            note1.pitch = None

    def is_repeated_note(self, note1, note2):
        if note1.pitch != note2.pitch:
            return False
        if note1.timing.start64th != note2.timing.start64th:
            return False
        if note1.timing.duration64ths != note2.timing.duration64ths:
            return False
        return True