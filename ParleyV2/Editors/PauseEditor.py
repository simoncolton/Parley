import copy
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.TiedNotesUtils import *


class PauseEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        for note in ExtractionUtils.get_notes_in_composition(composition):
            bar = composition.bars_hash[note.bar_num]
            spec = self.edit_spec.instantiate_me(composition, bar, None, note)
            length_param = spec["pause_length_64ths"]
            if length_param is not None:
                note.pause_64ths = length_param
        return composition
