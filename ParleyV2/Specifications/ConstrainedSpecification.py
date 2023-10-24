import random
from importlib import import_module

# CONSTRAINTS


class Constraint:

    def __init__(self, constraint_string):
        self.constraint_condition = [c for c in ["=", "<", ">"] if c in constraint_string][0]
        self.constraint_subject = constraint_string.split(self.constraint_condition)[0]
        self.constraint_requirement = constraint_string.split(self.constraint_condition)[1]

    def is_satisfied(self, composition, episode, bar, chord, note, track_num):

        if self.constraint_subject == "efi":
            if episode is None:
                return False
            return (episode.form_id == self.constraint_requirement)

        to_check = None
        if self.constraint_subject == "en": to_check = episode.episode_num
        elif self.constraint_subject == "cbn": to_check = bar.bar_num - 1
        elif self.constraint_subject == "cbc": to_check = bar.bar_num - 1
        elif self.constraint_subject == "br": to_check = bar.bar_random_int
        elif self.constraint_subject == "tn": to_check = track_num

        if "/" in self.constraint_requirement:
            numerator = int(self.constraint_requirement.split("/")[0]) - 1
            denominator = int(self.constraint_requirement.split("/")[1])
            return to_check % denominator == numerator

        if self.constraint_subject == "tn":
            return track_num == int(self.constraint_requirement)

        if self.constraint_subject == "en":
            episode_num_required = int(self.constraint_requirement)
            if "-" in self.constraint_requirement:
                episode_num_required = composition.num_episodes - (int(self.constraint_requirement[1:]) - 1)
            return episode.episode_num == episode_num_required

        if self.constraint_subject == "cbn" or self.constraint_subject == "ebn":
            bar_num_required = int(self.constraint_requirement)
            if "-" in self.constraint_requirement:
                bar_num_required = composition.num_bars if self.constraint_subject == "cbn" else episode.num_bars
                bar_num_required -= (int(self.constraint_requirement[1:]) - 1)
            if self.constraint_subject == "ebn":
                return bar.episode_bar_num == bar_num_required
            else:
                return bar.bar_num == bar_num_required

# VARIABLES


class GlobalVariables:

    def __init__(self):
        self.variables = {}

    def add_variable(self, variable_name, value):
        self.variables[variable_name] = value

    def contains(self, variable_name):
        return variable_name in self.variables

    def get_value(self, variable_name):
        return self.variables[variable_name]

global_variables = GlobalVariables()

# VALUES


class Value:

    randoms_hash = {}

    def __init__(self, value_id):
        self.value_id = value_id

    def expand_value(self, composition, episode, bar, chord, note):
        if isinstance(self.value_id, str) and global_variables.contains(self.value_id):
            return global_variables.get_value(self.value_id)
        return self.value_id

        # TODO expand values referencing the composition


class ConstrainedValue:

    def __init__(self, value, constraints_string, priority):
        self.value = Value(value)
        self.constraints = None if constraints_string is None else [Constraint(c) for c in constraints_string.split(",")]
        self.priority = priority

    def get_constraints(self, constraints_string):
        return None if constraints_string is None else [Constraint(c) for c in constraints_string.split(",")]

    def is_satisfied(self, priority, composition, episode, bar, chord, note, track_num):
        if self.priority != priority:
            return False
        if self.constraints is not None:
            for constraint in self.constraints:
                if not constraint.is_satisfied(composition, episode, bar, chord, note, track_num):
                    return False
        return True


class ConstrainedRandomValue(ConstrainedValue):

    def __init__(self, value, constraints_string, pc, priority):
        self.value = Value(value)
        self.constraints = self.get_constraints(constraints_string)
        self.pc = pc
        self.priority = priority


class ConstrainedRandomRangeValue(ConstrainedValue):

    def __init__(self, lower_value, upper_value, constraints_string, priority):
        self.lower_value = Value(lower_value)
        self.upper_value = Value(upper_value)
        self.constraints = self.get_constraints(constraints_string)
        self.priority = priority


class ConstrainedInterpolationValue(ConstrainedValue):

    def __init__(self, value_id, interpolation_point, constraints_string, priority):
        self.value = Value(value_id)
        self.interpolation_point = interpolation_point
        self.constraints = self.get_constraints(constraints_string)
        self.priority = priority


# PARAMETERS


