from ParleyV2.Specifications.ConstrainedSpecification import *
from ParleyV2.Specifications.SoundFontClasses import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Utils.AccompanimentUtils import *
import numpy as np

class ColabFlaneur:

    def __init__(self, output_dir):
        self.output_dir = output_dir

    def get_composition_gen_spec(self, pdict):

        random_seed = pdict["seed"]
        instrument_num = 0

        if pdict["instrument"] == "Yamaha S6 Piano":
          soundfont_filepath = "DoreMarkYamahaS6-v1.6.sf2"
          instrument_num = SFYamahaPiano.piano_YamahaS6
        elif pdict["instrument"] == "Rhodes EPiano":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_Rhodes_EP
        elif pdict["instrument"] == "DX7 EPiano":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_DX7_EP
        elif pdict["instrument"] == "FLT EPiano":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_FLT_Bright
        elif pdict["instrument"] == "Clavinet":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_Clavinet
        elif pdict["instrument"] == "Wurlitzer":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_Wurlitzer_4_Layer
        elif pdict["instrument"] == "Electric Grand":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_Electric_Grand
        elif pdict["instrument"] == "Harpsichord":
          soundfont_filepath = "RhodesEPsPlus-v2.3.sf2"
          instrument_num = SFRhodesEP.epiano_Harpsichord
        elif pdict["instrument"] == "Choir":
          soundfont_filepath = "KBH-Real-Choir-V2.5.sf2"

        melody_instrument_num = instrument_num
        harmonisation_instrument_num = instrument_num
        chords_instrument_num = instrument_num
        bass_instrument_num = instrument_num

        if pdict["instrument"] == "Choir":
          melody_instrument_num = SFKBHChoir.voice_Vocal_Aaah
          harmonisation_instrument_num = SFKBHChoir.voice_Irina_Brochin
          chords_instrument_num = SFKBHChoir.voice_Mix__Choir
          bass_instrument_num = SFKBHChoir.voice_Oooh_to_Aaah_Vel

        melody_instrument_param = Parameter("instrument_num", melody_instrument_num)
        harmonisation_instrument_param = Parameter("instrument_num", harmonisation_instrument_num)
        chords_instrument_param = Parameter("instrument_num", chords_instrument_num)
        bass_instrument_param = Parameter("instrument_num", bass_instrument_num)

        epA_chord_allowances = pdict["episode_a_chord_type"]
        epB_chord_allowances = pdict["episode_b_chord_type"]

        scale_tonic = pdict["scale_tonic"]
        scale_type = pdict["scale_type"]

        scaleA = MusicUtils.get_named_scale(f"{scale_tonic}_{scale_type}")

        scaleA_chords = MusicUtils.get_chords_for_scale(scaleA, epA_chord_allowances, 70)
        if scaleA_chords is None or len(scaleA_chords) == 0:
          scaleA_chords = MusicUtils.get_chords_for_scale(scaleA, "maj;min;aug;dim", 70)

        scaleB = scaleA

        scaleB_chords = MusicUtils.get_chords_for_scale(scaleA, epA_chord_allowances, 70)
        if scaleB_chords is None or len(scaleB_chords) == 0:
          scaleB_chords = MusicUtils.get_chords_for_scale(scaleB, "maj;min;aug;dim", 70)

        home_chordA = random.choice(scaleA_chords)
        home_chordB = random.choice(scaleB_chords)

        st = ""
        for s in scaleA.scale_type.split(" "):
            st += s.capitalize() + " "
        st = st[:-1]
        scale_subtitle = "In the " + st + " Scale of " + scaleA.tonic_letter.capitalize()
        title = pdict["title"]
        if st == "Major" or st == "Minor":
          scale_subtitle = f"In {scaleA.tonic_letter.capitalize()} {st}"

        t = f"{title} {scale_subtitle} (seed: {random_seed})"
        print("=" * len(t))
        print(t)
        print("=" * len(t))

        discordancy_spec_params = [
            Parameter("max_clang_severity", 0),
            Parameter("max_clang_duration_ms", 0),
            Parameter("max_grind_severity", 0),
            Parameter("max_grind_duration_ms", 0)
        ]
        if pdict["discordancy"] == "Allowed":
          discordancy_spec_params = [
              Parameter("max_clang_severity", None),
              Parameter("max_clang_duration_ms", None),
              Parameter("max_grind_severity", None),
              Parameter("max_grind_duration_ms", None)
          ]
        elif pdict["discordancy"] == "Mild":
          discordancy_spec_params = [
              Parameter("max_clang_severity", 0),
              Parameter("max_clang_duration_ms", 0),
              Parameter("max_grind_severity", 1),
              Parameter("max_grind_duration_ms", 1000)
          ]

        discordancy_spec = ParameterisedSpecification(discordancy_spec_params)

        reverb_param = Parameter("reverb")
        reverb_param.add_constrained_value(pdict["episode_a_reverb"], "efi=A")
        reverb_param.add_constrained_value(pdict["episode_b_reverb"], "efi=B")

        sustain_pedal_bars_param = Parameter("sustain_pedal_bars")
        sustain_pedal_bars_param.add_constrained_value(int(pdict["episode_a_sustain_bars"]), "efi=A")
        sustain_pedal_bars_param.add_constrained_value(int(pdict["episode_b_sustain_bars"]), "efi=B")

        performance_params = [
            reverb_param,
            sustain_pedal_bars_param,
            Parameter("sustain_pedal_reset", "episode")
        ]

        performance_spec = ParameterisedSpecification(performance_params)

        fixed_scale_param = Parameter("fixed_scale")
        fixed_scale_param.add_constrained_value("epA_scale", "efi=A")
        fixed_scale_param.add_constrained_value("epB_scale", "efi=B")

        output_stem = f"{self.output_dir}/flaneur_{random_seed}"

        bar_start_duration_ms_param = Parameter("bar_start_duration_ms")

        duration_range = pdict["aba_episodic_tempo_range"]
        epa_start_bar_duration = pdict["start_bar_duration"]

        if duration_range == "Even":
          epa_end_bar_duration = epa_start_bar_duration
        elif duration_range == "Mild slow-fast-slow":
          epa_end_bar_duration = max(1, epa_start_bar_duration - 0.3)
        elif duration_range == "Medium slow-fast-slow":
          epa_end_bar_duration = max(1, epa_start_bar_duration - 0.7)
        elif duration_range == "Strong slow-fast-slow":
          epa_end_bar_duration = max(1, epa_start_bar_duration - 1.0)
        elif duration_range == "Mild fast-slow-fast":
          epa_end_bar_duration = max(1, epa_start_bar_duration + 0.3)
        elif duration_range == "Medium fast-slow-fast":
          epa_end_bar_duration = max(1, epa_start_bar_duration + 0.7)
        elif duration_range == "Strong fast-slow-fast":
          epa_end_bar_duration = max(1, epa_start_bar_duration + 1.0)

        epb_start_bar_duration = epa_end_bar_duration
        epb_end_bar_duration = epa_start_bar_duration

        bar_start_duration_ms_param.add_constrained_value(epa_start_bar_duration * 1000, "efi=A")
        bar_start_duration_ms_param.add_constrained_value(epa_end_bar_duration * 1000, "efi=B")

        bar_end_duration_ms_param = Parameter("bar_end_duration_ms")
        bar_end_duration_ms_param.add_constrained_value(epb_start_bar_duration * 1000, "efi=A")
        bar_end_duration_ms_param.add_constrained_value(epb_end_bar_duration * 1000, "efi=B")

        epa_start_volume = pdict["start_volume"]
        vol_range = pdict["aba_episodic_volume_range"]

        if vol_range == "Even":
          epa_end_volume = epa_start_volume
        elif vol_range == "Mild soft-loud-soft":
          epa_end_volume = min(120, epa_start_volume + 20)
        elif vol_range == "Medium soft-loud-soft":
          epa_end_volume = min(120, epa_start_volume + 40)
        elif vol_range == "Strong soft-loud-soft":
          epa_end_volume = min(120, epa_start_volume + 60)
        elif vol_range == "Mild loud-soft-loud":
          epa_end_volume = max(0, epa_start_volume - 20)
        elif vol_range == "Medium loud-soft-loud":
          epa_end_volume = max(0, epa_start_volume - 40)
        elif vol_range == "Strong loud-soft-loud":
          epa_end_volume = max(0, epa_start_volume - 60)

        epb_start_volume = epa_end_volume
        epb_end_volume = epa_start_volume

        global_variables.add_variable("epa_accompaniment_start_episode_volume", np.clip(epa_start_volume + pdict["episode_a_lh_relative_volume"], 0, 128))
        global_variables.add_variable("epa_accompaniment_end_episode_volume", np.clip(epa_end_volume + pdict["episode_a_lh_relative_volume"], 0, 128))
        global_variables.add_variable("epb_accompaniment_start_episode_volume", np.clip(epb_start_volume + pdict["episode_b_lh_relative_volume"], 0, 128))
        global_variables.add_variable("epb_accompaniment_end_episode_volume", np.clip(epb_end_volume + pdict["episode_b_lh_relative_volume"], 0, 128))
        global_variables.add_variable("epA_scale", scaleA)
        global_variables.add_variable("epB_scale", scaleB)

        form_params = [
            Parameter("applier_class_name", "BasicFormDesigner"),
            Parameter("output_composition_id", "basic_form"),
            Parameter("composition_duration_ms", 1000 * pdict["duration"]),
            Parameter("num_cycles", 1),
            Parameter("cycle_form", pdict["episodic_form"]),
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
        chord_sequence_max_repetitions_param.add_constrained_value(pdict["episode_a_max_repetitions"], "efi=A")
        chord_sequence_max_repetitions_param.add_constrained_value(pdict["episode_b_max_repetitions"], "efi=B")

        focal_pitch = 65 if pdict["instrument"] == "Choir" else 70
        chord_sequence_params = [
            Parameter("applier_class_name", "NRTChordSequenceDesigner"),
            Parameter("output_composition_id", "chord_sequence"),
            Parameter("focal_pitch", focal_pitch),
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

        note_colours_hash = { }

        note_colours_hash["harmony=added"] = "grey"
        if pdict["likelihood_improvements"] == "Show":
          note_colours_hash["likelihood=unchanged"] = "blue"
          note_colours_hash["likelihood=more likely"] = "green"
          note_colours_hash["likelihood=less likely"] = "purple"
        if pdict["discordancies"] == "Show":
          note_colours_hash["discordance=clang"] = "red"
          note_colours_hash["discordance=grind"] = "red"
          note_colours_hash["discordance=clang and grind"] = "red"
        if pdict["listening_editing_amount"] > 0:
          note_colours_hash["listening edit improvement=improvement"] = "orange"

        margin_colours_hash = {
            "discordance": "red",
            "likelihood": "blue",
            "tuplet": "brown",
            "bar listening tag": "green",
            "listening edit improvement": "orange"
        }

        total_exporter_params = [
            Parameter("applier_class_name", "TotalExporter"),
            Parameter("output_composition_id", None),
            Parameter("composition_title", title),
            Parameter("export_score", True),
            Parameter("export_audio", True),
            Parameter("export_video", False),
            Parameter("export_data", True),
            Parameter("output_stem", None),
            Parameter("score_parts", None),
            Parameter("scale", scaleA),
            Parameter("show_chord_name", True),
            Parameter("show_episode_duration", True),
            Parameter("show_colours", True),
            Parameter("note_colours_hash", note_colours_hash),
            Parameter("margin_colours_hash", margin_colours_hash),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("musescore_cli", "mscore3"),
            Parameter("resources_dir", "."),
            Parameter("ffmpeg_cli", "ffmpeg"),
            Parameter("codec", "libx264"),
            Parameter("audio_formats", ["WAV", "MP3"]),
            Parameter("video_fade_in", False),
            Parameter("video_border_pixels", 4),
            Parameter("video_border_colour", (200, 200, 200, 200)),
            Parameter("dpi", 100),
            Parameter("fps", 3),
            Parameter("end_rest_ms", 3000),
            Parameter("performance_spec", performance_spec)
        ]

        lead_sheet_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [3]), ("bass", [0, 1, 2])]}]

        lead_sheet_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"output_stem": output_stem + "_lead_sheet",
                                                               "composition_title": title + " (Lead Sheet)",
                                                               "score_parts": lead_sheet_score_parts,
                                                               "soundfont_filepath": "DoreMarkYamahaS6-v1.6.sf2"})

        bass_rhythm_param = Parameter("rhythm")
        bass_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:2/4"], "cbn=-1", priority=1)
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=A,cbc=1/4|efi=A,cbc=2/4|efi=A,cbc=3/4")
        bass_rhythm_param.add_constrained_value(["1/4:1/4"], "efi=A,cbc=4/4")
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=B,br=1/2")
        bass_rhythm_param.add_constrained_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=B,br=2/2")

        accompaniment_volume_param = Parameter("volume")
        accompaniment_volume_param.set_interpolation_counter("ebp")
        accompaniment_volume_param.add_constrained_interpolation_value("epa_accompaniment_start_episode_volume", 0, "efi=A")
        accompaniment_volume_param.add_constrained_interpolation_value("epa_accompaniment_end_episode_volume", 1, "efi=A")
        accompaniment_volume_param.add_constrained_interpolation_value("epb_accompaniment_start_episode_volume", 0, "efi=B")
        accompaniment_volume_param.add_constrained_interpolation_value("epb_accompaniment_end_episode_volume", 1, "efi=B")

        accompaniment_choices = ["Bass+Chords 1", "Bass+Chords 2", "Pedal", "Arpeggio 1", "Arpeggio 2", "Chords"]
        accompaniment_num = accompaniment_choices.index(pdict["accompaniment"])

        bass_backbone_note_sequence_spec, chord_tonic_backbone_note_sequence_spec, chord_third_backbone_note_sequence_spec, chord_fifth_backbone_note_sequence_spec = AccompanimentUtils.get_accompaniment_specs(accompaniment_num, bass_instrument_param, chords_instrument_param, accompaniment_volume_param)

        vl_melody_volume_param = Parameter("volume")
        vl_melody_volume_param.set_interpolation_counter("ebp")
        vl_melody_volume_param.add_constrained_interpolation_value(epa_start_volume, 0, "efi=A")
        vl_melody_volume_param.add_constrained_interpolation_value(epa_end_volume, 1, "efi=A")
        vl_melody_volume_param.add_constrained_interpolation_value(epb_start_volume, 0, "efi=B")
        vl_melody_volume_param.add_constrained_interpolation_value(epb_end_volume, 1, "efi=B")

        vl_melody_backbone_length_param = Parameter("backbone_length")
        vl_melody_backbone_length_param.add_constrained_value(1, "cbn=0|cbn=-1", priority=2)
        vl_melody_backbone_length_param.add_constrained_random_range_value(3, 4, "efi=A")
        vl_melody_backbone_length_param.add_constrained_random_range_value(5, 7, "efi=B")
        vl_melody_backbone_length_param.set_interpolation_counter("ebp")
        vl_melody_backbone_length_param.add_constrained_interpolation_value(4, 0, "en=-1", priority=1)
        vl_melody_backbone_length_param.add_constrained_interpolation_value(2, 1, "en=-1", priority=1)

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
                                                             "composition_title": title + " (First Draft)",
                                                             "show_chord_name": False,
                                                             "score_parts": pre_edit_score_parts})

        likelihood_edit_pc = pdict["likelihood_editing_amount"]

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
            Parameter("application_probability_pc", likelihood_edit_pc),
            fixed_scale_param,
            vl_melody_in_bar_repetition_param,
            vl_melody_over_bar_repetition_param
        ]

        vl_melody_interestingness_edit_spec = ParameterisedSpecification(vl_melody_interestingness_edit_params)

        bass_passover_notes_param = Parameter("passover_notes")
        bass_passover_notes_param.add_constrained_value(True, "cbn=-1")

        bass_interest_changes = {"output_composition_id": "bass_ie",
                                 "track_num": 0, "focal_pitch": 43,
                                 "repetition": "disallow", "application_probability_pc": likelihood_edit_pc}
        tonic_interest_changes = {"output_composition_id": "tonic_ie",
                                  "track_num": 1, "focal_pitch": 55,
                                  "repetition": "disallow", "application_probability_pc": likelihood_edit_pc}
        third_interest_changes = {"output_composition_id": "third_ie",
                                  "track_num": 2, "focal_pitch": 55,
                                  "repetition": "disallow", "application_probability_pc": likelihood_edit_pc}
        fifth_interest_changes = {"output_composition_id": "fifth_ie",
                                  "track_num": 3, "focal_pitch": 55,
                                  "repetition": "disallow", "application_probability_pc": likelihood_edit_pc}

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

        intervals = []
        if pdict["harmonisation_intervals"] != "None":
            intervals = [int(i) for i in pdict["harmonisation_intervals"].split(",")]

        randomise_harmonisation_choice_order = (pdict["harmonisation_choice_order"] == "Disordered")
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
            Parameter("intervals_allowed", intervals),
            Parameter("randomise_intervals", randomise_harmonisation_choice_order),
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

        awkward_rhythm_edit_action_param = Parameter("edit_action")
        awkward_rhythm_edit_action_param.add_constrained_value("make_first_rest", "tn=5")
        awkward_rhythm_edit_action_param.add_constrained_value("make_second_rest", "tn=5")

        awkward_rhythm_params = [
            Parameter("applier_class_name", "AwkwardRhythmEditor"),
            Parameter("output_composition_id", "awkward_edited"),
            awkward_rhythm_edit_action_param
        ]
        awkward_rhythm_editor_spec = ParameterisedSpecification(awkward_rhythm_params)

        target_tag_param = Parameter("target_tag")
        target_tag_param.add_constrained_value(pdict["episode_a_listening_target"], "efi=A")
        target_tag_param.add_constrained_value(pdict["episode_b_listening_target"], "efi=B")
        fixed_scale_param = Parameter("fixed_scale")
        fixed_scale_param.add_constrained_value(None, "efi=A")
        fixed_scale_param.add_constrained_value(None, "efi=B")

        if pdict["listening_editing_effort"] == "Low":
          num_listening_trials = 5
        if pdict["listening_editing_effort"] == "Medium":
          num_listening_trials = 10
        if pdict["listening_editing_effort"] == "High":
          num_listening_trials = 20

        listening_edit_params = [
            Parameter("applier_class_name", "MTGListeningModelEditor"),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("performance_spec", performance_spec),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("ffmpeg_cli", "ffmpeg"),
            Parameter("temp_dir", "."),
            Parameter("pc_bars_per_episode", pdict["listening_editing_amount"]),
            Parameter("num_hill_climb_trials_per_bar", num_listening_trials),
            Parameter("track_num", 4),
            Parameter("num_rounds", pdict["listening_editing_rounds"]),
            Parameter("discordancy_spec", discordancy_spec),
            Parameter("allow repetition", False),
            target_tag_param,
            fixed_scale_param
        ]
        listening_edit_spec = ParameterisedSpecification(listening_edit_params)

        listening_analyser_params = [
            Parameter("applier_class_name", "MTGListeningModelAnalyser"),
            Parameter("output_composition_id", "listening_analysed"),
            Parameter("soundfont_filepath", soundfont_filepath),
            Parameter("performance_spec", performance_spec),
            Parameter("fluidsynth_cli", "fluidsynth"),
            Parameter("pc_bars_to_tag", pdict["highlight_amount"]),
            Parameter("output_stem", f"Outputs/flaneur_{random_seed}_harmonised")
        ]
        listening_analyser_spec = ParameterisedSpecification(listening_analyser_params)

        pause_length_param = Parameter("pause_length_64ths")
        if pdict["end_pause"] > 0:
          pause_length_param.add_constrained_value(pdict["end_pause"], "tn=4,tnn=-1", 1)
        if pdict["episode_end_pause"] > 0:
          pause_length_param.add_constrained_value(pdict["episode_end_pause"], "tn=4,enn=-1,nl>=16,nl<32", 0)
        pause_editor_params = [
            Parameter("applier_class_name", "PauseEditor"),
            Parameter("output_composition_id", "pause_edited"),
            pause_length_param
        ]
        pause_editor_spec = ParameterisedSpecification(pause_editor_params)

        harmonised_score_parts = [{"part_id": "Piano", "part_name": "Piano",
                                  "track_details": [("treble", [4, 5]), ("bass", [0, 1, 2, 3])]}]

        harmonised_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"input_composition_id": "interest_analysed",
                                                               "composition_title": title + " (Second Draft)",
                                                               "output_stem": output_stem + "_harmonised",
                                                               "show_chord_name": False,
                                                               "export_video": False,
                                                               "score_parts": harmonised_score_parts})

        final_exporter_spec = ParameterisedSpecification(total_exporter_params,
                                                              {"input_composition_id": "pause_edited",
                                                               "output_stem": output_stem + "_final",
                                                               "show_chord_name": False,
                                                               "export_video": True,
                                                               "score_parts": harmonised_score_parts})

        surplus_note_removal_editor_spec = ParameterisedSpecification([
            Parameter("applier_class_name", "SurplusNoteRemovalEditor")
        ])

        lead_sheet_display_spec = ParameterisedSpecification([
            Parameter("applier_class_name", "ColabDisplayCommunicator"),
            Parameter("text", "Here is the lead sheet for the composition:"),
            Parameter("pdf_postfix", "lead_sheet"),
            Parameter("show_mp3", True)
        ])

        pre_edit_display_spec = ParameterisedSpecification([
            Parameter("applier_class_name", "ColabDisplayCommunicator"),
            Parameter("text", "This is the first draft of the composition:"),
            Parameter("pdf_postfix", "pre_edit"),
            Parameter("show_mp3", True)
        ])

        harmonised_display_spec = ParameterisedSpecification([
            Parameter("applier_class_name", "ColabDisplayCommunicator"),
            Parameter("text", "This is the second draft of the composition:"),
            Parameter("pdf_postfix", "harmonised"),
            Parameter("show_mp3", True)
        ])

        final_display_spec = ParameterisedSpecification([
            Parameter("applier_class_name", "ColabDisplayCommunicator"),
            Parameter("text", "Here is a video performance of the final composition:"),
            Parameter("pdf_postfix", None),
            Parameter("show_mp3", False)
        ])

        clean_exporter_spec = ParameterisedSpecification(total_exporter_params, {
            "applier_class_name": "ScoreExporter",
            "input_composition_id": "pause_edited",
            "show_colours": False,
            "output_stem": output_stem + "_clean",
            "show_chord_name": False,
            "export_video": False,
            "score_parts": harmonised_score_parts})

        specs_to_apply_param = []
        specs_to_apply_param.append(form_spec)
        specs_to_apply_param.append(chord_sequence_spec)
        specs_to_apply_param.append(lead_sheet_generator_spec)
        specs_to_apply_param.append(lead_sheet_exporter_spec)
        specs_to_apply_param.append(lead_sheet_display_spec)
        specs_to_apply_param.append(bass_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_tonic_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_third_backbone_note_sequence_spec)
        specs_to_apply_param.append(chord_fifth_backbone_note_sequence_spec)
        specs_to_apply_param.append(vl_melody_spec)
        specs_to_apply_param.append(melody_passing_notes_spec)
        specs_to_apply_param.append(pre_edit_exporter_spec)
        specs_to_apply_param.append(pre_edit_display_spec)
        if likelihood_edit_pc > 0:
          specs_to_apply_param.append(vl_melody_interestingness_edit_spec)
          specs_to_apply_param.append(bass_interestingness_edit_spec)
          specs_to_apply_param.append(chord_tonic_interestingness_edit_spec)
          specs_to_apply_param.append(chord_third_interestingness_edit_spec)
          specs_to_apply_param.append(chord_fifth_interestingness_edit_spec)
        if pdict["bass_passing_notes"] == "On":
          specs_to_apply_param.append(bass_passing_notes_spec)
        specs_to_apply_param.append(note_removal_editor)
        specs_to_apply_param.append(melody_repetition_editor_spec)
        if pdict["melody_tuplets"] == "On":
          specs_to_apply_param.append(melody_tuplets_spec)
        if pdict["bass_tuplets"] == "On":
          specs_to_apply_param.append(bass_tuplets_spec)
        specs_to_apply_param.append(surplus_note_removal_editor_spec)
        if pdict["harmonisation_intervals"] != "None":
          specs_to_apply_param.append(harmonisation_edit_spec)
        specs_to_apply_param.append(harmonised_exporter_spec)
        specs_to_apply_param.append(harmonised_display_spec)
        if pdict["likelihood_improvements"] == "Show":
          specs_to_apply_param.append(interestingness_edit_analyser_spec)
        if pdict["discordancies"] == "Show":
          specs_to_apply_param.append(discordancy_analyser_spec)
        if pdict["tuplets"] == "Show":
          specs_to_apply_param.append(tuplet_analyser_spec)
        specs_to_apply_param.append(awkward_rhythm_editor_spec)
        if (pdict["episode_a_listening_target"] != "none" or pdict["episode_a_listening_target"] != "none") and pdict["listening_editing_amount"] > 0:
          specs_to_apply_param.append(listening_edit_spec)
        if pdict["local_highlights"] == "Show" or pdict["global_highlights"] == "Show":
          specs_to_apply_param.append(listening_analyser_spec)
        if pdict["end_pause"] > 0 or pdict["episode_end_pause"] > 0:
          specs_to_apply_param.append(pause_editor_spec)
        specs_to_apply_param.append(final_exporter_spec)
        specs_to_apply_param.append(final_display_spec)
        specs_to_apply_param.append(clean_exporter_spec)

        composition_params = [
            Parameter("applier_class_name", "CompositionGenerator"),
            Parameter("output_composition_id", "final_composition"),
            Parameter("title", title),
            Parameter("random_seed", random_seed),
            Parameter("subtitle", scale_subtitle),
            Parameter("random_seed", random_seed),
            Parameter("dynamic_lead_track_num", 4),
            Parameter("specs_to_apply", specs_to_apply_param)
        ]

        composition_generation_spec = ParameterisedSpecification(composition_params)
        return composition_generation_spec
