import numpy as np
from ParleyV2.Utils.ExtractionUtils import *

class DynamicsUtils:

    def update_directions(composition, dynamic_lead_track_num):
        prev_direction = None
        for bar in composition.bars:
            bar.directions = []
            if prev_direction is not None and bar.volume_direction == prev_direction:
                bar.volume_direction = None
            prev_direction = bar.volume_direction if bar.volume_direction is not None else prev_direction
        #dynamic_lead_track_num = gen_spec.get_value("dynamic_lead_track_num")
        for episode_num in range(1, composition.num_episodes + 1):
            bars = ExtractionUtils.get_bars_for_episode_num(composition, episode_num)
            episode_start_vol = DynamicsUtils.get_av_note_volume(bars[0], dynamic_lead_track_num)
            episode_end_vol = DynamicsUtils.get_av_note_volume(bars[-1], dynamic_lead_track_num)
            if episode_start_vol is not None and episode_end_vol is not None:
                is_increasing = episode_end_vol > episode_start_vol + 15
                is_decreasing = episode_start_vol > episode_end_vol + 15
                for bar in bars:
                    prev_bar = None if bar.bar_num == 1 else composition.bars_hash[bar.bar_num - 1]
                    if prev_bar is not None:
                        if prev_bar.volume_direction is not None and bar.volume_direction is None:
                            if is_increasing:
                               bar.directions.append("cresc.")
                            elif is_decreasing:
                                bar.directions.append("dim.")

        for episode_num in range(1, composition.num_episodes + 1):
            bars = ExtractionUtils.get_bars_for_episode_num(composition, episode_num)
            episode_start_duration = bars[0].duration_ticks
            episode_end_duration = bars[-1].duration_ticks
            is_slowing_down = episode_end_duration > episode_start_duration + 200
            is_speeding_up = episode_start_duration > episode_end_duration + 200
            for bar in bars:
                prev_bar = None if bar.bar_num == 1 else composition.bars_hash[bar.bar_num - 1]
                if prev_bar is not None:
                    if prev_bar.volume_direction is not None and bar.volume_direction is None:
                        if is_slowing_down:
                           bar.directions.append("rall.")
                        elif is_speeding_up:
                            bar.directions.append("accel.")

    def get_av_note_volume(bar, track_num):
        note_volumes = []
        for note_sequence in [n for n in bar.note_sequences if n.track_num == track_num]:
            note_volumes.extend([n.volume for n in note_sequence.notes])
        if len(note_volumes) > 0:
            return np.mean(note_volumes)
        else:
            return None

