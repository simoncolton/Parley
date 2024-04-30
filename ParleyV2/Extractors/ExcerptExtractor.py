import copy
from ParleyV2.Utils.TimingUtils import *

class ExcerptExtractor:

    def __init__(self, extract_spec):
        self.extract_spec = extract_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        start_bar_num = self.extract_spec.get_value("start_bar_num")
        end_bar_num = self.extract_spec.get_value("end_bar_num")
        new_bars = [b for b in composition.bars if start_bar_num <= b.bar_num <= end_bar_num]
        composition.num_bars = len(new_bars)
        composition.bars = new_bars
        composition.bars_hash = {}
        composition.note_sequences_hash = {}
        for ind, bar in enumerate(composition.bars):
            bar.bar_num = ind + 1
            bar.start64th = ind * 64
            composition.bars_hash[bar.bar_num] = bar
            for ns in bar.note_sequences:
                composition.note_sequences_hash[ns.note_sequence_num] = ns
                ns.bar_num = bar.bar_num
                for note in ns.notes:
                    note.bar_num = bar.bar_num
                    note.note_sequence_num = ns.note_sequence_num
        earliest_on_tick = TimingUtils.get_first_on_tick(composition)
        for note in ExtractionUtils.get_notes_in_composition(composition):
            note.midi_timing.on_tick -= earliest_on_tick
            note.midi_timing.off_tick -= earliest_on_tick
        return composition
