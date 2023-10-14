from Artefacts.Artefacts import *
import random


class OptimisedCompositionGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, _):
        compositions = {}
        seed = self.gen_spec.get_value("random_seed")
        num_trials = self.gen_spec.get_value("num_trials")
        termination_condition = self.gen_spec.get_value("termination_condition")
        analyser = self.gen_spec.get_value("analyser")
        composition_id_to_evaluate = self.gen_spec.get_value("composition_id_to_evaluate")
        termination_achieved = False
        best_composition = None
        best_composition_distance = 100000000
        for trial_num in range(0, num_trials):
            if not termination_achieved:
                previous_composition = Composition(title=self.gen_spec.get_value("title"), subtitle=self.gen_spec.get_value("subtitle"))
                previous_composition.random_seed = seed
                continue_generation = True
                for spec in self.gen_spec.get_value("specs_to_apply"):
                    if continue_generation:
                        #random.seed(seed)
                        if spec.get_value("input_composition_id") is not None:
                            composition = compositions[spec.get_value("input_composition_id")]
                        else:
                            composition = previous_composition
                        new_composition = spec.apply(composition)
                        compositions[spec.get_value("output_composition_id")] = new_composition
                        previous_composition = new_composition
                        if spec.get_value("output_composition_id") == composition_id_to_evaluate:
                            evaluation = analyser.evaluate(previous_composition)
                            distance = abs(evaluation - termination_condition)
                            if distance < best_composition_distance:
                                best_composition_distance = distance
                                best_composition = previous_composition
                            if evaluation == termination_condition:
                                termination_achieved = True
                                best_composition = previous_composition
                            else:
                                if trial_num == num_trials - 1:
                                    previous_composition = best_composition
                                    continue_generation = True
                                else:
                                    continue_generation = False
        return best_composition