class Parameter:

    def __init__(self, name, value_id=None):
        self.name = name
        self.value = None if value_id is None else Value(value_id)
        self.constrained_values = []
        self.constrained_random_values = []
        self.constrained_random_range_values = []
        self.constrained_interpolation_details = []
        self.interpolation_counter = None

    def set_value(self, value_id):
        self.value = None if value_id is None else Value(value_id)

    def add_constrained_value(self, value, constraints_string, priority=0):
        for c_string in constraints_string.split("|"):
            self.constrained_values.append(ConstrainedValue(value, c_string, priority))

    def add_constrained_random_value(self, value, constraints_string, pc, priority=0):
        if constraints_string is None:
            self.constrained_random_values.append(ConstrainedRandomValue(value, None, pc, priority))
        else:
            for c_string in constraints_string.split("|"):
                self.constrained_random_values.append(ConstrainedRandomValue(value, c_string, pc, priority))

    def add_constrained_random_range_value(self, lower_value, upper_value, constraints_string, priority=0):
        if constraints_string is None:
            self.constrained_random_range_values.append(ConstrainedRandomRangeValue(lower_value, upper_value, None, priority))
        else:
            for c_string in constraints_string.split("|"):
                self.constrained_random_range_values.append(ConstrainedRandomRangeValue(lower_value, upper_value, c_string, priority))

    def set_interpolation_counter(self, interpolation_counter):
        self.interpolation_counter = interpolation_counter

    def add_constrained_interpolation_value(self, value_id, interpolation_point, constraints_string, priority=0):
        if constraints_string is None:
            self.constrained_interpolation_details.append(ConstrainedInterpolationValue(value_id, interpolation_point, None, priority))
        else:
            for c_string in constraints_string.split("|"):
                self.constrained_interpolation_details.append(ConstrainedInterpolationValue(value_id, interpolation_point, c_string, priority))

    def instantiate(self, composition, episode, bar, chord, note, track_num):

        # First, check if there is a value given and use that

        if self.value is not None:
            return self.value.expand_value(composition, episode, bar, chord, note)

        # Next,check constrained normal values

        for priority in range(10, -1, -1):
            satisfied_values = [c.value for c in self.constrained_values if c.is_satisfied(priority, composition, episode, bar, chord, note, track_num)]
            if len(satisfied_values) > 0:
                value = random.choice(satisfied_values)
                return value.expand_value(composition, episode, bar, chord, note)

        # Next, check constrained random values

            satisfied_crvs = [crv for crv in self.constrained_random_values if crv.is_satisfied(priority, composition, episode, bar, chord, note, track_num)]
            tot = sum([r.pc for r in satisfied_crvs])
            if tot > 0:
                rn = random.randint(0, tot)
                cumul = 0
                for rv in satisfied_crvs:
                    cumul += rv.pc
                    if cumul >= rn:
                        return rv.value.expand_value(composition, episode, bar, chord, note)

            # Next, check random range values

            satisfied_ranges = [c for c in self.constrained_random_range_values if c.is_satisfied(priority, composition, episode, bar, chord, note, track_num)]
            if len(satisfied_ranges) > 0:
                r = random.choice(satisfied_ranges)
                lower = r.lower_value.expand_value(composition, episode, bar, chord, note)
                upper = r.upper_value.expand_value(composition, episode, bar, chord, note)
                return random.randint(lower, upper)

            # Next, calculate the interpolation

            details_satisfied = [d for d in self.constrained_interpolation_details if d.is_satisfied(priority, composition, episode, bar, chord, note, track_num)]
            if len(details_satisfied) > 0:
                details_satisfied.sort(key=lambda x: x.interpolation_point)
                frac = None
                if self.interpolation_counter == "ebp" or self.interpolation_counter == "ebk":
                    frac = (bar.episode_bar_num - 1)/(episode.num_bars - 1)
                for ind in range(0, len(details_satisfied) - 1):
                    if frac is not None and details_satisfied[ind].interpolation_point <= frac <= details_satisfied[ind + 1].interpolation_point:
                        dist = details_satisfied[ind + 1].interpolation_point - details_satisfied[ind].interpolation_point
                        ffrac = (frac - details_satisfied[ind].interpolation_point)/dist
                        v1 = details_satisfied[ind].value.expand_value(composition, episode, bar, chord, note)
                        v2 = details_satisfied[ind + 1].value.expand_value(composition, episode, bar, chord, note)
                        return (v1 * (1 - ffrac)) + (v2 * ffrac)

        return None


# SPECIFICATIONS


class ParameterisedSpecification:

    def __init__(self, constrained_parameters, variables_hash={}):
        self.parameters = {}
        for parameter in constrained_parameters:
            if parameter.name in variables_hash:
                self.parameters[parameter.name] = Parameter(parameter.name, variables_hash[parameter.name])
            else:
                self.parameters[parameter.name] = parameter

    def get_value(self, param_name):
        if param_name not in self.parameters:
            return None
        parameter = self.parameters[param_name]
        if parameter.value is None:
            return None
        return parameter.value.expand_value(None, None, None, None, None)

    def instantiate_me(self, composition=None, bar=None, chord=None, note=None):

        episode = None if (composition is None or bar is None) else composition.episodes_hash[bar.episode_num]
        track_num = None if note is None else composition.note_sequences_hash[note.note_sequence_num].track_num
        instantiated_params = {}
        for param_name in self.parameters.keys():
            instantiated_param = self.parameters[param_name].instantiate(composition, episode, bar, chord, note, track_num)
            instantiated_params[param_name] = instantiated_param
        return instantiated_params

    def apply(self, starting_composition=None):
        applier_class_name = self.parameters["applier_class_name"].value.value_id
        for class_type in ["Designer", "Generator", "Editor", "Analyser", "Communicator", "Exporter", "Extractor"]:
            if class_type in applier_class_name:
                applier_path = f"ParleyV2.{class_type}s.{applier_class_name}"
                module = import_module(applier_path)
                klass = getattr(module, applier_class_name)(self)
                return klass.apply(starting_composition)

