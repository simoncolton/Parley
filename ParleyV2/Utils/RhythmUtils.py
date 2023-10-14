from Utils.MusicUtils import *
from Utils.MathUtils import *
from Artefacts.Artefacts import *
import random
import itertools


class RhythmUtils:

    def get_overlap_ticks(note1, note2):
        r1 = [note1.start_tick, note1.start_tick + note1.duration_ticks]
        r2 = [note2.start_tick, note2.start_tick + note2.duration_ticks]
        return MathUtils.get_overlap(r1, r2)

    def correct_note_sequence(note_sequence):
        notes = note_sequence.notes
        note_sequence_ticks = sum([n.duration_ticks for n in notes])
        bar_duration_ticks = note_sequence.notes[0].parent_bar.duration_ticks
        addon = 1 if note_sequence_ticks < bar_duration_ticks else -1
        while note_sequence_ticks != bar_duration_ticks:
            ind = random.randint(0, len(notes) - 1)
            notes[ind].duration_ticks += addon
            for i in range(ind + 1, len(notes)):
                notes[i].start_tick += addon
            note_sequence_ticks += addon

    def get_fracs_from_rhythm(rhythm_strings):
        frac_details = []
        for rhythm_string in rhythm_strings:
            start_fraction = rhythm_string.split(":")[0]
            duration_fraction = rhythm_string.split(":")[1]
            start_prop = float(start_fraction.split("/")[0])/float(start_fraction.split("/")[1])
            duration_prop = float(duration_fraction.split("/")[0])/float(duration_fraction.split("/")[1])
            frac_details.append([128 * start_prop, 128 * duration_prop])
        return frac_details

    def get_frac(frac_string, minus_1):
        parts = frac_string.split("/")
        takeoff = 1 if minus_1 else 0
        return (float(parts[0]) - takeoff)/float(parts[1])

    def get_bar_divisions(rhythm_string):
        denominators = []
        for part in rhythm_string.split(","):
            bits = part.split(":")
            denominators.append(int(bits[2].split("/")[1]))
        return max(denominators)

    def get_note_quantization_split(num_fracs, so_far=[]):
        wholes = [1, 2, 4, 8, 16, 32, 64]
        dotted = [round(x * 1.5) for x in wholes[1:-1]]
        double_dotted = [round(x * 1.75) for x in wholes[2:-1]]
        all = wholes.copy()
        all.extend(dotted)
        all.extend(double_dotted)
        all.sort()
        so_far_copy = so_far.copy()
        if num_fracs in wholes:
            so_far_copy.append((num_fracs, 0))
            return so_far_copy
        if num_fracs in dotted:
            so_far_copy.append((int(num_fracs/1.5), 1))
            return so_far_copy
        if num_fracs in double_dotted:
            so_far_copy.append((int(num_fracs/1.75), 2))
            return so_far_copy

        for ind, w in enumerate(wholes):
            if w > num_fracs:
                next_so_far = so_far.copy()
                next_so_far.append((wholes[ind - 1], 0))
                return RhythmUtils.get_note_quantization_split(num_fracs - wholes[ind - 1], next_so_far)

    def get_best_beat_ordering(dur_dot_pairs, start_frac):
        permutations = itertools.permutations(dur_dot_pairs)
        pairs = []
        beats = [0, 32, 64, 96]
        half_beats = [16, 48, 80, 112]
        for ddp in permutations:
            beat_frac = start_frac
            score = 0
            for dur, _ in ddp:
                for b in beats:
                    if beat_frac == b:
                        score += 2
                for b in half_beats:
                    if beat_frac == b:
                        score += 1
                beat_frac += dur
            pairs.append((score, ddp))
        pairs.sort(reverse=True)
        return pairs[0][1]

    def get_backbone_passing_note_signature(note_sequence):
        s = ""
        for note in note_sequence.notes:
            note_type = "b" if note.is_backbone_note else "p"
            s += note_type
        return s
