import copy
from ParleyV2.Artefacts.Artefacts import *


class LeadSheetGenerator:

    def __init__(self, export_spec):
        self.export_spec = export_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        composition.title += " Lead Sheet"
        for bar in composition.bars:
            bar.note_sequences = []
            for note_num in range(0, 4):
                NoteSequence.next_note_sequence_num += 1
                note_sequence = NoteSequence(note_sequence_num=NoteSequence.next_note_sequence_num,
                                             instrument_num=0, voice_id="piano", track_num=note_num,
                                             channel_num=note_num, notes=[], bar_num=bar.bar_num)
                composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
                for chord_num in bar.chord_nums:
                    chord = composition.chords_hash[chord_num]
                    pitch = chord.pitches[0] + 12 if note_num == 3 else chord.pitches[note_num] - 12
                    note = Note(pitch=pitch, volume=100, note_type="backbone", timing=chord.timing,
                                chord_num=chord.chord_num, note_sequence_num=note_sequence.note_sequence_num,
                                bar_num = note_sequence.bar_num, track_note_num=None)
                    note_sequence.notes.append(note)
                bar.note_sequences.append(note_sequence)
        return composition
