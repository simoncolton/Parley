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
                        all_notes_to_pause = TimingUtils.get_all_notes_to_pause(note_sequence.track_num, note, bar)
                        extra = int(round((note.pause_64ths/64) * bar.duration_ticks))
                        TimingUtils.extend_note_duration(composition, note, all_notes_to_pause, extra)

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

    def get_all_notes_to_pause(track_num, note, bar):
        notes_to_pause_hash = {}
        notes_to_pause_hash[track_num] = note

        for note_sequence in bar.note_sequences:
            if note_sequence.track_num != track_num:
                poss_notes = []
                overlap_v = []
                for n in note_sequence.notes:
                    if n.timing.start64th >= note.timing.start64th and \
                            n.timing.start64th + n.timing.duration64ths <= note.timing.start64th + note.timing.duration64ths:
                        poss_notes.append(n)
                    overlap_v.append((TimingUtils.get_note_overlap_duration64ths(n, note), n))
                if len(poss_notes) > 0:
                    notes_to_pause_hash[note_sequence.track_num]=poss_notes[-1]
                else:
                    overlap_v.sort(key=lambda x: x[0])
                    if len(overlap_v) > 0:
                        notes_to_pause_hash[note_sequence.track_num]=overlap_v[-1][1]
        return notes_to_pause_hash

    def extend_note_duration(composition, note, all_notes_to_pause, extra):
        bar = composition.bars_hash[note.bar_num]
        bar.duration_ticks += extra
        bar.end_tick += extra
        bars_adjusted = [bar]
        for track_num in all_notes_to_pause.keys():
            n = all_notes_to_pause[track_num]
            n.midi_timing.duration_ticks += extra
            n.midi_timing.off_tick += extra
            for tn in ExtractionUtils.get_notes_for_track_num(composition, track_num):
                if tn.track_note_num > n.track_note_num:
                    tn.midi_timing.on_tick += extra
                    tn.midi_timing.off_tick += extra
                    bar = composition.bars_hash[tn.bar_num]
                    if bar not in bars_adjusted:
                        bar.start_tick += extra
                        bar.end_tick += extra
                        bars_adjusted.append(bar)

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

