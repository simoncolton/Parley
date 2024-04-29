from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Specifications.ConstrainedSpecification import *
from ParleyV2.Exporters.TotalExporter import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Utils.VolumeUtils import *
from ParleyV2.Analysers.ExpressionAnalyser import *

import numpy as np
import math
import librosa

class AriaScoreExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec
        self.notes = []
        self.neighbourhoods = []
        self.bpm = None
        self.beat_duration_s = None
        self.lh_notes = []
        self.rh_notes = []
        self.lh_tick_dists = []
        self.rh_tick_dists = []
        self.chord_note_lists = [[] for _ in range(2, 10)]
        self.piece_duration = None

    def apply(self, starting_composition, make_loud=False, keep_slow=False):
        self.load_tokens(self.export_spec.get_value("tokens_filepath"))
        self.get_neighbourhoods()
        self.get_note_sets()
        #self.get_note_sets_from_volume()

        self.get_tick_dists()
        speed = self.slow_down()
        self.get_tick_dists() # do it again after change
        self.get_bpm()
        self.get_smallest_64th_distance()
        self.quantise_from_lh()
        self.fit_against(self.rh_notes, self.lh_notes)
        self.fill_in(self.rh_notes)
        self.add_chord_notes()
        self.add_start_notes()
        self.specify_bars(self.lh_notes)
        self.specify_bars(self.rh_notes)
        for chord_notes in self.chord_note_lists:
            self.specify_bars(chord_notes)
        self.do_offset()
        if self.export_spec.get_value("keep_slow") == False:
           self.change_speed(1/speed)
           self.bpm = int(self.bpm/speed)
        if self.export_spec.get_value("make_loud") == True:
            for n in self.rh_notes + self.lh_notes:
                n.volume = 100
                n.volume = 100
        self.make_composition()
        return self.composition

    def get_smallest_64th_distance(self):
        min_tick_dist = min(self.lh_tick_dists + self.rh_tick_dists)
        min_s = (min_tick_dist/960)
        min_beats = min_s/self.beat_duration_s
        min_64ths = (min_beats/4) * 64

        # FIX THIS MAX - LIMITS IT TO SEMIQUAVERS

        self.min_64ths_dist = min_64ths # max(4, MathUtils.closest_power_of_2_dividing(min_64ths) ** 2)
        self.min_64ths_dist = max(4, MathUtils.closest_power_of_2_dividing(min_64ths) ** 2)
        self.min_64ths_dist = 8

    def get_tick_dists(self):
        self.lh_tick_dists = [abs(self.lh_notes[ind].midi_timing.on_tick - self.lh_notes[ind+1].midi_timing.on_tick) for ind in range(0, len(self.lh_notes)-1)]
        self.rh_tick_dists = [abs(self.rh_notes[ind].midi_timing.on_tick - self.rh_notes[ind+1].midi_timing.on_tick) for ind in range(0, len(self.rh_notes)-1)]

    def slow_down(self):
        av_tick_dist = np.mean(self.lh_tick_dists + self.rh_tick_dists)
        if av_tick_dist < 300:
            factor = av_tick_dist / 600
            self.change_speed(factor)
            return factor
        else:
            return 1

    def change_speed(self, factor):
        for note in self.notes:
            note.midi_timing.on_tick = int(note.midi_timing.on_tick / factor)
            note.midi_timing.off_tick = int(note.midi_timing.off_tick / factor)
            note.midi_timing.duration_ticks = int(note.midi_timing.duration_ticks / factor)

    def do_offset(self):
        first_note = None
        earliest_64th = 100000000
        for n in self.notes:
            if (n.bar_num * 64) + n.timing.start64th < earliest_64th:
                first_note = n
                earliest_64th = (n.bar_num * 64) + n.timing.start64th
        s_offset = ((first_note.timing.start64th)/64) * self.beat_duration_s * 4
        tick_offset = int(s_offset * 960)
        for n in self.notes:
            n.midi_timing.on_tick += tick_offset
            n.midi_timing.off_tick += tick_offset

    def add_start_notes(self):
        ind = [i for i in range(0, len(self.notes)) if self.notes[i].timing.start64th is not None][0]
        take_off = 0
        while ind > 0:
            dist_ticks = self.notes[ind].midi_timing.on_tick - self.notes[ind - 1].midi_timing.on_tick
            beat_s = 60/self.bpm
            beat_ticks = beat_s * 960
            num_beats = dist_ticks/beat_ticks
            num64ths = int(16 * num_beats)
            start64th = take_off - num64ths
            start64th = int(round(start64th/8) * 8)
            self.notes[ind-1].timing.start64th = start64th
            take_off -= num64ths
            ind -= 1
        if take_off < 0:
            for note in self.notes:
                note.timing.start64th += 64

    def add_chord_notes(self):
        for neighbourhood in self.neighbourhoods:
            if len(neighbourhood) > 2:
                for note in neighbourhood[1:-1]:
                    note.timing.start64th = neighbourhood[0].timing.start64th

    def specify_bars(self, notes):
        for note in notes:
            if note.timing.start64th is not None:
                note.bar_num = 1 + math.floor(note.timing.start64th / 64)
                t = note.timing.start64th
                note.timing.start64th = note.timing.start64th % 64

    def fill_in(self, notes):
        ind = 0
        while ind < len(notes):
            if notes[ind].timing.start64th is not None:
                next_posses = [ind2 for ind2 in range(ind + 1, len(notes)) if notes[ind2].timing.start64th is not None]
                if len(next_posses) > 0:
                    next_ind = next_posses[0]
                    if next_ind - ind > 1:
                        self.fill_between(notes, ind, next_ind)
                    ind = next_ind
                else:
                    ind += 1
            else:
                ind += 1

    def fill_between(self, notes, ind1, ind2):
        num_notes_to_fill = (ind2 - ind1) - 1
        tot_dist = notes[ind2].timing.start64th - notes[ind1].timing.start64th
        if num_notes_to_fill == 1:
            self.place_between(notes, ind1)
        elif num_notes_to_fill == 2:
            self.make_triplet(notes, ind1)
        else:
            addon = tot_dist/(num_notes_to_fill + 1)
            for ind, note in enumerate(notes[ind1+1:ind2]):
                note.timing.start64th = notes[ind1].timing.start64th + int(addon * (ind + 1))

    def place_between(self, notes, ind):
        dist64ths = notes[ind + 2].timing.start64th - notes[ind].timing.start64th
        dist_ticks = notes[ind + 2].midi_timing.on_tick - notes[ind].midi_timing.on_tick
        dist_prop = (notes[ind + 1].midi_timing.on_tick - notes[ind].midi_timing.on_tick)/dist_ticks
        addon = int(dist_prop * dist64ths)
        addon = int(math.ceil(addon/self.min_64ths_dist)) * self.min_64ths_dist
        notes[ind + 1].timing.start64th = int(notes[ind].timing.start64th + addon)

    def make_triplet(self, notes, ind):
        for note in notes[ind:ind + 3]:
            note.timing.tuplet_note_duration64ths = 8
            note.timing.tuplet_duration64ths = 16
            note.timing.normal_notes = 2
            note.timing.tuplet_length = 3
        notes[ind].timing.tuplet_note_type = "start"
        notes[ind].timing.duration64ths = 4
        notes[ind + 1].timing.tuplet_note_type = "mid"
        notes[ind + 1].timing.start64th = notes[ind].timing.start64th + 4
        notes[ind + 1].timing.duration64ths = 8
        notes[ind + 2].timing.tuplet_note_type = "end"
        notes[ind + 2].timing.duration64ths = 4
        notes[ind + 2].timing.start64th = notes[ind].timing.start64th + 12

    def fit_against(self, notes_to_fit, existing_notes):
        for ntf in notes_to_fit:
            for ex in existing_notes:
                if abs(ntf.midi_timing.on_tick - ex.midi_timing.on_tick) < 100:
                    ntf.timing.start64th = ex.timing.start64th

    def get_neighbourhoods(self):
        in_a_hood = []
        tolerance = self.export_spec.get_value("tolerance_ms")
        for ind, note in enumerate(self.notes):
            if note not in in_a_hood:
                neighbourhood = [n for n in self.notes[ind:] if abs(n.midi_timing.on_tick - note.midi_timing.on_tick) < tolerance]
                neighbourhood.sort(key=lambda x: x.pitch)
                self.neighbourhoods.append(neighbourhood)
                in_a_hood.extend(neighbourhood)

    def get_note_sets_from_volume(self):
        for hood in self.neighbourhoods:
            if len(hood) >= 2:
                snotes = sorted(hood, key=lambda x: x.pitch)
                self.lh_notes.append(snotes[0])
                self.rh_notes.append(snotes[-1])
                for i in range(1, len(snotes)-1):
                    self.chord_note_lists[i - 1].append(snotes[i])
            if len(hood) == 1:
                note = hood[0]
                if note.volume > 57 or note.pitch > 65:
                    self.rh_notes.append(note)
                else:
                    self.lh_notes.append(note)

    def get_note_sets(self):
        for hood in self.neighbourhoods:
            if len(hood) >= 2:
                snotes = sorted(hood, key=lambda x: x.pitch)
                self.lh_notes.append(snotes[0])
                self.rh_notes.append(snotes[-1])
                for i in range(1, len(snotes)-1):
                    self.chord_note_lists[i - 1].append(snotes[i])
            if len(hood) == 1:
                note = hood[0]
                if note.pitch >= 60:
                    if len(self.rh_notes) == 0:
                        self.rh_notes.append(note)
                    else:
                        rh_dist = abs(self.rh_notes[-1].pitch - note.pitch)
                        if rh_dist >= 12 and note.pitch < 72:
                            self.lh_notes.append(note)
                        else:
                            self.rh_notes.append(note)
                else:
                    if len(self.lh_notes) == 0:
                        self.lh_notes.append(note)
                    else:
                        lh_dist = abs(self.lh_notes[-1].pitch - note.pitch)
                        if lh_dist >= 12 and note.pitch > 48:
                            self.rh_notes.append(note)
                        else:
                            self.lh_notes.append(note)

    def get_bpm(self):
        lh_s_dists = [td/960 for td in self.lh_tick_dists]
        rh_s_dists = [td/960 for td in self.rh_tick_dists]
        tolerance = 0.15
        lh_cluster_centres = self.get_cluster_centres(lh_s_dists, tolerance)
        rh_cluster_centres = self.get_cluster_centres(rh_s_dists, tolerance)
        unique_dists = self.get_cluster_centres(lh_cluster_centres + rh_cluster_centres, tolerance)
        possible_beat_durations = []
        fracs = [4, 2, 1, 1/2, 1/3, 1/4, 1/6, 1/8]
        for ud in unique_dists:
            possible_beat_durations.extend([frac * ud for frac in fracs if 10 <= 60/(frac * ud) <= 220])
        pairs = []
        for pbd in possible_beat_durations:
            nnpb_lh = int(round(4 * np.mean([(pbd * 960)/lhd for lhd in self.lh_tick_dists])))
            nnpb_rh = int(round(4 * np.mean([(pbd * 960)/rhd for rhd in self.rh_tick_dists])))
            if nnpb_lh <= 16 and nnpb_rh <= 16:
                score = self.get_note_distances_score(pbd, lh_s_dists, rh_s_dists, tolerance)
                pairs.append([score, pbd])
        self.beat_duration_s = sorted(pairs)[-1][1]
        self.bpm = 60/self.beat_duration_s

        # REMOVE THESE
        self.beat_duration_s = 0.7361111111111112
        self.bpm = 81.50943396226414

    def get_note_distances_score(self, pbd, lh_dists, rh_dists, tolerance):
        score = 0
        for frac in [4, 2, 1, 1/2, 1/3, 1/4, 1/6, 1/8]:
            lh_ds = [d for d in lh_dists if abs(d - (pbd * frac)) <= tolerance]
            rh_ds = [d for d in rh_dists if abs(d - (pbd * frac)) <= tolerance]
            score += len(lh_ds) + len(rh_ds)
        return score

    def get_cluster_centres(self, s_dists, tolerance):
        clusters = []
        for s_dist in s_dists:
            has_added = False
            for cluster in clusters:
                if not has_added:
                    if abs(cluster[0] - s_dist) <= tolerance:
                        cluster[1].append(s_dist)
                        cluster[0] = np.mean(cluster[1])
                        has_added = True
            if not has_added:
                clusters.append([s_dist, [s_dist]])
        return [c[0] for c in clusters]

    def map_to_rationalised_beats(self, num_beats):
        pairs = []
        #for b in [4, 2, 1, 0.875, 0.75, 0.5, 0.33, 0.25, 0.125]:
        for b in [4, 2, 1, 0.5, 0.33, 0.25, 0.125]:
                pairs.append([abs(num_beats - b), b])
        pairs.sort()
        rationalised_num_beats = pairs[0][1]
        if rationalised_num_beats <= 0.5:
            rationalised_num_beats = 0.25
        return rationalised_num_beats

    def quantise_from_lh(self):
        n64 = 0
        for ind, note in enumerate(self.lh_notes[0:-1]):
            ticks_to_next = self.lh_notes[ind + 1].midi_timing.on_tick - note.midi_timing.on_tick
            s_to_next = ticks_to_next/960
            beats_to_next = s_to_next/self.beat_duration_s
            beats_to_next = self.map_to_rationalised_beats(beats_to_next)
            note.timing.start64th = n64
            n64 += int(round(beats_to_next * 16))
        self.lh_notes[-1].timing.start64th = n64

    def load_tokens(self, tokens_filepath):
        note_being_constructed = Note()
        addon_ms = 0
        with open(tokens_filepath) as f:
            for token in [l.strip() for l in f.readlines()]:
                if token == "<T>":
                    addon_ms += 5000
                else:
                    nbc = self.read_token(token, note_being_constructed, addon_ms)
                    if nbc is not None:
                        note_being_constructed = nbc
                        self.notes.append(nbc)

    def read_token(self, token, note, addon_ms):
        parts = token.split(",")
        if len(parts) == 1:
            return
        if parts[0] == "piano":
            note = Note()
            note.pitch = int(parts[1])
            note.volume = int(int(parts[2])/100 * 128)
            note.tags = {}
            note.timing = Timing()
            return note
        elif parts[0] == "onset":
            note.midi_timing = MidiTiming(int(parts[1]) + addon_ms)
            return None
        elif parts[0] == "dur":
            note.midi_timing.duration_ticks = TimingUtils.ms_to_ticks(int(parts[1]))
            note.midi_timing.off_tick = note.midi_timing.on_tick + note.midi_timing.duration_ticks

    def make_composition(self):
        self.composition = Composition(title=f"Pianita #{self.export_spec.get_value('pianita_num')}")
        self.composition.bpm = int(round(self.bpm))
        self.composition.musical_directive = self.export_spec.get_value("musical_directives")
        scale = MusicUtils.get_closest_scale_for_notes(self.notes, True)
        if scale.scale_type == "major" or scale.scale_type == "minor":
            self.composition.subtitle = f"In {scale.tonic_letter} {scale.scale_type}".title()
        else:
            self.composition.subtitle = f"In the {scale.scale_type} scale of {scale.tonic_letter}".title()

        self.composition.num_bars = max([n.bar_num for n in self.lh_notes])
        self.composition.num_episodes = 1
        self.composition.beats_per_bar = 4
        self.composition.bars_hash = {}
        self.composition.note_sequences_hash = {}
        self.composition.episodes_hash = {}
        episode = Episode(episode_num=1, form_id="A", num_bars=self.composition.num_bars)
        self.composition.episodes_hash[1] = episode
        self.composition.bars = [Bar(bar_num=i + 1, episode_bar_num=i + 1) for i in range(0, self.composition.num_bars)]

        NoteSequence.note_sequence_num = 0
        prev_volume_direction = None
        for bar in self.composition.bars:
            lh_note_sequence = NoteSequence(note_sequence_num=NoteSequence.note_sequence_num, bar_num=bar.bar_num, track_num=0, channel_num=0, instrument_num=0)
            rh_note_sequence = NoteSequence(note_sequence_num=NoteSequence.note_sequence_num + 1, bar_num=bar.bar_num, track_num=1, channel_num=1, instrument_num=0)
            NoteSequence.note_sequence_num += 2
            lh_note_sequence.notes = []
            rh_note_sequence.notes = []
            bar.note_sequences = []
            bar.episode_num = 1
            bar.directions = []
            self.add_notes_to_note_sequence(self.lh_notes, lh_note_sequence, bar)
            self.add_notes_to_note_sequence(self.rh_notes, rh_note_sequence, bar)
            if len(lh_note_sequence.notes) > 0:
                self.composition.note_sequences_hash[lh_note_sequence.note_sequence_num] = lh_note_sequence
                bar.note_sequences.append(lh_note_sequence)
            if len(rh_note_sequence.notes) > 0:
                self.composition.note_sequences_hash[rh_note_sequence.note_sequence_num] = rh_note_sequence
                bar.note_sequences.append(rh_note_sequence)

            self.add_chord_notes_to_bar(bar)
            v_note_sets = [ns.notes for ns in bar.note_sequences if ns.track_num == 1]
            if len(v_note_sets) == 0:
                v_note_sets = [ns.notes for ns in bar.note_sequences if ns.track_num == 0]
            if len(v_note_sets) > 0:
                v_notes = v_note_sets[0]
                bar_volume = np.mean([n.volume for n in v_notes])
                new_volume_direction = VolumeUtils.get_vol_direction(bar_volume)
                if prev_volume_direction != new_volume_direction:
                    bar.volume_direction = new_volume_direction
                prev_volume_direction = new_volume_direction

        for bar in self.composition.bars:
            bar.start64th = bar.bar_num * 64
            bdt = int((60 / self.bpm) * 960) * 4
            if self.export_spec.get_value("expression") == "per_score":
                bar.start_tick = int((bar.bar_num - 1) * bdt)
            else:
                if bar.bar_num == 1:
                    bar.start_tick = 0
                else:
                    notes_in_bar = ExtractionUtils.get_notes_in_bar(bar)
                    ordered_notes = sorted(notes_in_bar, key=lambda x: x.timing.start64th)
                    bar.start_tick = ordered_notes[0].midi_timing.on_tick

            self.composition.bars_hash[bar.bar_num] = bar
            ticks_per_64th = bdt / 64
            bar.tick_timings = [int(round(ticks_per_64th * t)) for t in range(0, 65)]
            bar.bar_random_int = random.randint(0, 100000)

        for ind, bar in enumerate(self.composition.bars):
            bar.duration_ticks = int((60 / self.bpm) * 960) * 4
            if self.export_spec.get_value("expression") != "per_score" and (ind < len(self.composition.bars) - 1):
                next_bar = self.composition.bars[ind + 1]
                bar.duration_ticks = next_bar.start_tick - bar.start_tick

        self.export_total(scale)

    def add_notes_to_note_sequence(self, notes, note_sequence, bar):
        for note in notes:
            if note.bar_num == bar.bar_num:
                note_sequence.notes.append(note)
                note.note_sequence_num = note_sequence.note_sequence_num
        for ind, note in enumerate(note_sequence.notes):
            next_note_start64th = 64 if ind == len(note_sequence.notes) - 1 else note_sequence.notes[ind + 1].timing.start64th
            if note.timing.tuplet_note_type is None:
                note.timing.duration64ths = next_note_start64th - note.timing.start64th

                # REMOVE THIS _ SHOULDN'T BE HAPPENING!

                if note.timing.duration64ths == 0:
                    note.timing.duration64ths = 1

    def add_chord_notes_to_bar(self, bar):
        note_sequences_for_this_bar = []
        for i in range(0, 8):
            ns = NoteSequence(note_sequence_num=NoteSequence.note_sequence_num + i + 2, bar_num=bar.bar_num, track_num=i+2, channel_num=i+2, instrument_num=0)
            ns.notes = []
            note_sequences_for_this_bar.append(ns)
        NoteSequence.note_sequence_num += 8
        chord_notes_for_this_bar = []
        for chord_note_list in self.chord_note_lists:
            for note in chord_note_list:
                if note.bar_num == bar.bar_num:
                    chord_notes_for_this_bar.append(note)
        for ind, chord_note in enumerate(chord_notes_for_this_bar):
            chord = [c for c in chord_notes_for_this_bar if c.timing.start64th == chord_note.timing.start64th and chord_notes_for_this_bar.index(c) >= ind]
            before = [c for c in chord_notes_for_this_bar if c.timing.start64th == chord_note.timing.start64th and chord_notes_for_this_bar.index(c) < ind]
            if len(before) == 0:
                for nind, n in enumerate(chord):
                    addon = 0 if n.pitch <= 60 else 4
                    ns = note_sequences_for_this_bar[nind + addon]
                    ns.notes.append(n)
        for ns in note_sequences_for_this_bar:
            if len(ns.notes) > 0:
                bar.note_sequences.append(ns)
                self.composition.note_sequences_hash[ns.note_sequence_num] = ns
                for ind, note in enumerate(ns.notes):
                    next_note_start64th = 64 if ind == len(ns.notes) - 1 else ns.notes[ind + 1].timing.start64th
                    note.note_sequence_num = ns.note_sequence_num
                    if note.timing.tuplet_note_type is None:
                        note.timing.duration64ths = next_note_start64th - note.timing.start64th

    def exaggerate_expression(self, performance_spec, expression):
        on_score_composition = copy.deepcopy(self.composition)
        TimingUtils.add_midi_timings(on_score_composition, performance_spec)
        original_notes = ExtractionUtils.get_notes_in_composition(self.composition)
        on_score_notes = ExtractionUtils.get_notes_in_composition(on_score_composition)
        for note in self.notes:
            note.tick_addon = None
        addon = 0
        self.rh_notes[0].tick_addon = 0
        for ind, note in enumerate(self.rh_notes[1:]):
            pre_note = self.rh_notes[ind]
            on_score_note = on_score_notes[original_notes.index(note)]
            pre_on_score_note = on_score_notes[original_notes.index(pre_note)]
            offset_ticks = note.midi_timing.on_tick - pre_note.midi_timing.on_tick
            on_score_offset_ticks = on_score_note.midi_timing.on_tick - pre_on_score_note.midi_timing.on_tick
            expressive_direction = offset_ticks - on_score_offset_ticks
            addon += int(expressive_direction * self.export_spec.get_value("exaggeration_factor"))
            for n in [nh for nh in self.neighbourhoods if note in nh][0]:
                n.tick_addon = addon
        current_addon = 0
        for ind, note in enumerate(self.lh_notes):
            if note.tick_addon is None:
                for n in [nh for nh in self.neighbourhoods if note in nh][0]:
                    n.tick_addon = current_addon
            else:
                current_addon = note.tick_addon
        for note in self.notes:
            note.midi_timing.on_tick += note.tick_addon
            note.midi_timing.off_tick += note.tick_addon

    def export_total(self, scale):

        if self.export_spec.get_value("expression") == "per_score":
            VolumeUtils.homogenise_volumes(self.composition)

        score_parts = [{"part_id": "Piano", "part_name": "Piano",
                        "track_details": [("treble", [1, 6, 7, 8, 9]), ("bass", [0, 2, 3, 4, 5])]}]

        soundfont_filepath = SFYamahaPiano.soundfont_filepath

        reverb_param = Parameter("reverb")
        reverb_param.add_constrained_value(1.2, "efi=A")

        sustain_pedal_bars_param = Parameter("sustain_pedal_bars")
        if self.export_spec.get_value("expression") != "per_score":
            sustain_pedal_bars_param.add_constrained_value(1, "efi=A")
        else:
            sustain_pedal_bars_param.add_constrained_value(0, "efi=A")

        performance_params = [
            reverb_param,
            sustain_pedal_bars_param,
            Parameter("sustain_pedal_reset", "episode"),
            Parameter("add_midi_timings", self.export_spec.get_value("expression") == "per_score")
        ]

        performance_spec = ParameterisedSpecification(performance_params)

        expression = self.export_spec.get_value("expression")
        if expression == "modified":
            self.exaggerate_expression(performance_spec, expression)

        """
        if self.export_spec.get_value("analyse_expression") == True:
            analyser_params = [
                Parameter("applier_class_name", "ExpressionAnalyser"),
            ]
            analyser_spec = ParameterisedSpecification(analyser_params)
            analyser = ExpressionAnalyser(analyser_spec)
            self.composition = analyser.apply(self.composition)
        """

        note_colours_hash = {}
        note_colours_hash["speed=slow"] = "orange"
        note_colours_hash["speed=very slow"] = "red"
        note_colours_hash["highlight=yes"] = "green"

        """
        notes = ExtractionUtils.get_notes_for_track_num(self.composition, 1)
        notes[0].tags["highlight"] = "yes"
        notes[11].tags["highlight"] = "yes"
        notes[15].tags["highlight"] = "yes"
        notes[20].tags["highlight"] = "yes"
        notes[22].tags["highlight"] = "yes"

        notes = ExtractionUtils.get_notes_for_track_num(self.composition, 0)
        notes[5].tags["highlight"] = "yes"
        notes[7].tags["highlight"] = "yes"
        notes[8].tags["highlight"] = "yes"
        """

        pianita_num = self.export_spec.get_value("pianita_num")
        total_exporter_params = [
            Parameter("applier_class_name", "TotalExporter"),
            Parameter("output_stem", f"/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Outputs/AriaScores/pianita_{pianita_num}"),
            Parameter("output_composition_id", None),
            Parameter("composition_title", f"Pianita No. {pianita_num}"),
            Parameter("creator", "Aria"),
            Parameter("export_score", False),
            Parameter("export_audio", False),
            Parameter("export_video", False),
            Parameter("export_data", True),
            Parameter("score_parts", score_parts),
            Parameter("scale", scale),
            Parameter("show_chord_name", False),
            Parameter("show_episode_duration", False),
            Parameter("show_colours", True),
            Parameter("note_colours_hash", note_colours_hash),
            Parameter("margin_colours_hash", None),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("musescore_cli", "/Applications/MuseScore\ 3.app/Contents/MacOS/mscore"),
            Parameter("resources_dir", "/Users/Simon/Dropbox/Code/Parley/ParleyV2/Resources"),
            Parameter("ffmpeg_cli", "ffmpeg"),
            Parameter("codec", "libx264"),
            Parameter("audio_formats", ["WAV", "MP3"]),
            Parameter("video_fade_in", False),
            Parameter("video_border_pixels", 2),
            Parameter("video_border_colour", (200, 200, 200, 200)),
            Parameter("dpi", 200),
            Parameter("fps", 5),
            Parameter("end_rest_ms", 3000),
            Parameter("performance_spec", performance_spec)
        ]
        exporter_spec = ParameterisedSpecification(total_exporter_params)
        exporter = TotalExporter(exporter_spec)
        exporter.apply(self.composition)


