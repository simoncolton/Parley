from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.ExtractionUtils import *
import random


class CompositionGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, _):
        compositions = {}
        seed = self.gen_spec.get_value("random_seed")
        previous_composition = Composition(title=self.gen_spec.get_value("title"),
                                           subtitle=self.gen_spec.get_value("subtitle"),
                                           track_notes_hash={}, episode_track_notes_hash={})
        previous_composition.random_seed = seed
        for spec in self.gen_spec.get_value("specs_to_apply"):
            #random.seed(seed)
            if spec.get_value("input_composition_id") is not None:
                composition = compositions[spec.get_value("input_composition_id")]
            else:
                composition = previous_composition
            new_composition = spec.apply(composition)
            self.update_artefacts(new_composition)
            compositions[spec.get_value("output_composition_id")] = new_composition
            previous_composition = new_composition
        return previous_composition

    def update_artefacts(self, composition):
        for track_num in ExtractionUtils.get_track_nums(composition):
            track_notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            composition.track_notes_hash[track_num] = track_notes
            for ind, note in enumerate(track_notes):
                note.track_note_num = ind
            for episode_num in range(1, composition.num_episodes + 1):
                ep_track_notes = ExtractionUtils.get_episode_notes_for_track_num(composition, episode_num, track_num)
                composition.episode_track_notes_hash[(track_num, episode_num)] = ep_track_notes
                for ind, note in enumerate(ep_track_notes):
                    note.episode_track_note_num = ind