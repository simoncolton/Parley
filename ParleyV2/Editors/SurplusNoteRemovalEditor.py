import copy
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.TimingUtils import *

class SurplusNoteRemovalEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        for bar in composition.bars:
            bar_notes = ExtractionUtils.get_notes_in_bar(bar)
            for ind, n1 in enumerate(bar_notes):
                for n2 in bar_notes[ind + 1:]:
                    if n1.pitch is not None and n2.pitch is not None and n1.pitch == n2.pitch:
                        if n1.timing.start64th == n2.timing.start64th and n1.timing.duration64ths == n2.timing.duration64ths:
                            n2.pitch = None
        return composition
