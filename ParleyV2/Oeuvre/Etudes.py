# https://flypaper.soundfly.com/write/what-are-etudes-and-why-do-composers-write-them/

import copy
import random
import time
from ParleyV2.Specifications.ConstrainedSpecification import *
from ParleyV2.Specifications.SoundFontClasses import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Analysers.DiscordancyAnalyser import *
from ParleyV2.Logistics.Constants import *
import warnings
from ParleyV2.Utils.PatternUtils import *


class Etude:

    def get_composition_gen_spec(self):

        random_seed = random.randint(0, 100000)
        #random_seed = 171717

        print("Random seed:", random_seed)

        epA_chord_allowances = "min" #"min;dim"
        epB_chord_allowances = "maj" #"maj;aug"

        soundfont_filepath = SFYamahaPiano.soundfont_filepath
        epA_instrument_num = SFYamahaPiano.piano_YamahaS6
        epB_instrument_num = SFYamahaPiano.piano_YamahaS6

        instrument_param = Parameter("instrument_num")
        instrument_param.add_constrained_value(epA_instrument_num, "efi=A")
        instrument_param.add_constrained_value(epB_instrument_num, "efi=B")

        random.seed(random_seed)

        scaleA = MusicUtils.get_random_scale(epA_chord_allowances)
        scaleB = MusicUtils.get_random_scale(epB_chord_allowances)
        while len(MusicUtils.get_chords_for_scale(scaleA, epA_chord_allowances, 70)) == 0:
            scaleA = MusicUtils.get_random_scale(epA_chord_allowances)
        while len(MusicUtils.get_chords_for_scale(scaleB, epB_chord_allowances, 70)) == 0:
            scaleB = MusicUtils.get_random_scale(epB_chord_allowances)

        # Fix to C major scale
        #scaleA = MusicUtils.get_named_scale("c_major")

        # Fix scales for both episodes to be the same
        #scaleB = scaleA

        home_chordA = random.choice(MusicUtils.get_chords_for_scale(scaleA, epA_chord_allowances, 70))
        home_chordB = random.choice(MusicUtils.get_chords_for_scale(scaleB, epB_chord_allowances, 70))

        st = ""
        for s in scaleA.scale_type.split(" "):
            st += s.capitalize() + " "
        scale_subtitle = "In the " + st + "scale of " + scaleA.tonic_letter.capitalize()
        st = ""
        if scaleA != scaleB:
            for s in scaleB.scale_type.split(" "):
                st += s.capitalize() + " "
            scale_subtitle += "\nand the " + st + "scale of " + scaleB.tonic_letter.capitalize()
        print("Etude", scale_subtitle)

        discordancy_spec_params = [
            Parameter("max_clang_severity", 0),
            Parameter("max_clang_duration_ms", 0),
            Parameter("max_grind_severity", 0),
            Parameter("max_grind_duration_ms", 0)
        ]

        discordancy_spec = ParameterisedSpecification(discordancy_spec_params)

        sustain_factor_param = Parameter("sustain_factor")
        sustain_factor_param.add_constrained_value(None, "efi=A,tn=0") # SGC 4
        sustain_factor_param.add_constrained_value(None, "efi=A") # SGC 1.4

        sustain_pedal_beats_param = Parameter("sustain_pedal_beats")
        sustain_pedal_beats_param.add_constrained_value(None, "efi=A")
        sustain_pedal_beats_param.add_constrained_value(None, "efi=B") # SGC 4

        performance_params = [
            sustain_factor_param,
            sustain_pedal_beats_param,
            Parameter("end_sustain_pedal_beats", None) # SGC 4
        ]

        performance_spec = ParameterisedSpecification(performance_params)

        rh_pattern_form = PatternUtils.get_form_pattern(random.randint(2, 3))
        lh_pattern_form = PatternUtils.get_form_pattern(1)
        print("RH Pattern form:", rh_pattern_form)
        print("LH Pattern form:", lh_pattern_form)

        global_variables.add_variable("lh_pattern_form", lh_pattern_form)
        global_variables.add_variable("rh_pattern_form", rh_pattern_form)
        global_variables.add_variable("lh_start_episode_volume", random.randint(40, 50))
        global_variables.add_variable("lh_end_episode_volume", random.randint(80, 90))
        global_variables.add_variable("rh_start_episode_volume", random.randint(50, 60))
        global_variables.add_variable("rh_end_episode_volume", random.randint(90, 100))
        global_variables.add_variable("epA_scale", scaleA)
        global_variables.add_variable("epB_scale", scaleB)

        fixed_scale_param = Parameter("fixed_scale")
        fixed_scale_param.add_constrained_value("epA_scale", "efi=A")
        fixed_scale_param.add_constrained_value("epB_scale", "efi=B")

        output_stem = f"./Outputs/Etudes/etude_{random_seed}"
        num_minutes = 11

        bar_start_duration_ms_param = Parameter("bar_start_duration_ms")
        bar_start_duration_ms_param.add_constrained_value(2000, "efi=A")
        bar_start_duration_ms_param.add_constrained_value(2000, "efi=B") # SGC 2200

        bar_end_duration_ms_param = Parameter("bar_end_duration_ms")
        bar_end_duration_ms_param.add_constrained_value(2000, "efi=A")
        bar_end_duration_ms_param.add_constrained_value(2000, "efi=B") # SGC 2200

        form_params = [
            Parameter("applier_class_name", "BasicFormDesigner"),
            Parameter("output_composition_id", "basic_form"),
            Parameter("composition_duration_ms", 60000 * num_minutes),
            Parameter("num_cycles", 1),
            Parameter("cycle_form", "ABAB"),
            Parameter("beats_per_bar", 4),
            bar_start_duration_ms_param,
            bar_end_duration_ms_param
        ]

        form_spec = ParameterisedSpecification(form_params)

        chord_sequence_cnro_length_param = Parameter("cnro_length")
        chord_sequence_cnro_length_param.add_constrained_random_range_value(5, 10, None)

        chord_sequence_override_chord_param = Parameter("override_chord")
        chord_sequence_override_chord_param.add_constrained_value(home_chordA, "efi=A,ebn=1")
        chord_sequence_override_chord_param.add_constrained_value(home_chordA, "efi=A,ebn=-1")
        chord_sequence_override_chord_param.add_constrained_value(home_chordA, "efi=A,ebn=-2")
        chord_sequence_override_chord_param.add_constrained_value(home_chordA, "efi=A,ebn=-3")
        chord_sequence_override_chord_param.add_constrained_value(home_chordB, "efi=B,ebn=1")
        chord_sequence_override_chord_param.add_constrained_value(home_chordB, "efi=B,ebn=-1")

        chord_sequence_majmin_allowance_param = Parameter("chord_type_allowance")
        chord_sequence_majmin_allowance_param.add_constrained_value(epA_chord_allowances, "efi=A")
        chord_sequence_majmin_allowance_param.add_constrained_value(epB_chord_allowances, "efi=B")

        chord_sequence_change_rhythm_param = Parameter("chord_change_rhythm")
        chord_sequence_change_rhythm_param.add_constrained_value(["1/1:1/1"], "ebn=-1")
        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/1:1/1"], None, 25)
