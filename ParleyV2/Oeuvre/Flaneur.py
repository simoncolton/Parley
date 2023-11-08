import copy
import random
import time
from ParleyV2.Specifications.ConstrainedSpecification import *
from ParleyV2.Specifications.SoundFontClasses import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Logistics.Constants import *
import warnings
import os


# PARAMETERS FOR FLANEURS (2 EPISODE CYCLE)

class Flaneur:

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def get_composition_gen_spec(self):

        random_seed = random.randint(0, 100000)
        #random_seed = 55649

        print("Random seed:", random_seed)

        epA_chord_allowances = "min;dim"
        epB_chord_allowances = "maj;aug"

        soundfont_filepath = SFYamahaPiano.soundfont_filepath

        """
        soundfont_filepath = SFRhodesEP.soundfont_filepath
        soundfont_filepath = SFKBHChoir.soundfont_filepath
        melody_instrument_num = SFKBHChoir.voice_Vocal_Aaah
        harmonisation_instrument_num = SFKBHChoir.voice_Irina_Brochin
        chords_instrument_num = SFKBHChoir.voice_Mix__Choir
        bass_instrument_num = SFKBHChoir.voice_Oooh_to_Aaah_Vel

        soundfont_filepath = SFStrings4U.soundfont_filepath
        melody_instrument_num = SFStrings4U.strings_Violin
        harmonisation_instrument_num = SFStrings4U.strings_Violin
        chords_instrument_num = SFStrings4U.strings_Full_Strings_Vel
        bass_instrument_num = SFStrings4U.strings_Cello

        soundfont_filepath = SFSonatina.soundfont_filepath
        melody_instrument_num = SFSonatina.strings_Violin_Solo
        harmonisation_instrument_num = SFSonatina.strings_Second_Violins_Sustain
        chords_instrument_num = SFSonatina.strings_Cello_Section_Sustai
        bass_instrument_num = SFSonatina.strings_Basses_Sustain



        #epA_instrument_num = SFRhodesEP.epiano_FLT_Bright
#        soundfont_filepath = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/soundfonts/DoreMarkYamahaS6-v1.6.sf2"
        """
        instrument_num = SFYamahaPiano.piano_YamahaS6
        melody_instrument_num = instrument_num
        harmonisation_instrument_num = instrument_num
        chords_instrument_num = instrument_num
        bass_instrument_num = instrument_num

        melody_instrument_param = Parameter("instrument_num", melody_instrument_num)
        harmonisation_instrument_param = Parameter("instrument_num", harmonisation_instrument_num)
        chords_instrument_param = Parameter("instrument_num", chords_instrument_num)
        bass_instrument_param = Parameter("instrument_num", bass_instrument_num)

        random.seed(random_seed)

        scaleA = MusicUtils.get_random_scale(epA_chord_allowances)
        while len(MusicUtils.get_chords_for_scale(scaleA, epB_chord_allowances, 70)) == 0:
            scaleA = MusicUtils.get_random_scale(epA_chord_allowances)

        scaleB = scaleA

        home_chordA = random.choice(MusicUtils.get_chords_for_scale(scaleA, epA_chord_allowances, 70))
        home_chordB = random.choice(MusicUtils.get_chords_for_scale(scaleB, epB_chord_allowances, 70))

        st = ""
        for s in scaleA.scale_type.split(" "):
            st += s.capitalize() + " "
        scale_subtitle = "In the " + st + "Scale of " + scaleA.tonic_letter.capitalize()
        print("Flaneur", scale_subtitle)

        discordancy_spec_params = [
            Parameter("max_clang_severity", 0),
            Parameter("max_clang_duration_ms", 0),
            Parameter("max_grind_severity", 0),
            Parameter("max_grind_duration_ms", 0)
        ]


        discordancy_spec_params = [
            Parameter("max_clang_severity", None),
            Parameter("max_clang_duration_ms", None),
            Parameter("max_grind_severity", None),
            Parameter("max_grind_duration_ms", None)
        ]

        discordancy_spec = ParameterisedSpecification(discordancy_spec_params)

        reverb_param = Parameter("reverb")
