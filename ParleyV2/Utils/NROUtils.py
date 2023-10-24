import random
from ParleyV2.Utils.MusicUtils import *


class NROUtils:

    def get_all_nros():
        moves = range(-2, 3)
        all_nros = [[]]
        for rep in range(0, 3):
            new_nros = []
            for nro in all_nros:
                for move in moves:
                    new_nro = nro.copy()
                    new_nro.append(move)
                    new_nros.append(new_nro)
            all_nros = new_nros
        final_nros = []
        for [a, b, c] in all_nros:
            if 0 in [a, b, c]:
                if a is not b or a is not c or b is not c:
                    final_nros.append([a, b, c])
        return final_nros

    all_nros = get_all_nros()

    def get_random_admissible_cnro(trichord_pitches, cnro_len, fixed_scale, chord_type_allowance, must_change, original_cnro_len=None):
        trial_num = 0
        is_ok = False
        while is_ok is False and trial_num < 1000:
            cnro = [0, 0, 0]
            for i in range(0, cnro_len):
                nro = random.choice(NROUtils.all_nros)
                for j in range(0, 3):
                    cnro[j] += nro[j]
            new_pitches = trichord_pitches.copy()
            for i in range(0, len(cnro)):
                new_pitches[i] += cnro[i]
            is_ok = (MusicUtils.is_nrt_admissible(new_pitches)
                     and MusicUtils.chord_type_is_ok(new_pitches, chord_type_allowance)
                     and MusicUtils.chord_is_in_scale(new_pitches, fixed_scale))
            if is_ok and must_change:
                prev = MusicUtils.mapped_to_mid_octave(trichord_pitches)
                new_p = MusicUtils.mapped_to_mid_octave(new_pitches)
                if prev == new_p:
                    is_ok = False
            if not is_ok and original_cnro_len is not None and cnro_len > (original_cnro_len + 3):
                is_ok = (MusicUtils.is_nrt_admissible(new_pitches)
                         and MusicUtils.chord_is_in_scale(new_pitches, fixed_scale))
            trial_num += 1
        if is_ok:
            return cnro, new_pitches
        else:
            original_cnro_len = cnro_len if original_cnro_len is None else original_cnro_len
            return NROUtils.get_random_admissible_cnro(trichord_pitches, cnro_len + 1, fixed_scale,
                                                       chord_type_allowance, must_change, original_cnro_len)

