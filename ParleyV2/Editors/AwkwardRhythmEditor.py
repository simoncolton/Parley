import copy
from Utils.ExtractionUtils import *


class AwkwardRhythmEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        all_notes = ExtractionUtils.get_notes_in_composition(composition)
        pairs = [((n.bar_num * 64) + n.timing.start64th, n) for n in all_notes]
        pairs.sort(key=lambda x: x[0])
        for ind1 in range(0, len(pairs) - 1):
            (t1, n1) = pairs[ind1]
            if n1.timing.tuplet_length is None and n1.pitch is not None and (n1.tie_type is None or n1.tie_type == "start") and n1.timing.duration64ths <= 4:
                n1_end = t1 + n1.timing.duration64ths
                for ind2 in range(ind1 + 1, len(pairs)):
                    (t2, n2) = pairs[ind2]
                    if n1.timing.tuplet_length is None and (t2 == n1_end or t2 == n1_end + 1) and n1.pitch == n2.pitch:
                        bar = composition.bars_hash[n2.bar_num]
                        spec1 = self.edit_spec.instantiate_me(composition, bar, None, n1)
                        if spec1["edit_action"] == "make_first_rest":
                            n1.pitch = None
                            n1.volume = 0
                        spec2 = self.edit_spec.instantiate_me(composition, bar, None, n2)
                        if spec2["edit_action"] == "make_second_rest":
                            n2.pitch = None
                            n2.volume = 0
        return composition
