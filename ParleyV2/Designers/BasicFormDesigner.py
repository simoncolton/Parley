import copy
from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.TimingUtils import *

class BasicFormDesigner:

    def __init__(self, design_spec):
        self.design_spec = design_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        composition.bars = []
        composition.episodes_hash = {}
        composition.bars_hash = {}
        composition.note_sequences_hash = {}
        num_cycles = self.design_spec.get_value("num_cycles")
        cycle_form = self.design_spec.get_value("cycle_form")
        total_ms = self.design_spec.get_value("composition_duration_ms")
        ms_per_episode = total_ms/(len(cycle_form) * num_cycles)
        episode_num = 1
        comp_bar_num = 1
        addon_tick = 0
        for cycle_num in range(0, num_cycles):
            for form_id in cycle_form:
                episode = Episode(episode_num=episode_num, form_id=form_id)
                composition.episodes_hash[episode_num] = episode
                dummy_bar = Bar(episode_num=episode_num)
                spec = self.design_spec.instantiate_me(composition, dummy_bar)
                empty_bars = self.get_empty_bars(ms_per_episode, episode, spec, comp_bar_num, addon_tick)
                for bar in empty_bars:
                    composition.bars_hash[bar.bar_num] = bar
                episode.num_bars = len(empty_bars)
                composition.bars.extend(empty_bars)
                episode_num += 1
                comp_bar_num += len(empty_bars)
                addon_tick = empty_bars[-1].end_tick + 1
        composition.num_bars = len(composition.bars)
        composition.num_episodes = len(composition.episodes_hash.keys())
        s64 = 0
        for bar in composition.bars:
            bar.start64th = s64
            s64 += bar.num_beats * 16
        return composition

    def get_empty_bars(self, episode_duration_ms, episode, spec, comp_bar_num, addon_tick):
        bars = []
        s = spec["bar_start_duration_ms"]
        f = spec["bar_end_duration_ms"]
        t = episode_duration_ms
        n = int(((2 * t) - s + f) // (f + s))
        x = (s - f) / n
        short_t = (n * s) - (x * (n - 1) * n) / 2
        diff = t - short_t
        addon = diff/n
        start_tick = addon_tick
        for i in range(0, n):
            cb_num = comp_bar_num + i
            eb_num = i + 1
            ms_duration = (s - (i * x)) + addon
            bar_duration_ticks = TimingUtils.ms_to_ticks(ms_duration)
            end_tick = start_tick + bar_duration_ticks
            bar = Bar(bar_num=cb_num, episode_bar_num=eb_num,
                      start64th=0, # will calculate this later
                      start_tick=start_tick, end_tick=end_tick, duration_ticks=bar_duration_ticks,
                      num_beats=spec["beats_per_bar"], note_sequences=[], episode_num=episode.episode_num,
                      margin_comments=[], mtg_activation_vectors=[], mtg_activations_hash={}, mtg_activation_highlights=[])
            ticks_per_64th = bar.duration_ticks / 64
            bar.tick_timings = [int(round(ticks_per_64th * t)) for t in range(0, 65)]
            bar.bar_random_int = random.randint(0, 100000)
            start_tick += bar_duration_ticks + 1
            bars.append(bar)
        return bars

