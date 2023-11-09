from ParleyV2.Specifications.ConstrainedSpecification import *

class AccompanimentUtils:

    def get_bass_rhythm_param(accompaniment_num):
        bass_rhythm_param = Parameter("rhythm")
        if accompaniment_num < 2:
            bass_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:2/4"], "cbn=-1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=A,cbc=1/4|efi=A,cbc=2/4|efi=A,cbc=3/4")
            bass_rhythm_param.add_constrained_value(["1/4:1/4"], "efi=A,cbc=4/4")
            bass_rhythm_param.add_constrained_value(["1/4:1/4", "3/4:1/4"], "efi=B,br=1/2")
            bass_rhythm_param.add_constrained_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=B,br=2/2")
        elif accompaniment_num == 2:
            bass_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/1:1/1"], "ebn=-1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/8:1/8", "2/8:1/8", "3/8:1/8", "4/8:1/8", "5/8:1/8", "6/8:1/8", "7/8:1/8", "8/8:1/8"], "efi=A|efi=B")
        elif accompaniment_num == 3:
            bass_rhythm_param.add_constrained_value([], "cbn=1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/4:1/8", "3/4:1/8"], "efi=A|efi=B")
            bass_rhythm_param.add_constrained_value(["1/1:1/1"], "ebn=-1", priority=1)
            bass_rhythm_param.add_constrained_value(["1/4:1/4", "2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=B,br=4/4", priority=1)
        elif accompaniment_num == 4:
            return AccompanimentUtils.get_full_arpeggio_param("bass")
        elif accompaniment_num == 5:
            return AccompanimentUtils.get_chords_only_param(1)

        return bass_rhythm_param

    def get_chord_rhythms_param(accompaniment_num):

        chord_rhythm_param = Parameter("rhythm")
        chord_rhythm_param.add_constrained_value([], "cbn=1", priority=1)

        if accompaniment_num == 0:
            chord_rhythm_param.add_constrained_value([], "efi=B,br=2/2")
            chord_rhythm_param.add_constrained_value(["2/4:1/4"], "cbn=-1", priority=1)
            chord_rhythm_param.add_constrained_value(["2/4:1/4", "4/4:1/4"], "efi=A,cbc=1/4|efi=A,cbc=2/4|efi=A,cbc=3/4")
            chord_rhythm_param.add_constrained_value(["2/4:1/4", "3/4:1/4", "4/4:1/4"], "efi=A,cbc=4/4")
            chord_rhythm_param.add_constrained_value(["2/4:1/4", "4/4:1/4"], "efi=B,br=1/2")

        if accompaniment_num == 1:
            chord_rhythm_param.add_constrained_value([], "efi=B,br=2/2")
            chord_rhythm_param.add_constrained_value(["3/8:1/8", "4/8:1/8", "5/8:4/8"], "cbn=-1", priority=1)
            chord_rhythm_param.add_constrained_value(["3/8:1/8", "4/8:1/8", "5/8:2/8", "7/8:1/8", "8/8:1/8"], "efi=A|efi=B")

        if accompaniment_num == 2:
            chord_rhythm_param.add_constrained_value([], "efi=A|efi=B")

        return chord_rhythm_param

    def get_tonic_rhythm_param(accompaniment_num):
        if accompaniment_num < 2:
            return AccompanimentUtils.get_chord_rhythms_param(accompaniment_num)
        elif accompaniment_num == 2:
            chord_rhythm_param = Parameter("rhythm")
            chord_rhythm_param.add_constrained_value([], "cbn=1|ebn=-1", priority=1)
            chord_rhythm_param.add_constrained_value(["1/8:1/8", "4/8:1/8", "5/8:1/8"], "efi=A,cbc=2/2")
            return chord_rhythm_param
        elif accompaniment_num == 3:
            return AccompanimentUtils.get_arpeggio_rhythm_param(4, 8)
        elif accompaniment_num == 4:
            return AccompanimentUtils.get_full_arpeggio_param("tonic")
        elif accompaniment_num == 5:
            return AccompanimentUtils.get_chords_only_param(1)

    def get_third_rhythm_param(accompaniment_num):
        if accompaniment_num < 3:
            return AccompanimentUtils.get_chord_rhythms_param(accompaniment_num)
        elif accompaniment_num == 3:
            return AccompanimentUtils.get_arpeggio_rhythm_param(2, 6)
        elif accompaniment_num == 4:
            return AccompanimentUtils.get_full_arpeggio_param("third")
        elif accompaniment_num == 5:
            return AccompanimentUtils.get_chords_only_param(2)

    def get_fifth_rhythm_param(accompaniment_num):
        if accompaniment_num < 3:
            return AccompanimentUtils.get_chord_rhythms_param(accompaniment_num)
        elif accompaniment_num == 3:
            return AccompanimentUtils.get_arpeggio_rhythm_param(3, 7)
        elif accompaniment_num == 4:
            return AccompanimentUtils.get_full_arpeggio_param("fifth")
        elif accompaniment_num == 5:
            return AccompanimentUtils.get_chords_only_param(2)

    def get_chords_only_param(chord_num):
        chords_only_param = Parameter("rhythm")
#        chords_only_param.add_constrained_value([], "cbn=1", priority=2)
        chords_only_param.add_constrained_value(["1/1:1/1"], "efi=A|efi=B", priority=2)
        return chords_only_param

    def get_arpeggio_rhythm_param(first_beat, second_beat):
        arpeggio_rhythm_param = Parameter("rhythm")
        arpeggio_rhythm_param.add_constrained_value([], "cbn=1", priority=2)
        arpeggio_rhythm_param.add_constrained_value([], "efi=B,br=4/4", priority=1)
        arpeggio_rhythm_param.add_constrained_value([f"{first_beat}/8:1/8", f"{second_beat}/8:1/8"], "efi=A|efi=B")
        arpeggio_rhythm_param.add_constrained_value(["1/1:1/1"], "ebn=-1", priority=2)
        return arpeggio_rhythm_param

    def get_full_arpeggio_param(chord_pos):
        arpeggio_rhythm_param = Parameter("rhythm")
        arpeggio_rhythm_param.add_constrained_value([], "cbn=1|cbn=-1", priority=2)
        if chord_pos == "bass" or chord_pos == "tonic":
            arpeggio_rhythm_param.add_constrained_value(["1/1:1/1"], "cbn=1|cbn=-1", priority=2)
        if chord_pos == "bass":
            positions = [1, 7, 13]
        elif chord_pos == "third":
            positions = [2, 6, 8, 12, 14]
        elif chord_pos == "fifth":
            positions = [3, 5, 9, 11, 15]
        elif chord_pos == "tonic":
            positions = [4, 10, 16]
        ids = []
        for pos in positions:
            ids.append(f"{pos}/16:1/16")
        arpeggio_rhythm_param.add_constrained_value(ids, "efi=A|efi=B")
        print(arpeggio_rhythm_param)
        return arpeggio_rhythm_param

    def get_accompaniment_specs(accompaniment_num, bass_instrument_param, chords_instrument_param, accompaniment_volume_param):

        bass_rhythm_param = AccompanimentUtils.get_bass_rhythm_param(accompaniment_num)
        bass_focal_pitch = 43
        tonic_focal_pitch = 50
        third_focal_pitch = 50
        fifth_focal_pitch = 50
        if accompaniment_num == 2:
            tonic_focal_pitch = 55
        if accompaniment_num == 3:
            tonic_focal_pitch = 60
            third_focal_pitch = 50
            fifth_focal_pitch = 55

        params1 = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("input_composition_id", "chord_sequence"),
            Parameter("output_composition_id", "bass_backbone"),
            Parameter("voice_id", "bass"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 0),
            Parameter("channel_num", 0),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", bass_focal_pitch),
            bass_instrument_param,
            bass_rhythm_param,
            accompaniment_volume_param
        ]
        spec1 = ParameterisedSpecification(params1)

        tonic_rhythm_param = AccompanimentUtils.get_tonic_rhythm_param(accompaniment_num)
        params2 = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("output_composition_id", "tonic_backbone"),
            Parameter("voice_id", "tonic_chord"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 1),
            Parameter("channel_num", 1),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 1),
            Parameter("focal_pitch", tonic_focal_pitch),
            chords_instrument_param,
            tonic_rhythm_param,
            accompaniment_volume_param
        ]
        spec2 = ParameterisedSpecification(params2)

        third_rhythm_param = AccompanimentUtils.get_third_rhythm_param(accompaniment_num)
        params3 = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("output_composition_id", "tonic_backbone"),
            Parameter("voice_id", "tonic_chord"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 1),
            Parameter("channel_num", 1),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 2),
            Parameter("focal_pitch", third_focal_pitch),
            chords_instrument_param,
            third_rhythm_param,
            accompaniment_volume_param
        ]
        spec3 = ParameterisedSpecification(params3)

        fifth_rhythm_param = AccompanimentUtils.get_fifth_rhythm_param(accompaniment_num)
        params4 = [
            Parameter("applier_class_name", "RhythmNoteSequenceGenerator"),
            Parameter("output_composition_id", "tonic_backbone"),
            Parameter("voice_id", "tonic_chord"),
            Parameter("instrument_name", "piano"),
            Parameter("track_num", 1),
            Parameter("channel_num", 1),
            Parameter("leads_dynamics", False),
            Parameter("backbone_note", 3),
            Parameter("focal_pitch", fifth_focal_pitch),
            chords_instrument_param,
            fifth_rhythm_param,
            accompaniment_volume_param
        ]
        spec4 = ParameterisedSpecification(params4)

        return spec1, spec2, spec3, spec4