#        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/2:1/2", "2/2:1/2"], None, 50)
#        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], None, 100)
#        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/4:3/4", "4/4:1/4"], None, 25)

        chord_sequence_max_repetitions_param = Parameter("max_repetitions")
        chord_sequence_max_repetitions_param.add_constrained_value(5, "efi=A")
        chord_sequence_max_repetitions_param.add_constrained_value(1, "efi=B")

        chord_sequence_params = [
            Parameter("applier_class_name", "NRTChordSequenceDesigner"),
            Parameter("output_composition_id", "chord_sequence"),
            Parameter("focal_pitch", 70),
            Parameter("start_nro", None),
            fixed_scale_param,
            chord_sequence_cnro_length_param,
            chord_sequence_override_chord_param,
            chord_sequence_majmin_allowance_param,
            chord_sequence_change_rhythm_param,
            chord_sequence_max_repetitions_param
        ]

        chord_sequence_spec = ParameterisedSpecification(chord_sequence_params)

        lead_sheet_generator_params = [
            Parameter("applier_class_name", "LeadSheetGenerator"),
            Parameter("output_composition_id", "lead_sheet")
        ]

        lead_sheet_generator_spec = ParameterisedSpecification(lead_sheet_generator_params)

        total_exporter_params = [
            Parameter("applier_class_name", "TotalExporter"),
            Parameter("output_composition_id", None),
            Parameter("export_score", True),
            Parameter("export_audio", True),
            Parameter("export_video", False),
            Parameter("export_data", True),
            Parameter("output_stem", None),
            Parameter("score_parts", None),
            Parameter("show_chord_name", True),
            Parameter("show_episode_duration", True),
            Parameter("show_colours", True),
            Parameter("musescore_command_line", "/Applications/MuseScore\ 3.app/Contents/MacOS/mscore"),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("audio_formats", ["WAV", "MP3"]),
            Parameter("dpi", 100),
            Parameter("fps", 5),
            Parameter("end_rest_ms", 0), # SGC 3000
            Parameter("performance_spec", performance_spec),
            Parameter("export_bars_wav_zip", False)
        ]

        lead_sheet_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [3]), ("bass", [0, 1, 2])]}]

        lead_sheet_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"output_stem": output_stem + "_lead_sheet",
                                                               "score_parts": lead_sheet_score_parts})

        rh_volume_param = Parameter("volume")
        rh_volume_param.set_interpolation_counter("ebp")
        rh_volume_param.add_constrained_interpolation_value("rh_start_episode_volume", 0, "efi=A")
        rh_volume_param.add_constrained_interpolation_value("rh_end_episode_volume", 1, "efi=A")
        rh_volume_param.add_constrained_interpolation_value("rh_end_episode_volume", 0, "efi=B")
        rh_volume_param.add_constrained_interpolation_value("rh_start_episode_volume", 1, "efi=B")

        melody1_pattern_note_sequence_params = [
            Parameter("applier_class_name", "PatternNoteSequenceGenerator"),
            Parameter("output_composition_id", "melody_pattern1"),
            Parameter("voice_id", "melody1"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 2),
            Parameter("channel_num", 2),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", 70),
            Parameter("num_notes_in_pattern", 8),
            Parameter("pattern_form", "rh_pattern_form"),
            Parameter("num_pattern_rests", 0), #random.randint(0, 1)),
            instrument_param,
            rh_volume_param
        ]

        melody1_pattern_note_sequence_spec = ParameterisedSpecification(melody1_pattern_note_sequence_params)

        melody2_pattern_note_sequence_params = [
            Parameter("applier_class_name", "PatternNoteSequenceGenerator"),
            Parameter("output_composition_id", "melody_pattern2"),
            Parameter("voice_id", "melody2"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 1),
            Parameter("channel_num", 1),
            Parameter("leads_dynamics", True),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", 70),
            Parameter("num_notes_in_pattern", 8),
            Parameter("pattern_form", "lh_pattern_form"),
            Parameter("num_pattern_rests", 0), # random.randint(0, 3)),
            instrument_param,
            rh_volume_param
        ]

        melody2_pattern_note_sequence_spec = ParameterisedSpecification(melody2_pattern_note_sequence_params)

        lh_volume_param = Parameter("volume")
        lh_volume_param.set_interpolation_counter("ebp")
        lh_volume_param.add_constrained_interpolation_value("lh_start_episode_volume", 0, "efi=A")
        lh_volume_param.add_constrained_interpolation_value("lh_end_episode_volume", 1, "efi=A")
        lh_volume_param.add_constrained_interpolation_value("lh_end_episode_volume", 0, "efi=B")
        lh_volume_param.add_constrained_interpolation_value("lh_start_episode_volume", 1, "efi=B")

        bass_pattern_note_sequence_params = [
            Parameter("applier_class_name", "PatternNoteSequenceGenerator"),
            Parameter("output_composition_id", "bass_pattern"),
            Parameter("voice_id", "bass"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 0),
            Parameter("channel_num", 0),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", 46),
            Parameter("num_notes_in_pattern", 16),
            Parameter("pattern_form", "pattern_form"),
            Parameter("num_pattern_rests", 0), # random.randint(0, 1)),
            instrument_param,
            lh_volume_param
        ]

        bass_pattern_note_sequence_spec = ParameterisedSpecification(bass_pattern_note_sequence_params)

        repeat_note_removal_params = [
            Parameter("applier_class_name", "DuplicateNoteRemovalEditor"),
            Parameter("output_composition_id", "post_edited"),
            Parameter("track_removal_order", [0, 1, 2])
        ]
        note_removal_editor = ParameterisedSpecification(repeat_note_removal_params)

        discordancy_analyser_params = [
            Parameter("applier_class_name", "DiscordancyAnalyser"),
            Parameter("output_composition_id", "discordancy_analysed")
        ]

        harmonised_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [1, 2]), ("bass", [0])]}]

        harmonised_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"input_composition_id": "discordancy_analysed",
                                                               "output_stem": output_stem + "_harmonised",
                                                               "show_chord_name": False,
                                                               "export_video": True,
                                                               "export_bars_wav_zip": True,
                                                               "score_parts": harmonised_score_parts})

        discordancy_analyser_spec = ParameterisedSpecification(discordancy_analyser_params)
        discordancy_analyser = DiscordancyAnalyser(discordancy_analyser_spec)

        discordancy_editor_spec_params = [
            Parameter("applier_class_name", "DiscordancyEditor"),
            Parameter("max_clang_severity", 0),
            Parameter("max_clang_duration_ms", 0),
            Parameter("max_grind_severity", 0),
            Parameter("max_grind_duration_ms", 0),
            Parameter("fix_to", "nearest")
        ]
        discordancy_editor_spec = ParameterisedSpecification(discordancy_editor_spec_params)

        bar_var_extract_spec_params = [
            Parameter("applier_class_name", "BarVariationExtractor"),
            Parameter("bar_num", 0),
            Parameter("num_bars_per_change", 10),
            Parameter("audio_excerpt_duration_s", 2)
        ]
        bar_variations_extraction_spec = ParameterisedSpecification(bar_var_extract_spec_params)

        specs_to_apply_param = []
        specs_to_apply_param.append(form_spec)
        specs_to_apply_param.append(chord_sequence_spec)
        #specs_to_apply_param.append(lead_sheet_generator_spec)
        #specs_to_apply_param.append(lead_sheet_exporter_spec)
        specs_to_apply_param.append(melody1_pattern_note_sequence_spec)
        specs_to_apply_param.append(melody2_pattern_note_sequence_spec)
        specs_to_apply_param.append(bass_pattern_note_sequence_spec)
        specs_to_apply_param.append(note_removal_editor)
        specs_to_apply_param.append(discordancy_editor_spec)
        specs_to_apply_param.append(note_removal_editor)
        specs_to_apply_param.append(discordancy_analyser_spec)
        #specs_to_apply_param.append(harmonised_exporter_spec)
        specs_to_apply_param.append(bar_variations_extraction_spec)
        specs_to_apply_param.append(harmonised_exporter_spec)

        composition_params = [
            Parameter("applier_class_name", "OptimisedCompositionGenerator"),
            Parameter("output_composition_id", "final_composition"),
            Parameter("title", "Etude"),
            Parameter("random_seed", random_seed),
            Parameter("subtitle", scale_subtitle),
            Parameter("random_seed", random_seed),
            Parameter("specs_to_apply", specs_to_apply_param),
            Parameter("num_trials", 1),
            Parameter("termination_condition", 0),
            Parameter("analyser", discordancy_analyser),
            Parameter("composition_id_to_evaluate", "bass_pattern")
        ]

        composition_generation_spec = ParameterisedSpecification(composition_params)
        return composition_generation_spec

start_time = time.time()
nf = Etude()
composition_spec = nf.get_composition_gen_spec()
composition = composition_spec.apply()

stop_time = time.time()
print("Duration: ", stop_time - start_time)
