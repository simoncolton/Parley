from ParleyV2.Artefacts.Artefacts import *
import random


class CompositionGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, _):
        compositions = {}
        seed = self.gen_spec.get_value("random_seed")
        previous_composition = Composition(title=self.gen_spec.get_value("title"), subtitle=self.gen_spec.get_value("subtitle"))
        previous_composition.random_seed = seed
        for spec in self.gen_spec.get_value("specs_to_apply"):
            #random.seed(seed)
            if spec.get_value("input_composition_id") is not None:
                composition = compositions[spec.get_value("input_composition_id")]
            else:
                composition = previous_composition
            new_composition = spec.apply(composition)
            compositions[spec.get_value("output_composition_id")] = new_composition
            previous_composition = new_composition
        return previous_composition
