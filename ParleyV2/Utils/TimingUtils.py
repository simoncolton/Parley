import random, math
from Artefacts.Artefacts import *
from Utils.MathUtils import *
from Utils.ExtractionUtils import *


class TimingUtils:

    def ms_to_ticks(ms):
        return int(round((ms/1000) * 960))

    def ticks_to_ms(ticks):
        return int(round((ticks/960) * 1000))

    def timing_to_ticks(timing, total_duration_ticks):
        return int(round((timing.duration64ths/64) * total_duration_ticks))

    def ms_duration(duration64ths, bar):
        return (duration64ths/64) * bar.duration_ticks

    def get_note_overlap_duration64ths(note1, note2):
        range1 = range(note1.timing.start64th, note1.timing.start64th + note1.timing.duration64ths)
        range2 = range(note2.timing.start64th, note2.timing.start64th + note2.timing.duration64ths)
        overlap = range(max(range1[0], range2[0]), min(range1[-1], range2[-1])+1)
        return len(overlap)

    def get_timing(details_string):
        lh_str = details_string.split(":")[0]
        rh_str = details_string.split(":")[1]
        start_prop = (float(lh_str.split("/")[0]) - 1)/float(lh_str.split("/")[1])
        dur_prop = float(rh_str.split("/")[0])/float(rh_str.split("/")[1])
        return Timing(int(64 * start_prop), int(64 * dur_prop))

    def get_start_and_duration_fracs(details_string):
        start_prop, dur_prop = TimingUtils.get_start_and_duration_props(details_string)
        return int(start_prop * 128), int(dur_prop * 128)

    def fix_ticks_to_total(sequence, total_ticks):
        total_ticks_in_sequence = sequence[-1].end_tick
        addon = 1 if total_ticks > total_ticks_in_sequence else -1
        while total_ticks_in_sequence != total_ticks:
            entry = random.choice(sequence)
            entry.duration_ticks += addon
            entry.end_tick += addon
            for i in range(sequence.index(entry) + 1, len(sequence)):
                sequence[i].start_tick += addon
                sequence[i].end_tick += addon
            total_ticks_in_sequence = sequence[-1].end_tick

    def get_quantized_timings(num_notes, num64ths):

        for n in range(2, 9):
            if num_notes == n and (num64ths % n == 0):
                h = int(num64ths/n)
                return [Timing(h * i, h) for i in range(0, n)]

        note_duration64ths = MathUtils.largest_pow2_lte(math.floor((1/num_notes) * num64ths))
        note_durations = [note_duration64ths for i in range(0, num_notes)]
        duration_to_fill = num64ths - sum(note_durations)
        while duration_to_fill > 0:
            addon = MathUtils.largest_pow2_lte(duration_to_fill)
            pos = random.randint(0, len(note_durations) - 1)
            note_durations[pos] += addon
            duration_to_fill = num64ths - sum(note_durations)
        start64th = 0
        timings = []
        for note_duration in note_durations:
            timings.append(Timing(start64th, note_duration))
            start64th += note_duration
        return timings

    def add_midi_timings(composition, performance_spec):
        track_nums = ExtractionUtils.get_track_nums(composition)
        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                notes = note_sequence.notes
                start_tick_move = 0

                for note in notes:
                    if note.timing.tuplet_length is None:
                        start_tick_move = 0
                    on_tick = bar.start_tick + bar.tick_timings[note.timing.start64th] + start_tick_move
                    note.midi_timing = MidiTiming(on_tick=on_tick)
                    note.midi_timing.duration_ticks = bar.tick_timings[note.timing.duration64ths]
                    note.midi_timing.off_tick = note.midi_timing.on_tick + note.midi_timing.duration_ticks
                    if note.timing.tuplet_length is not None:
                        old_off = note.midi_timing.off_tick
                        nticks = (note.timing.tuplet_duration64ths/note.timing.tuplet_length) * bar.tick_timings[1]
                        note.midi_timing.duration_ticks = int(round(nticks))
                        note.midi_timing.off_tick = note.midi_timing.on_tick + note.midi_timing.duration_ticks
                        start_tick_move += note.midi_timing.off_tick - old_off
                total_ticks = sum([n.midi_timing.duration_ticks for n in note_sequence.notes])

                if total_ticks != bar.duration_ticks:
                    diff = bar.duration_ticks - total_ticks
                    notes[-1].midi_timing.duration_ticks += diff

        for track_num in track_nums:
            notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            tied_note = None
            for note in notes:
                if note.tie_type == "start":
                    tied_note = note
                if note.tie_type == "mid" or note.tie_type == "end":
                    tied_note.midi_timing.duration_ticks += note.midi_timing.duration_ticks
                    tied_note.midi_timing.off_tick += note.midi_timing.duration_ticks
                    note.midi_timing.duration_ticks = 0

        for track_num in track_nums:
            notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            for note in notes:
                bar = composition.bars_hash[note.bar_num]
                spec = performance_spec.instantiate_me(composition, bar=bar, note=note)
                if note.pitch is not None and note.midi_timing.duration_ticks > 0:
                    if spec["sustain_pedal_beats"] is not None:
                        extra = int(round((64 - note.timing.start64th - note.timing.duration64ths)/64 * bar.duration_ticks))
                        note.midi_timing.duration_ticks += extra
                        note.midi_timing.off_tick += extra
                    if spec["sustain_factor"] is not None:
                        extra = int(round(note.midi_timing.duration_ticks * (spec["sustain_factor"] - 1)))
                        note.midi_timing.duration_ticks += extra
                        note.midi_timing.off_tick += extra
                    if spec["end_sustain_pedal_beats"] is not None:
                        last_bar = composition.bars[-1]
                        composition_end_tick = last_bar.end_tick + int((last_bar.duration_ticks/4) * spec["end_sustain_pedal_beats"])
                        note.midi_timing.off_tick = min(note.midi_timing.off_tick, composition_end_tick)
                        if note == notes[-1]:
                            note.midi_timing.off_tick = composition_end_tick



