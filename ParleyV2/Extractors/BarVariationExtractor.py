import copy
import random
from ParleyV2.Utils.MusicUtils import *

class BarVariationExtractor:

    def __init__(self, extract_spec):
        self.extract_spec = extract_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        bar_num = self.extract_spec.get_value("bar_num")
        num_bars_per_changes = self.extract_spec.get_value("num_bars_per_change")
        fixed_bar = start_composition.bars[bar_num]
        num_changes = 0
        for bar in composition.bars:
            if bar.bar_num == 1:
                num_changes = 0
            elif bar.bar_num == 2:
                num_changes = 1
            elif ((bar.bar_num - 2) % num_bars_per_changes == 0) or num_bars_per_changes == 1:
                num_changes += 1
            total_num_notes = 0
            for ind, note_sequence in enumerate(bar.note_sequences):
                note_sequence.notes = []
                for note in fixed_bar.note_sequences[ind].notes:
                    clean_note = copy.deepcopy(note)
                    note.note_sequence_num = note_sequence.note_sequence_num
                    note.bar_num = bar.bar_num
                    clean_note.tags = {}
                    note_sequence.notes.append(clean_note)
                    if note.pitch is not None:
                        total_num_notes += 1
            notes_changed = []
            num_changes_to_make = min(total_num_notes, num_changes)
            num_changes_made = 0
            while num_changes_made < num_changes_to_make:
                note_sequence = random.choice(bar.note_sequences)
                note = random.choice(note_sequence.notes)
                if note.pitch is not None and note not in notes_changed:
                    chord = composition.chords_hash[note.chord_num]
                    scale = MusicUtils.get_named_scale(chord.scale_name)
                    pitches = MusicUtils.get_pitches_in_scale(scale)
                    found_pitch = False
                    while not found_pitch:
                        pitch = random.choice(pitches)
                        if abs(pitch - note.pitch) <= 6 and pitch != note.pitch:
                            note.pitch = pitch
                            found_pitch = True
                    note.tags["variation"] = "varied"
                    num_changes_made += 1
                    notes_changed.append(note)
            bar.pc_change = int(round(100 * (num_changes_made/total_num_notes)))
        return composition