#        reverb_param.add_constrained_value(4, "efi=A,tn=0")
        reverb_param.add_constrained_value(0.2, "efi=A")
        reverb_param.add_constrained_value(0.6, "efi=B")

        sustain_pedal_bars_param = Parameter("sustain_pedal_bars")
        sustain_pedal_bars_param.add_constrained_value(1, "efi=A")
        sustain_pedal_bars_param.add_constrained_value(2, "efi=B")

        performance_params = [
            reverb_param,
            sustain_pedal_bars_param,
            Parameter("sustain_pedal_reset", "episode")
        ]

        performance_spec = ParameterisedSpecification(performance_params)

        global_variables.add_variable("accompaniment_start_episode_volume", random.randint(40, 50))
        global_variables.add_variable("accompaniment_end_episode_volume", random.randint(60, 80))
        global_variables.add_variable("epA_scale", scaleA)
        global_variables.add_variable("epB_scale", scaleB)

        fixed_scale_param = Parameter("fixed_scale")
        fixed_scale_param.add_constrained_value("epA_scale", "efi=A")
        fixed_scale_param.add_constrained_value("epB_scale", "efi=B")

        output_stem = f"{self.output_dir}/flaneur_{random_seed}"
        num_minutes = 2

        bar_start_duration_ms_param = Parameter("bar_start_duration_ms")
        bar_start_duration_ms_param.add_constrained_value(3000, "efi=A")
        bar_start_duration_ms_param.add_constrained_value(2500, "efi=B")

        bar_end_duration_ms_param = Parameter("bar_end_duration_ms")
        bar_end_duration_ms_param.add_constrained_value(2500, "efi=A")
        bar_end_duration_ms_param.add_constrained_value(3000, "efi=B")

        form_params = [
            Parameter("applier_class_name", "BasicFormDesigner"),
            Parameter("output_composition_id", "basic_form"),
            Parameter("composition_duration_ms", 60000 * num_minutes),
            Parameter("num_cycles", 1),
            Parameter("cycle_form", "ABABA"),
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
        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/2:1/2", "2/2:1/2"], None, 25)
        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], None, 25)
        chord_sequence_change_rhythm_param.add_constrained_random_value(["1/4:3/4", "4/4:1/4"], None, 25)

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
        note_colours_hash = {
            "harmony=added": "grey",
            "likelihood=unchanged": "blue",
            "likelihood=more likely": "green",
            "likelihood=less likely": "purple",
            "discordance=clang": "red",
            "discordance=grind": "red",
            "discordance=clang and grind": "red"
        }

        margin_colours_hash = {
            "discordance": "yellow",
            "likelihood": "blue",
            "tuplet": "orange"
        }

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
            Parameter("note_colours_hash", note_colours_hash),
            Parameter("margin_colours_hash", margin_colours_hash),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("musescore_cli", "/Applications/MuseScore\ 3.app/Contents/MacOS/mscore"),
            Parameter("resources_dir", "/Users/Simon/Dropbox/Code/Parley/ParleyV2/Resources"),
            Parameter("ffmpeg_cli", "ffmpeg"),
            Parameter("codec", "libx264"),
            Parameter("audio_formats", ["WAV", "MP3"]),
            Parameter("video_fade_in", False),
            Parameter("dpi", 100),
            Parameter("fps", 3),
            Parameter("end_rest_ms", 3000),
            Parameter("performance_spec", performance_spec)
        ]

        lead_sheet_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [3]), ("bass", [0, 1, 2])]}]

        lead_sheet_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"output_stem": output_stem + "_lead_sheet",
                                                               "score_parts": lead_sheet_score_parts})

        bass_rhythm_param = Parameter("rhythm")
        bass_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:2/4"], "cbn=-1", priority=1)
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=A,cbc=1/4|efi=A,cbc=2/4|efi=A,cbc=3/4")
        bass_rhythm_param.add_constrained_value(["1/4:1/4"], "efi=A,cbc=4/4")
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=B,br=1/2")
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=B,br=2/2")

        accompaniment_volume_param = Parameter("volume")
        accompaniment_volume_param.set_interpolation_counter("ebp")
        accompaniment_volume_param.add_constrained_interpolation_value("accompaniment_start_episode_volume", 0, "efi=A")
        accompaniment_volume_param.add_constrained_interpolation_value("accompaniment_end_episode_volume", 1, "efi=A")
        accompaniment_volume_param.add_constrained_interpolation_value("accompaniment_end_episode_volume", 0, "efi=B")
        accompaniment_volume_param.add_constrained_interpolation_value("accompaniment_start_episode_volume", 1, "efi=B")

        bass_backbone_note_sequence_params = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("input_composition_id", "chord_sequence"),
            Parameter("output_composition_id", "bass_backbone"),
            Parameter("voice_id", "bass"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 0),
            Parameter("channel_num", 0),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", 43),
            bass_instrument_param,
            bass_rhythm_param,
            accompaniment_volume_param
        ]

        bass_backbone_note_sequence_spec = ParameterisedSpecification(bass_backbone_note_sequence_params)

        chord_rhythm_param = Parameter("rhythm")
        chord_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
        chord_rhythm_param.add_constrained_value(["2/4:1/4"], "cbn=-1", priority=1)
        chord_rhythm_param.add_constrained_value(["2/4:1/4", "4/4:1/4"], "efi=A,cbc=1/4|efi=A,cbc=2/4|efi=A,cbc=3/4")
        chord_rhythm_param.add_constrained_value(["2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=A,cbc=4/4")
        chord_rhythm_param.add_constrained_value(["2/4:1/4", "4/4:1/4"], "efi=B,br=1/2")
        chord_rhythm_param.add_constrained_value([], "efi=B,br=2/2")

        chord_tonic_backbone_note_sequence_params = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("output_composition_id", "tonic_backbone"),
            Parameter("voice_id", "tonic_chord"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 1),
            Parameter("channel_num", 1),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", 55),
            chords_instrument_param,
            chord_rhythm_param,
            accompaniment_volume_param
        ]

        chord_tonic_backbone_note_sequence_spec = ParameterisedSpecification(chord_tonic_backbone_note_sequence_params)
        third_changes = {"output_composition_id": "third_backbone",
                         "track_num": 2, "channel_num": 2, "backbone_note": 2}
        chord_third_backbone_note_sequence_spec = ParameterisedSpecification(chord_tonic_backbone_note_sequence_params, third_changes)
        fifth_changes = {"output_composition_id": "fifth_backbone",
                         "track_num": 3, "channel_num": 3, "backbone_note": 3}
        chord_fifth_backbone_note_sequence_spec = ParameterisedSpecification(chord_tonic_backbone_note_sequence_params, fifth_changes)

        vl_melody_volume_param = Parameter("volume")
        vl_melody_volume_param.set_interpolation_counter("ebp")
        vl_melody_volume_param.add_constrained_interpolation_value(60, 0, "efi=A")
        vl_melody_volume_param.add_constrained_interpolation_value(100, 1, "efi=A")
        vl_melody_volume_param.add_constrained_interpolation_value(100, 0, "efi=B")
        vl_melody_volume_param.add_constrained_interpolation_value(60, 1, "efi=B")

        vl_melody_backbone_length_param = Parameter("backbone_length")
        vl_melody_backbone_length_param.add_constrained_value(1, "cbn=0|cbn=-1", priority=2)
        vl_melody_backbone_length_param.add_constrained_random_range_value(3, 4, "efi=A")
        vl_melody_backbone_length_param.add_constrained_random_range_value(5, 7, "efi=B")
        vl_melody_backbone_length_param.set_interpolation_counter("ebp")
        vl_melody_backbone_length_param.add_constrained_interpolation_value(4, 0, "en=-1", priority=1)
        vl_melody_backbone_length_param.add_constrained_interpolation_value(1, 1, "en=-1", priority=1)

        vl_melody_backbone_choice_param = Parameter("backbone_choice")
        vl_melody_backbone_choice_param.add_constrained_random_value("least_distance", None, 30)
        vl_melody_backbone_choice_param.add_constrained_random_value("random", None, 70)

        vl_melody_passing_notes_param = Parameter("passing_notes")
        vl_melody_passing_notes_param.add_constrained_random_value("all", "efi=A", 100)
        vl_melody_passing_notes_param.add_constrained_random_value("mid", "efi=A", 30)
        vl_melody_passing_notes_param.add_constrained_random_value("none", "efi=A", 10)
        vl_melody_passing_notes_param.add_constrained_random_value("mid", "efi=B", 50)
        vl_melody_passing_notes_param.add_constrained_random_value("none", "efi=B", 50)

        vl_melody_in_bar_repetition_param = Parameter("in_bar_repetition")
        vl_melody_in_bar_repetition_param.add_constrained_random_value(True, None, 0)
        vl_melody_in_bar_repetition_param.add_constrained_random_value(False, None, 100)

        vl_melody_over_bar_repetition_param = Parameter("over_bar_repetition")
        vl_melody_over_bar_repetition_param.add_constrained_random_value(True, None, 80)
        vl_melody_over_bar_repetition_param.add_constrained_random_value(False, None, 20)

        vl_melody_note_sequence_params = [
            Parameter("applier_class_name", "BackboneMelodyGenerator"),
            Parameter("output_composition_id", "backbone_melody"),
            Parameter("voice_id", "melody"),
            Parameter("instrument_num", 0),
            Parameter("track_num", 4),
            Parameter("channel_num", 4),
            Parameter("leads_dynamics", True),
            Parameter("octave_offset", 0),
            Parameter("note_length", 1),
            melody_instrument_param,
            vl_melody_volume_param,
            vl_melody_backbone_length_param,
            vl_melody_backbone_choice_param,
            vl_melody_in_bar_repetition_param,
            vl_melody_over_bar_repetition_param
        ]

        vl_melody_spec = ParameterisedSpecification(vl_melody_note_sequence_params)

        melody_passing_notes_params = [
            Parameter("applier_class_name", "PassingNotesGenerator"),
            Parameter("output_composition_id", "vl_melody"),
            Parameter("track_num", 4),
            Parameter("leads_dynamics", True),
            Parameter("min_duration64ths", 4),
            fixed_scale_param,
            vl_melody_volume_param,
            vl_melody_passing_notes_param
        ]

        melody_passing_notes_spec = ParameterisedSpecification(melody_passing_notes_params)

        melody_tuplets_params = [
            Parameter("applier_class_name", "TupletEditor"),
            Parameter("output_composition_id", "melody_tuples"),
            Parameter("track_num", 4),
            #Parameter("tuplets_sought", "6:32;3:16")
            Parameter("tuplets_sought", "3:16")
        ]

        melody_tuplets_spec = ParameterisedSpecification(melody_tuplets_params)

        bass_tuplets_params = [
            Parameter("applier_class_name", "TupletEditor"),
            Parameter("output_composition_id", "bass_tuples"),
            Parameter("track_num", 0),
            Parameter("tuplets_sought", "6:32;3:16")
        ]

        bass_tuplets_spec = ParameterisedSpecification(bass_tuplets_params)


        pre_edit_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                               "track_details": [("treble", [4]), ("bass", [0, 1, 2, 3])]}]

        pre_edit_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                            {"output_stem": output_stem + "_pre_edit",
                                                             "show_chord_name": False,
                                                             "score_parts": pre_edit_score_parts})

        vl_melody_interestingness_edit_params = [
            Parameter("applier_class_name", "InterestingnessEditor"),
            Parameter("output_composition_id", "vl_melody_ie"),
            Parameter("track_num", 4),
            Parameter("bar_types_to_change", "all"),
            Parameter("note_types_to_change", "all"),
            Parameter("pitch_change_choice", "closest_to_neighbours"),
            Parameter("focal_pitch", None),
            Parameter("chord_notes_fixed", True),
            Parameter("seed_length", 50),
            Parameter("discordancy_avoid", discordancy_spec),
            Parameter("passover_notes", None),
            Parameter("application_probability_pc", 50),
            fixed_scale_param,
            vl_melody_in_bar_repetition_param,
            vl_melody_over_bar_repetition_param
        ]

        vl_melody_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params)

        bass_passover_notes_param = Parameter("passover_notes")
        bass_passover_notes_param.add_constrained_value(True, "cbn=-1")

        bass_interest_changes = {"output_composition_id": "bass_ie",
                                 "track_num": 0, "focal_pitch": 43, "repetition": "disallow"}
        tonic_interest_changes = {"output_composition_id": "tonic_ie",
                                  "track_num": 1, "focal_pitch": 55, "repetition": "disallow"}
        third_interest_changes = {"output_composition_id": "third_ie",
                                  "track_num": 2, "focal_pitch": 55, "repetition": "disallow"}
        fifth_interest_changes = {"output_composition_id": "fifth_ie",
                                  "track_num": 3, "focal_pitch": 55, "repetition": "disallow"}

        bass_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params, bass_interest_changes)
        bass_interestingness_edit_spec.parameters["passover_notes"] = bass_passover_notes_param

        bass_passing_notes_params = [
            Parameter("applier_class_name", "PassingNotesGenerator"),
            Parameter("output_composition_id", "bass_passing"),
            Parameter("track_num", 0),
            Parameter("leads_dynamics", False),
            Parameter("passing_notes", "all"),
            Parameter("min_duration64ths", 4),
            fixed_scale_param,
            accompaniment_volume_param
        ]

        bass_passing_notes_spec = ParameterisedSpecification(bass_passing_notes_params)

        chord_tonic_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params, tonic_interest_changes)
        chord_third_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params, third_interest_changes)
        chord_fifth_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params, fifth_interest_changes)

        repeat_note_removal_params = [
            Parameter("applier_class_name", "DuplicateNoteRemovalEditor"),
            Parameter("output_composition_id", "post_edited"),
            Parameter("track_removal_order", [0, 1, 2, 3, 4])
        ]
        note_removal_editor = ParameterisedSpecification(repeat_note_removal_params)

        repetition_param = Parameter("repetition")
        repetition_param.add_constrained_random_value("leave", None, 0)
        repetition_param.add_constrained_random_value("tie", None, 100)

        repetition_editor_params = [
            Parameter("applier_class_name", "RepeatedPitchEditor"),
            Parameter("output_composition_id", "repetition_handled"),
            Parameter("track_num", 4),
            repetition_param
        ]

        melody_repetition_editor_spec = ParameterisedSpecification(repetition_editor_params)

        post_edit_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                 "track_details": [("treble", [4]), ("bass", [0, 1, 2, 3])]}]

        post_edit_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                             {"output_stem": output_stem + "_post_edit",
                                                              "show_chord_name": False,
                                                              "score_parts": post_edit_score_parts})

        harmonisation_edit_params = [
            Parameter("applier_class_name", "HarmonisationEditor"),
            Parameter("output_composition_id", "harmonised"),
            Parameter("voice_id", "melody harmonisation"),
            Parameter("new_channel_num", 5),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 5),
            Parameter("channel_num", 5),
            Parameter("track_num_to_harmonise", 4),
            Parameter("note_types", "backbone"),
            #Parameter("intervals_allowed", [9, 7, 4, 3, -3, -5, -8]),
            #Parameter("intervals_allowed", [9]),
            #Parameter("intervals_allowed", [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
            Parameter("intervals_allowed", [-4, -3, -2, 2, 3, 4, 12 ]),
            Parameter("randomise_intervals", True),
            Parameter("pitch_range_low", 60),
            Parameter("pitch_range_high", 100),
            Parameter("map_to_scale", False),
            Parameter("keep_ties", True),
            Parameter("discordancy_avoid", discordancy_spec),
            harmonisation_instrument_param,
            fixed_scale_param,
            vl_melody_in_bar_repetition_param,
            vl_melody_over_bar_repetition_param
        ]

        harmonisation_edit_spec = ParameterisedSpecification(harmonisation_edit_params)

        interestingness_edit_analyser_params = [
            Parameter("applier_class_name", "InterestingnessEditAnalyser"),
            Parameter("output_composition_id", "interest_analysed"),
            Parameter("track_num", 4),
            Parameter("min_num_notes", 4),
            Parameter("num_highlight_bars", 10)
        ]

        interestingness_edit_analyser_spec = ParameterisedSpecification(interestingness_edit_analyser_params)

        discordancy_analyser_params = [
            Parameter("applier_class_name", "DiscordancyAnalyser"),
            Parameter("output_composition_id", "discordancy_analysed")
        ]

        discordancy_analyser_spec = ParameterisedSpecification(discordancy_analyser_params)

        tuplet_analyser_params = [
            Parameter("applier_class_name", "TupletAnalyser"),
            Parameter("output_composition_id", "tuplets_analysed")
        ]

        tuplet_analyser_spec = ParameterisedSpecification(tuplet_analyser_params)

        harmonised_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [4, 5]), ("bass", [0, 1, 2, 3])]}]

        harmonised_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"input_composition_id": "discordancy_analysed",
                                                               "output_stem": output_stem + "_harmonised",
                                                               "show_chord_name": False,
                                                               "export_video": True,
                                                               "score_parts": harmonised_score_parts})

        awkward_rhythm_edit_action_param = Parameter("edit_action")
        awkward_rhythm_edit_action_param.add_constrained_value("make_first_rest", "tn=5")
        awkward_rhythm_edit_action_param.add_constrained_value("make_second_rest", "tn=5")

        awkward_rhythm_params = [
            Parameter("applier_class_name", "AwkwardRhythmEditor"),
            Parameter("output_composition_id", "awkward_edited"),
            awkward_rhythm_edit_action_param
        ]
        awkward_rhythm_editor_spec = ParameterisedSpecification(awkward_rhythm_params)

        pause_length_param = Parameter("pause_length_64ths")
        pause_length_param.add_constrained_value(64, "tn=4,tnn=-1", 1)
        pause_length_param.add_constrained_value(8, "tn=4,enn=-1,nl>=16,nl<32", 0)
        pause_editor_params = [
            Parameter("applier_class_name", "PauseEditor"),
            Parameter("output_composition_id", "pause_edited"),
            pause_length_param
        ]
        pause_editor_spec = ParameterisedSpecification(pause_editor_params)

        target_tag_param = Parameter("target_tag")
        target_tag_param.add_constrained_value("mtg_jamendo_moodtheme__happy", "efi=A")
        target_tag_param.add_constrained_value("mtg_jamendo_moodtheme__sad", "efi=B")
        scale_param = Parameter("fixed_scale")
        scale_param.add_constrained_value(None, "efi=A")
        scale_param.add_constrained_value(None, "efi=B")
        listening_edit_params = [
            Parameter("applier_class_name", "MTGListeningModelEditor"),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("performance_spec", performance_spec),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("ffmpeg_cli", "ffmpeg"),
            Parameter("temp_dir", "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Temp"),
            Parameter("num_bars_per_episode", 2),
            Parameter("num_hill_climb_trials_per_bar", 2),
            Parameter("track_num", 4),
            target_tag_param,
            fixed_scale_param
        ]
        listening_edit_spec = ParameterisedSpecification(listening_edit_params)

        specs_to_apply_param = []
        specs_to_apply_param.append(form_spec)
        specs_to_apply_param.append(chord_sequence_spec)
        specs_to_apply_param.append(lead_sheet_generator_spec)
