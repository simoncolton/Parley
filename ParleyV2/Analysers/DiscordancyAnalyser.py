import copy
from ParleyV2.Utils.DiscordancyUtils import *
from ParleyV2.Utils.MarginUtils import *


class DiscordancyAnalyser:

    def __init__(self, analysis_spec):
        self.analysis_spec = analysis_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        for bar in composition.bars:
            has_clang = False
            has_grind = False
            for note_sequence in bar.note_sequences:
                for note in note_sequence.notes:
                    if note.pitch is not None and (note.tie_type is None or note.tie_type == "start"):
                        clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
                        has_clang = has_clang or clang is not None
                        has_grind = has_grind or grind is not None
                        disc = "none"
                        if has_clang:
                            disc = "clang and grind" if has_grind else "clang"
                        elif has_grind:
                            disc = "grind"
                        note.tags["discordance"] = disc
            if has_clang and has_grind:
                MarginUtils.add_margin_comment(bar, "Clang and grind!!", "discordance")
            elif has_clang:
                MarginUtils.add_margin_comment(bar, "Clang!", "discordance")
            elif has_grind:
                MarginUtils.add_margin_comment(bar, "Grind...", "discordance")

        return composition

    def evaluate(self, composition):
        evaluation = 0
        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                for note in note_sequence.notes:
                    if note.pitch is not None and (note.tie_type is None or note.tie_type == "start"):
                        clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
                        if clang is not None:
                            evaluation += 2
                        elif grind is not None:
                            evaluation += 1
        return evaluation


