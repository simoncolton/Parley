from dataclasses import dataclass
from Utils.TimingUtils import *
from Utils.MusicUtils import *
from Logistics.Constants import *


@dataclass
class Discordancy:
    severity: int = None
    duration_ms: int = None


class DiscordancyUtils:

    def get_discordancies_for_note(composition, note, bar):
        if note.pitch is None:
            return None, None
        clang_discordancy = Discordancy(0, 0)
        grind_discordancy = Discordancy(0, 0)
        bar = composition.bars_hash[note.bar_num]
        overlapping_notes = DiscordancyUtils.get_overlapping_discordant_notes(bar, note)
        clang_notes = [n for n in overlapping_notes if n.timing.start64th == note.timing.start64th]
        grind_notes = [n for n in overlapping_notes if n.timing.start64th != note.timing.start64th]
        if len(clang_notes) > 0:
            clang_duration64ths = max([n.timing.duration64ths for n in clang_notes])
            clang_duration_ms = TimingUtils.ms_duration(clang_duration64ths, bar)
            clang_discordancy = Discordancy(len(clang_notes), clang_duration_ms)
        if len(grind_notes) > 0:
            earliest_grind_start = min([g.timing.start64th for g in grind_notes])
            latest_grind_end = max([(g.timing.start64th + g.timing.duration64ths) for g in grind_notes])
            grid_duration64ths = latest_grind_end - earliest_grind_start
            grind_duration_ms = TimingUtils.ms_duration(grid_duration64ths, bar)
            grind_discordancy = Discordancy(len(grind_notes), grind_duration_ms)
        clang_discordancy = None if clang_discordancy.severity == 0 else clang_discordancy
        grind_discordancy = None if grind_discordancy.severity == 0 else grind_discordancy
        return clang_discordancy, grind_discordancy

    def get_overlapping_discordant_notes(bar, note):
        overlapping_notes =[]
        pitch_class = MusicUtils.pitch_class(note.pitch)
        for note_sequence in bar.note_sequences:
            if note.note_sequence_num != note_sequence.note_sequence_num:
                for other_note in note_sequence.notes:
                    if other_note.pitch is not None and other_note != note:
                        other_pitch_class = MusicUtils.pitch_class(other_note.pitch)
                        dist = MusicUtils.pitch_class_distance(pitch_class, other_pitch_class)
                        if 0 < dist <= 2:
                            overlap_duration64ths = TimingUtils.get_note_overlap_duration64ths(note, other_note)
                            if overlap_duration64ths > 0:
                                overlapping_notes.append(other_note)
        return overlapping_notes

    def discordancy_is_ok(composition, note, discordancy_spec, bar):
        if discordancy_spec is None:
            return True
        clang, grind = DiscordancyUtils.get_discordancies_for_note(composition, note, bar)
        if clang is None and grind is None:
            return True
        if clang is not None:
            clang_severity = discordancy_spec.get_value("max_clang_severity")
            max_clang_duration_ms = discordancy_spec.get_value("max_clang_duration_ms")
            if max_clang_duration_ms is not None and clang.severity > clang_severity and clang.duration_ms > max_clang_duration_ms:
                return False
        if grind is not None:
            grind_severity = discordancy_spec.get_value("max_grind_severity")
            max_grind_duration_ms = discordancy_spec.get_value("max_grind_duration_ms")
            if max_grind_duration_ms is not None and grind.severity > grind_severity and grind.duration_ms > max_grind_duration_ms:
                return False
        return True

