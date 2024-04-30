import random, math
from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.MathUtils import *
from ParleyV2.Utils.ExtractionUtils import *


class TimingUtils:

    def ms_to_ticks(ms):
        return int(round((ms/1000) * 960))

    def ticks_to_ms(ticks):
        return int(round((ticks/960) * 1000))

    def timing_to_ticks(timing, total_duration_ticks):
        return int(round((timing.duration64ths/64) * total_duration_ticks))

    def ms_duration(duration64ths, bar):
        return (duration64ths/64) * bar.duration_ticks

    def get_directly_preceding_notes(note, diff_64ths, composition):
        directly_preceding_notes = []
        bar_start64th = composition.bars_hash[note.bar_num].start64th
        for other_note in ExtractionUtils.get_notes_in_composition(composition):
            end64th = composition.bars_hash[other_note.bar_num].start64th + other_note.timing.start64th + other_note.timing.duration64ths
            diff = (bar_start64th + note.timing.start64th) - end64th
            if diff >= 0 and diff <= diff_64ths:
                directly_preceding_notes.append(other_note)
        return directly_preceding_notes

    def get_directly_following_notes(note, diff_64ths, composition):
        directly_following_notes = []
        bar_start64th = composition.bars_hash[note.bar_num].start64th
        for other_note in ExtractionUtils.get_notes_in_composition(composition):
            end64th = bar_start64th + note.timing.start64th + note.timing.duration64ths
            diff = (composition.bars_hash[other_note.bar_num].start64th + other_note.timing.start64th) - end64th
            if diff >= 0 and diff <= diff_64ths:
                directly_following_notes.append(other_note)
        return directly_following_notes

    def get_overlapping_notes(note, composition):
        overlapping_notes = []
        track_num = composition.note_sequences_hash[note.note_sequence_num].track_num
        for other_note in ExtractionUtils.get_notes_in_composition(composition):
            if other_note != note:
                if TimingUtils.get_note_overlap_duration64ths(note, other_note) > 0:
                    overlapping_notes.append(other_note)
        return overlapping_notes

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

                if total_ticks != bar.duration_ticks and len(notes) > 0:
                    diff = bar.duration_ticks - total_ticks
                    notes[-1].midi_timing.duration_ticks += diff

        for bar in composition.bars:
            for note_sequence in bar.note_sequences:
                for note in note_sequence.notes:
                    if note.pause_64ths is not None:
                        TimingUtils.handle_pause(composition, bar, note_sequence, note)

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
                    if spec["sustain_pedal_bars"] != 0:
                        spb = spec["sustain_pedal_bars"]
                        num_bars_to_add = (spb - (note.bar_num % spb)) - 1
                        if note.bar_num + num_bars_to_add < len(composition.bars):
                            pedal_end_bar = composition.bars_hash[note.bar_num + num_bars_to_add]
                        else:
                            pedal_end_bar = composition.bars[-1]
                        end64th = pedal_end_bar.start64th + 64
                        note_end64th = bar.start64th + note.timing.start64th + note.timing.duration64ths
                        extra = int(round(((end64th - note_end64th)/64) * bar.duration_ticks))
                        note.midi_timing.duration_ticks += extra
                        note.midi_timing.off_tick += extra
                    if spec["reverb"] != 0:
                        reverb = spec["reverb"]
                        extra = int(round(note.midi_timing.duration_ticks * reverb))
                        note.midi_timing.duration_ticks += extra
                        note.midi_timing.off_tick += extra

    def handle_pause(composition, bar, note_sequence, note):
        extra = int(round((note.pause_64ths / 64) * bar.duration_ticks))
        notes_after = [n for n in ExtractionUtils.get_notes_in_composition(composition) if n.midi_timing.on_tick > note.midi_timing.off_tick]
        for n in notes_after:
            n.midi_timing.on_tick += extra
            n.midi_timing.off_tick += extra
        bar.duration_ticks += extra
        bar.end_tick += extra
        for b in [b for b in composition.bars if b.bar_num > bar.bar_num]:
            b.start_tick += extra
            b.end_tick += extra
        s64 = note.timing.start64th
        e64 = note.timing.start64th + note.timing.duration64ths
        addon_ticks_per_64th = extra/(e64 - s64)
        bar_notes = ExtractionUtils.get_notes_in_bar(bar)
        for note_to_change in bar_notes:
            num_64ths_from_pause_start = note_to_change.timing.start64th - s64
            num_64ths_from_pause_start_to_end = note_to_change.timing.start64th + note_to_change.timing.duration64ths - s64
            if num_64ths_from_pause_start >= 0:
                note_to_change.midi_timing.on_tick += int(num_64ths_from_pause_start * addon_ticks_per_64th)
                addon_ticks_for_note = int(note_to_change.timing.duration64ths * addon_ticks_per_64th)
                note_to_change.midi_timing.duration_ticks += addon_ticks_for_note
                note_to_change.midi_timing.off_tick += int(num_64ths_from_pause_start_to_end * addon_ticks_per_64th)

    def get_pedal_on_and_off_bars(composition, export_spec):
        pedal_on_bars = []
        pedal_off_bars = []
        performance_spec = export_spec.get_value("performance_spec")
        pedal_reset = performance_spec.get_value("sustain_pedal_reset")
        if pedal_reset == "episode":
            for ep_num in range(0, composition.num_episodes):
                bars = ExtractionUtils.get_bars_for_episode_num(composition, ep_num + 1)
                bar_num = 0
                while bar_num < len(bars):
                    bar = bars[bar_num]
                    pspec = performance_spec.instantiate_me(composition, bar)
                    sustain_pedal_bars = pspec["sustain_pedal_bars"]
                    if sustain_pedal_bars is not None and sustain_pedal_bars > 0:
                        sustain_pedal_bars = pspec["sustain_pedal_bars"]
                        pedal_on_bars.append(bar)
                        off_bar_num = bar_num + sustain_pedal_bars - 1
                        if off_bar_num < len(bars):
                            pedal_off_bars.append(bars[off_bar_num])
                            bar_num += sustain_pedal_bars
                        else:
                            bar_num = len(bars)
                            if bars[-1] not in pedal_off_bars:
                                pedal_off_bars.append(bars[-1])
                    else:
                        bar_num += 1

        return pedal_on_bars, pedal_off_bars

    def assign_onset_64ths(notes):
        duration_ticks = max([n.midi_timing.on_tick + n.midi_timing.duration_ticks for n in notes])
        # Choose number of bars
        min_num_bars = int(len(notes)/20)
        max_num_bars = int(len(notes)/5)
        tuples = [(TimingUtils.get_score_for_num_bars(notes, duration_ticks/num_bars), num_bars, duration_ticks/num_bars) for num_bars in range(min_num_bars, max_num_bars + 1)]
        tuples.sort()
        num_bars = tuples[-1][1]
        bar_ticks = tuples[-1][2]
        av_notes_per_bar = len(notes)/num_bars
        ticks_per_64th = bar_ticks/64
        for note in notes:
            TimingUtils.quantise_note(note, bar_ticks, ticks_per_64th, 16)

        for fraction in [8, 4]:
            for ind1, note1 in enumerate(notes):
                for ind2, note2 in enumerate(notes[ind1+ 1:]):
                    if note1.bar_num == note2.bar_num and note1.timing.start64th == note2.timing.start64th:
                        diff = abs(note1.midi_timing.on_tick - note2.midi_timing.on_tick)
                        if diff > 100:
                            TimingUtils.quantise_note(note1, bar_ticks, ticks_per_64th, fraction)
                            TimingUtils.quantise_note(note2, bar_ticks, ticks_per_64th, fraction)
        return num_bars, bar_ticks

    def quantise_note(note, bar_ticks, ticks_per_64th, fraction):
        note.bar_num = 1 + math.floor(note.midi_timing.on_tick / bar_ticks)
        note_ticks_from_bar_start = note.midi_timing.on_tick % bar_ticks
        note_64ths_from_bar_start = int(note_ticks_from_bar_start / ticks_per_64th)
        note.timing = Timing()
        note.timing.start64th = int(math.floor(note_64ths_from_bar_start / fraction)) * fraction

    def get_score_for_num_bars(notes, bar_ticks):
        ticks_per_64th = bar_ticks/64
        total_score = 0
        for note in notes:
            note_ticks_from_bar_start = note.midi_timing.on_tick % bar_ticks
            note_64ths_from_bar_start = int(note_ticks_from_bar_start/ticks_per_64th)
            # quantise to quavers to get a score
            quantised_note_64ths_from_bar_start = int(math.floor(note_64ths_from_bar_start / 8)) * 8
            dist = note_64ths_from_bar_start - quantised_note_64ths_from_bar_start
            dist = min(dist, 8 - dist)
            score = 4 - dist
            total_score += score
        return total_score/len(notes)

    def get_first_on_tick(composition):
        notes = ExtractionUtils.get_notes_in_composition(composition)
        return min([n.midi_timing.on_tick for n in notes])