corpus_dir = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/experiments/aria_final_corpus"
def make_score(piece_id, musical_directives, pianita_num, expression, exaggeration_factor, keep_slow=False, make_loud=False, tolerance=100, analyse_expression=True):
    export_params = [
        Parameter("applier_class_name", "AriaScoreExporter"),
        Parameter("tokens_filepath", f"{corpus_dir}/{piece_id}.txt"),
        Parameter("musical_directives", musical_directives),
        Parameter("filestem", piece_id),
        Parameter("pianita_num", pianita_num),
        Parameter("expression", expression),
        Parameter("exaggeration_factor", exaggeration_factor),
        Parameter("keep_slow", keep_slow),
        Parameter("make_loud", make_loud),
        Parameter("analyse_expression", analyse_expression),
        Parameter("tolerance_ms", tolerance)

    ]
    export_spec = ParameterisedSpecification(export_params)
    return export_spec.apply()

"""
from mido import MidiFile

class MidiNote:

  def __init__(self, track_num, pitch, on_tick, off_tick, velocity, on_msg, off_msg):
    self.track_num = track_num
    self.pitch = pitch
    self.on_tick = on_tick
    self.off_tick = off_tick
    self.velocity = velocity
    self.on_msg = on_msg
    self.off_msg = off_msg
    self.overlapping_notes = []
    self.alternative_pitches = []
    self.best_alternative_pitch = None


def get_aria_tokenisation():
    midi_filepath = corpus_dir + "/large_pt_None_68_edited.mid"
    midi_file = MidiFile(midi_filepath)
    notes = []
    for track_num, track in enumerate(midi_file.tracks):
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "note_on":
                note = MidiNote(track_num, msg.note, tick, None, msg.velocity, msg, None)
                notes.append(note)
            if msg.type == "note_off":
                open_notes = [o for o in notes if o.pitch == msg.note and o.off_tick is None]
                for open_note in open_notes:
                    open_note.off_tick = tick
                    open_note.off_msg = msg
    notes.sort(key=lambda x: x.on_tick)
    take_off = notes[0].on_tick
    for note in notes:
        note.on_tick -= take_off
        note.off_tick -= take_off
    for n in notes:
        on_ms = int((n.on_tick/960) * 1000)
        dur_ms = int(((n.off_tick/960) * 1000) - on_ms)
        print(f"piano,{n.pitch},{n.velocity}")
        print(f"onset,{on_ms}")
        print(f"dur,{dur_ms}")

get_aria_tokenisation()

"""

