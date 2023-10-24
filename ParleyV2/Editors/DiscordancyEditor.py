import copy
from ParleyV2.Utils.DiscordancyUtils import *
from ParleyV2.Utils.ExtractionUtils import *


class DiscordancyEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        allow_repetitions = self.edit_spec.get_value("all_repetitions")
        track_nums = ExtractionUtils.get_track_nums(composition)
        for track_num in track_nums:
            previous_note_pitch = None
            for bar in composition.bars:
                for note_sequence in bar.note_sequences:
                    if note_sequence.track_num == track_num:
                        for note in note_sequence.notes:
                            if note.pitch is not None and (note.tie_type is None or note.tie_type == "start"):
                                clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
                                if clang is not None or grind is not None:
                                    chord = composition.chords_hash[note.chord_num]
                                    scale = MusicUtils.get_named_scale(chord.scale_name)
                                    original_pitch = note.pitch
                                    has_found = False
                                    for addon in range(0, 11):
                                        if not has_found:
                                            a = addon if random.randint(0, 1) == 0 else -addon
                                            note.pitch = original_pitch + a
                                            if note.pitch != previous_note_pitch and MusicUtils.note_is_in_scale(note.pitch, scale):
                                                clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
                                                if clang is None and grind is None:
                                                    note.score_colour = "orange"
                                                    has_found = True
                                                    break
                                            note.pitch = original_pitch - a
                                            if note.pitch != previous_note_pitch and MusicUtils.note_is_in_scale(note.pitch, scale):
                                                clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
                                                if clang is None and grind is None:
                                                    note.score_colour = "orange"
                                                    has_found = True
                                                    break
                                    if not has_found:
                                        note.pitch = original_pitch
                            previous_note_pitch = note.pitch

        return composition