#        specs_to_apply_param.append(lead_sheet_exporter_spec)
        specs_to_apply_param.append(bass_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_tonic_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_third_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_fifth_backbone_note_sequence_spec)
        specs_to_apply_param.append(vl_melody_spec)
        specs_to_apply_param.append(melody_passing_notes_spec)
        #specs_to_apply_param.append(pre_edit_exporter_spec)
        """
        specs_to_apply_param.append(vl_melody_interestingness_edit_spec)
        specs_to_apply_param.append(bass_interestingness_edit_spec)
        specs_to_apply_param.append(chord_tonic_interestingness_edit_spec)
        specs_to_apply_param.append(chord_third_interestingness_edit_spec)
        specs_to_apply_param.append(chord_fifth_interestingness_edit_spec)
        """
        specs_to_apply_param.append(bass_passing_notes_spec)
        specs_to_apply_param.append(note_removal_editor)
        specs_to_apply_param.append(melody_repetition_editor_spec)
        specs_to_apply_param.append(melody_tuplets_spec)
        specs_to_apply_param.append(bass_tuplets_spec)
        #specs_to_apply_param.append(post_edit_exporter_spec)
        specs_to_apply_param.append(harmonisation_edit_spec)
        specs_to_apply_param.append(interestingness_edit_analyser_spec)
        specs_to_apply_param.append(discordancy_analyser_spec)
        specs_to_apply_param.append(tuplet_analyser_spec)
        specs_to_apply_param.append(awkward_rhythm_editor_spec)
        specs_to_apply_param.append(pause_editor_spec)
        specs_to_apply_param.append(harmonised_exporter_spec)

        composition_params = [
            Parameter("applier_class_name", "CompositionGenerator"),
            Parameter("output_composition_id", "final_composition"),
            Parameter("title", "Flaneur"),
            Parameter("random_seed", random_seed),
            Parameter("subtitle", scale_subtitle),
            Parameter("random_seed", random_seed),
            Parameter("specs_to_apply", specs_to_apply_param)
        ]

        composition_generation_spec = ParameterisedSpecification(composition_params)
        return composition_generation_spec

def make_flaneur(output_dir):
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    start_time = time.time()
    nf = Flaneur(output_dir)
    composition_spec = nf.get_composition_gen_spec()
    composition = composition_spec.apply()
    stop_time = time.time()
    print("Duration: ", stop_time - start_time)

make_flaneur("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Outputs/Flaneurs")