# THESE WORK
original_composition = make_score("large_pt_None_68", "lacrimoso", 17, "original", 0, False)
#make_score("small_pt_classical_37", "upbeat", 117, "original", 1)
#make_score("medium_ft_classical_56", "quick", 20000, "original", 0.25)
#edited_composition = make_score("large_pt_None_68_edited", "lacrimoso", 17, "original", 0, analyse_expression=False)

# TO MASTER NEXT
#make_score("medium_ft_classical_75", "bright", 17171, 0, False, False, 50)

# MORE TO TRY
#make_score("large_ft_jazz_92", "jazzy", 1717)
#make_score("large_ft_classical_21", "smooth", 1717)
#make_score("large_ft_classical_83", "help", 171717)
#make_score("medium_ft_None_20", "bright", 171717)
#make_score("medium_ft_jazz_3", "bright", 17171)



from ParleyV2.Generators.LoadCompositionGenerator import *
from ParleyV2.Specifications.ConstrainedSpecification import *
from ParleyV2.Utils.ExtractionUtils import *

def load_pianita():

    pianita_dir = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Outputs/AriaScores"
    load_params = [
            Parameter("applier_class_name", "LoadCompositionGenerator"),
            Parameter("file_path", pianita_dir + "/pianita_17.xml")
        ]
    load_spec = ParameterisedSpecification(load_params)
    composition = load_spec.apply()

    reverb_param = Parameter("reverb")
    reverb_param.add_constrained_value(1.2, "efi=A")

    sustain_pedal_bars_param = Parameter("sustain_pedal_bars")
    sustain_pedal_bars_param.add_constrained_value(1, "efi=A")

    performance_params = [
        reverb_param,
        sustain_pedal_bars_param,
        Parameter("sustain_pedal_reset", "episode"),
        Parameter("add_midi_timings", False)
    ]

    performance_spec = ParameterisedSpecification(performance_params)
    soundfont_filepath = SFYamahaPiano.soundfont_filepath

    mp3_export_params = [
                Parameter("applier_class_name", "AudioExporter"),
                Parameter("output_stem", pianita_dir + "/temp"),
                Parameter("audio_formats", ["MP3"]),
                Parameter("soundfont_filepath", soundfont_filepath),
                Parameter("fluidsynth_cli", "fluidsynth"),
                Parameter("end_rest_ms", 3000),
                Parameter("performance_spec", performance_spec)
    ]

    mp3_export_spec = ParameterisedSpecification(mp3_export_params)
   # mp3_export_spec.apply(composition)

    score_parts = [{"part_id": "Piano", "part_name": "Piano",
                    "track_details": [("treble", [1, 6, 7, 8, 9]), ("bass", [0, 2, 3, 4, 5])]}]

    total_exporter_params = [
        Parameter("applier_class_name", "TotalExporter"),
        Parameter("output_stem", pianita_dir + "/temp"),
        Parameter("output_composition_id", None),
        Parameter("composition_title", f"Pianita No. 17"),
        Parameter("creator", "Aria"),
        Parameter("export_score", True),
        Parameter("export_audio", True),
        Parameter("export_video", True),
        Parameter("export_data", True),
        Parameter("score_parts", score_parts),
        Parameter("scale", MusicUtils.get_named_scale("d_minor")),
        Parameter("show_chord_name", False),
        Parameter("show_episode_duration", False),
        Parameter("show_colours", True),
        Parameter("note_colours_hash", {}),
        Parameter("margin_colours_hash", None),
        Parameter("soundfont_filepath", soundfont_filepath),
        Parameter("fluidsynth_cli", "fluidsynth"),
        Parameter("musescore_cli", "/Applications/MuseScore\ 3.app/Contents/MacOS/mscore"),
        Parameter("resources_dir", "/Users/Simon/Dropbox/Code/Parley/ParleyV2/Resources"),
        Parameter("ffmpeg_cli", "ffmpeg"),
        Parameter("codec", "libx264"),
        Parameter("audio_formats", ["WAV", "MP3"]),
        Parameter("video_fade_in", False),
        Parameter("video_border_pixels", 2),
        Parameter("video_border_colour", (200, 200, 200, 200)),
        Parameter("dpi", 200),
        Parameter("fps", 5),
        Parameter("end_rest_ms", 3000),
        Parameter("performance_spec", performance_spec)
    ]
    exporter_spec = ParameterisedSpecification(total_exporter_params)
    exporter = TotalExporter(exporter_spec)
    exporter.apply(composition)
    return composition

copy_composition = load_pianita()

o_notes = ExtractionUtils.get_notes_in_composition(original_composition)
c_notes = ExtractionUtils.get_notes_in_composition(copy_composition)

o_bars = ExtractionUtils.get_bars_for_episode_num(original_composition, 1)
c_bars = ExtractionUtils.get_bars_for_episode_num(copy_composition, 1)

for ind, o_n in enumerate(o_notes):
    c_n = c_notes[ind]
    if o_n.midi_timing != c_n.midi_timing:
        print(ind, o_n.pitch, c_n.pitch)

for ind, o_bar in enumerate(o_bars):
    c_bar = c_bars[ind]
    if o_bar != c_bar:
        print(o_bar)
        print(c_bar)

