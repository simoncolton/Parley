from ParleyV2.Specifications.SoundFontClasses import *


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
            bar.directions = VolumeUtils.get_vol_direction(bar_start_volume)

    def get_vol_direction(midi_volume):
        for (low, high) in VolumeUtils.vols_dict:
            if low <= midi_volume <= high:
                return VolumeUtils.vols_dict[(low, high)]

    def update_volumes(episode, note_gen_spec):
        specs = []
        for bar_ind, bar in enumerate(episode.bars):
            specs.append(SpecUtils.get_instantiated_copy(note_gen_spec, bar))
        for bar_ind, bar in enumerate(episode.bars):
            spec = specs[bar_ind]
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

    def adjust_volume_for_bad_soundfont(note, note_sequence, soundfont_filepath, msg_type):
        if soundfont_filepath == SFYamahaPiano.soundfont_filepath:
            if note.pitch == 58:
                return int(round(note.volume * 0.8))
        return note.volume
