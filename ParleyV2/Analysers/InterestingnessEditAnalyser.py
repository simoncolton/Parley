import copy
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Utils.MarginUtils import *


class InterestingnessEditAnalyser:

    def __init__(self, analysis_spec):
        self.analysis_spec = analysis_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        track_num = self.analysis_spec.get_value("track_num")
        num_highlight_bars = self.analysis_spec.get_value("num_highlight_bars")
        min_num_notes = self.analysis_spec.get_value("min_num_notes")
        episode_score_pairs = {}
        for bar in composition.bars:
            episode_num = bar.episode_num
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == track_num and len(note_sequence.notes) >= min_num_notes:
                    score = self.get_bar_score(note_sequence)
                    episode_pairs = [] if episode_num not in episode_score_pairs else episode_score_pairs[episode_num]
                    episode_pairs.append((score, note_sequence))
                    episode_score_pairs[episode_num] = episode_pairs
        num_highlight_bars_per_episode = int(round(num_highlight_bars/composition.num_episodes))
        for key in episode_score_pairs.keys():
            pairs = episode_score_pairs[key]
            pairs = sorted(pairs, key=lambda x: x[0], reverse=True)
            for i in range(0, min(len(pairs), num_highlight_bars_per_episode)):
                note_sequence = pairs[i][1]
                bar = composition.bars_hash[note_sequence.bar_num]
                MarginUtils.add_margin_comment(bar, "Most likely", "green")
        return composition

    def get_bar_score(self, note_sequence):
        score = 0
        for note in note_sequence.notes:
            if note.sorted_pitch_classes is not None:
                pos = note.sorted_pitch_classes.index(MusicUtils.pitch_class(note.pitch))
                score += (10 - pos)
        return score/len(note_sequence.notes)
