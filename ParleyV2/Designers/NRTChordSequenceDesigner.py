from ParleyV2.Utils.NROUtils import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.MusicUtils import *
import copy


class NRTChordSequenceDesigner:

    def __init__(self, design_spec):
        self.design_spec = design_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        previous_pitches = None
        num_repeated = 0
        chord_num = 1
        composition.chords_hash = {}
        for bar in composition.bars:
            bar.chord_nums = []
            spec = self.design_spec.instantiate_me(composition, bar)
            chord_change_rhythm = spec["chord_change_rhythm"]
            cnro_len = spec["cnro_length"]
            fixed_scale = spec["fixed_scale"]
            chord_type_allowance = spec["chord_type_allowance"]
            max_repetitions = spec["max_repetitions"]
            if fixed_scale is not None and chord_type_allowance is not None:
                num_chords_afforded = MusicUtils.num_chords_satisfying_chord_type_allowance(fixed_scale, chord_type_allowance)
                if num_chords_afforded == 1:
                    max_repetitions = None

            override_chord = spec["override_chord"]
            focal_pitch = spec["focal_pitch"]
            cnro = None
            for cc in chord_change_rhythm:
                if override_chord is not None:
                    pitches = override_chord.pitches
                else:
                    cnro, pitches = NROUtils.get_random_admissible_cnro(previous_pitches, cnro_len, fixed_scale, chord_type_allowance, False)
                pitches = MusicUtils.mapped_to_focal_pitch(pitches, focal_pitch)
                if previous_pitches is not None and MusicUtils.are_same_pitch_classes(pitches, previous_pitches):
                    num_repeated += 1
                else:
                    num_repeated = 1
                if override_chord is None and max_repetitions is not None and num_repeated > max_repetitions:
                    while MusicUtils.are_same_pitch_classes(pitches, previous_pitches):
                        cnro, pitches = NROUtils.get_random_admissible_cnro(previous_pitches, cnro_len,
                                                                            fixed_scale, chord_type_allowance, True)
                        pitches = MusicUtils.mapped_to_focal_pitch(pitches, focal_pitch)
                pitches = MusicUtils.get_root_inversion(pitches)
                chord = Chord(pitches=pitches, scale_name=fixed_scale.tonic_letter + "_" + fixed_scale.scale_type,
                              bar_num=bar.bar_num, cnro_used=cnro, chord_num=chord_num)
                chord.chord_name = MusicUtils.get_chord_name(chord, fixed_scale)
                chord.timing = TimingUtils.get_timing(cc)
                bar.chord_nums.append(chord.chord_num)
                composition.chords_hash[chord_num] = chord
                chord_num += 1
                previous_pitches = pitches
        return composition
