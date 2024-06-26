from ParleyV2.Specifications.SoundFontClasses import *
from ParleyV2.Utils.ExtractionUtils import *


class VolumeUtils:
    # See: https://en.wikipedia.org/wiki/Dynamics_(music)
    vols_dict = {(5, 9): "ppppp", (10, 15): "pppp", (16, 32): "ppp", (33, 48): "pp", (49, 63): "p",
                 (64, 79): "mp", (80, 95): "mf", (96, 111): "f", (112, 125): "ff", (126, 126): "fff",
                 (127, 127): "ffff"}

    def change_volumes(spec, previous_spec, bar, note_sequence):
        bar_start_volume = spec["volume"] if previous_spec is None else previous_spec["volume"]
        bar_end_volume = spec["volume"]
        for note in note_sequence.notes:
            diff = bar_end_volume - bar_start_volume
            volume = bar_start_volume + ((note.timing.start64th/64) * diff)
            note.volume = int(volume)
        if spec["leads_dynamics"]:
            bar.volume_direction = VolumeUtils.get_vol_direction(bar_start_volume)

    def get_vol_direction(midi_volume):
        for (low, high) in VolumeUtils.vols_dict:
            if low <= midi_volume <= high:
                return VolumeUtils.vols_dict[(low, high)]

    def adjust_volume_for_bad_soundfont(note, note_sequence, soundfont_filepath, msg_type):
        if "DoreMarkYamahaS6-v1.6.sf2" in soundfont_filepath:
            if note.pitch == 58 or note.pitch == 57 or note.pitch == 56:
                return int(round(note.volume * 0.8))
        return note.volume

    def homogenise_volumes(composition):
        notes = ExtractionUtils.get_notes_in_composition(composition)
        av_vol = int(round(sum([n.volume for n in notes])/len(notes)))
        for note in notes:
            note.volume = av_vol
        for bar in composition.bars:
            bar.volume_direction = None
        composition.bars[0].volume_direction = VolumeUtils.get_vol_direction(av_vol)

"""
    def update_volumes(composition, episode, note_gen_spec):
        specs = []
        for bar_ind, bar in enumerate(episode.bars):
            specs.append(SpecUtils.get_instantiated_copy(note_gen_spec, bar))
        for bar_ind, bar in enumerate(episode.bars):
            spec = specs[bar_ind]
            spec = note_gen_spec.instantiate_me(composition, bar)
            midi_volume = spec.volume
            if note_gen_spec.leads_dynamics_direction:
                previous_midi_volume = None if bar_ind == 0 else specs[bar_ind - 1].volume
                previous_bar_directions = None if previous_midi_volume is None else VolumeUtils.get_vol_direction(previous_midi_volume)
                this_bar_directions = VolumeUtils.get_vol_direction(midi_volume)
                if this_bar_directions != previous_bar_directions:
                    bar.directions = this_bar_directions
            next_midi_volume = spec.volume if bar_ind == len(episode.bars) - 1 else specs[bar_ind + 1].volume
            for note_sequence in bar.note_sequences:
                if note_sequence.track_num == spec.track_num:
                    bar_duration = 0
                    for note in note_sequence.notes:
                        note.volume = int(round((bar_duration * next_midi_volume) + ((1 - bar_duration) * midi_volume)))
                        bar_duration += note.num_fracs/128
"""

