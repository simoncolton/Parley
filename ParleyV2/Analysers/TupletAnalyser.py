import copy
from ParleyV2.Utils.DiscordancyUtils import *
from ParleyV2.Utils.MarginUtils import *
from ParleyV2.Utils.ExtractionUtils import *


class TupletAnalyser:

    def __init__(self, analysis_spec):
        self.analysis_spec = analysis_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        notes = ExtractionUtils.get_notes_in_composition(composition)
        for note in notes:
            if note.timing.tuplet_length == 6:
                bar = composition.bars_hash[note.bar_num]
                MarginUtils.add_margin_comment(bar, "Sextuplet", "tuplet")
        return composition

