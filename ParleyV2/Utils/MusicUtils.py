import random
from Utils.MusicUtils import *
from Logistics.Constants import *
from Artefacts.Artefacts import *


class MusicUtils:

    def get_octave(pitch):
        return pitch//12 - 1

    def pitch_class(pitch):
            return pitch % 12

    def pitch_class_distance_from_pitches(pitch1, pitch2):
        pitch_class1 = MusicUtils.pitch_class(pitch1)
        pitch_class2 = MusicUtils.pitch_class(pitch2)
        return MusicUtils.pitch_class_distance(pitch_class1, pitch_class2)

    def pitch_class_distance(pitch_class1, pitch_class2):
        d1 = abs(pitch_class1 - pitch_class2)
        d2 = abs(pitch_class1 + 12 - pitch_class2)
        d3 = abs(pitch_class2 + 12 - pitch_class1)
        return min([d1, d2, d3])

    def get_chord_name(chord, scale_name):
        a, b, c = MusicUtils.mapped_to_mid_octave(chord.pitches)
        for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
            for chord_type in Constants.chord_types_hash.keys():
                intervals = Constants.chord_types_hash[chord_type]
                if t2 - t1 == intervals[0] and t3 - t2 == intervals[1]:
                    chord_name = Constants.note_letters[MusicUtils.pitch_class(t1)] + "_" + chord_type
                    return chord_name
        return None

    def get_pitches_for_base_chord_in_scale(scale_name):
        scale_pitch_classes = MusicUtils.pitch_classes_for_scale(scale_name)
        return [scale_pitch_classes[c] + 60 for c in [0, 2, 4]]

    def are_same_pitch_classes(pitches1, pitches2):
        pitch_classes1 = [MusicUtils.pitch_class(p) for p in pitches1]
        for pitch in pitches2:
            if MusicUtils.pitch_class(pitch) not in pitch_classes1:
                return False
        return True

    def pitch_classes_for_chord(chord):
        pitch_classes = []
        for pitch in chord.pitches:
            pitch_classes.append(MusicUtils.pitch_class(pitch))
        return pitch_classes

    def pitch_class_is_backbone_for_chord(pitch_class, chord):
        for cp in chord.pitches:
            pc2 = MusicUtils.pitch_class(cp)
            if pc2 == pitch_class:
                return True
        return False

    def pitch_is_backbone_for_chord(pitch, chord):
        pc = MusicUtils.pitch_class(pitch)
        for cp in chord.pitches:
            pc2 = MusicUtils.pitch_class(cp)
            if pc2 == pc:
                return True
        return False

    def get_interval(pitch1, pitch2):
        pitch_class1 = MusicUtils.pitch_class(pitch1)
        pitch_class2 = MusicUtils.pitch_class(pitch2)
        dist = abs(pitch_class1 - pitch_class2)
        return min(dist, 12-dist)

    def is_nrt_admissible(pitches):
        pitch_classes = [MusicUtils.pitch_class(a) for a in pitches]
        pairs = []
        for i in range(0, len(pitch_classes)):
            for j in range(i + 1, len(pitch_classes)):
                pairs.append([pitch_classes[i], pitch_classes[j]])
        for pair in pairs:
            if abs(pair[0] - pair[1]) <= 1:
                return False
            if abs(pair[0] + 12 - pair[1]) <= 1:
                return False
            if abs(pair[0] - 12 - pair[1]) <= 1:
                return False
        return True

    def get_root_inversion(pitches):
        [a, b, c] = pitches
        if MusicUtils.is_major(pitches):
            for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
                if t2 - t1 == 4 and t3 - t2 == 3:
                    return [t1, t2, t3]
        elif MusicUtils.is_minor(pitches):
            for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
                if t2 - t1 == 3 and t3 - t2 == 4:
                    return [t1, t2, t3]
        return pitches

    def is_major(pitches):
        a, b, c = MusicUtils.mapped_to_mid_octave(pitches)
        for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
            if t2 - t1 == 4 and t3 - t2 == 3:
                return True
        return False

    def is_minor(pitches):
        a, b, c = MusicUtils.mapped_to_mid_octave(pitches)
        for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
            if t2 - t1 == 3 and t3 - t2 == 4:
                return True
        return False

    def is_major_or_minor(pitches):
        return MusicUtils.is_major(pitches) or MusicUtils.is_minor(pitches)

    def get_chord_type(pitches):
        a, b, c = MusicUtils.mapped_to_mid_octave(pitches)
        for t1, t2, t3 in [[a, b, c], [c - 12, a, b], [b - 12, c - 12, a]]:
            for chord_type in Constants.chord_types_hash.keys():
                intervals = Constants.chord_types_hash[chord_type]
                if t2 - t1 == intervals[0] and t3 - t2 == intervals[1]:
                    return chord_type
        return None

    def get_chords_for_scale(scale, chord_type_allowance, focal_pitch):
        chords = []
        pcs = scale.pitch_classes
        l = len(pcs)
        for ind1 in range(0, l-2):
            for ind2 in range(ind1 + 1, l-1):
                for ind3 in range(ind2 + 1, l):
                    pitches = [pcs[ind1], pcs[ind2], pcs[ind3]]
                    if MusicUtils.chord_type_is_ok(pitches, chord_type_allowance):
                        pitches = MusicUtils.mapped_to_focal_pitch(pitches, focal_pitch)
                        chord = Chord(pitches=pitches, scale_name=scale.tonic_letter + "_" + scale.scale_type)
                        chord.chord_name = MusicUtils.get_chord_name(chord, scale)
                        chords.append(chord)
        return chords

    def chord_type_is_ok(pitches, chord_type_allowance):
        if chord_type_allowance is None:
            return True
        chord_type = MusicUtils.get_chord_type(pitches)
        if chord_type is None:
            return False
        return chord_type in chord_type_allowance

    def chord_is_in_scale(pitches, scale):
        if scale is None:
            return True
        pitch_classes = scale.pitch_classes
        for pitch in pitches:
            if MusicUtils.pitch_class(pitch) not in pitch_classes:
                return False
        return True

    def mapped_to_mid_octave(pitches):
        mapped_pitches = []
        for pitch in pitches:
            try_pitch = pitch + (12 * 5)
            mapped_pitch = pitch
            while try_pitch > 0:
                if try_pitch >= 60 and try_pitch < 72:
                    mapped_pitch = try_pitch
                    break
                try_pitch -= 12
            mapped_pitches.append(mapped_pitch)
        mapped_pitches.sort()
        return mapped_pitches

    def map_pitch_to_focal_pitch(pitch, focal_pitch):
        return MusicUtils.mapped_to_focal_pitch([pitch], focal_pitch)[0]

    def mapped_to_focal_pitch(pitches, focal_pitch):
        mapped_pitches = []
        for pitch in pitches:
            min_dist = 10000
            try_pitch = pitch + (12 * 5)
            mapped_pitch = pitch
            while try_pitch > 0:
                dist = abs(focal_pitch - try_pitch)
                if dist < min_dist:
                    mapped_pitch = try_pitch
                    min_dist = dist
                try_pitch -= 12
            mapped_pitches.append(mapped_pitch)
        mapped_pitches.sort()
        return mapped_pitches

    def mapped_to_pitch_range(pitch, pitch_range_low, pitch_range_high):
        pitch_class = MusicUtils.pitch_class(pitch)
        pairs = []
        for p in range(pitch_range_low, pitch_range_high + 1):
            if MusicUtils.pitch_class(p) == pitch_class:
                dist = abs(pitch - p)
                pairs.append((dist, p))
        pairs.sort()
        return pairs[0][1]

    def note_is_in_scale(pitch, scale):
        return MusicUtils.pitch_class(pitch) in scale.pitch_classes

    def map_to_scale(pitch, scale):
        pitch_classes = scale.pitch_classes
        dist = 1
        while dist < 6:
            try_pitches = []
            if MusicUtils.pitch_class(pitch + dist) in pitch_classes:
                try_pitches.append(pitch + 1)
            if MusicUtils.pitch_class(pitch - 1) in pitch_classes:
                try_pitches.append(pitch - 1)
            random.shuffle(try_pitches)
            for p in try_pitches:
                if MusicUtils.pitch_class(p) in pitch_classes:
                    return p
            dist += 1
        return pitch

    def get_named_scale(scale_name):
        scale = Scale()
        scale.tonic_letter = scale_name.split("_")[0]
        scale.scale_type = scale_name.split("_")[1]
        intervals = Constants.scales_hash[scale.scale_type]
        tonic_pitch_class = Constants.note_letters.index(scale.tonic_letter)
        scale.pitch_classes = [(tonic_pitch_class + pos) % 12 for pos in intervals]
        scale.pitch_classes.sort()
        return scale

    def get_random_scale(chord_type_allowance=None):
        scale = Scale()
        scale.tonic_letter = random.choice(Constants.note_letters)
        scale.scale_type = random.choice(list(Constants.scales_hash.keys()))
        intervals = Constants.scales_hash[scale.scale_type]
        tonic_pitch_class = Constants.note_letters.index(scale.tonic_letter)
        scale.pitch_classes = [(tonic_pitch_class + pos) % 12 for pos in intervals]
        scale.pitch_classes.sort()
        if chord_type_allowance is not None:
            chords = MusicUtils.chords_satisfying_chord_type_allowance(scale, chord_type_allowance)
            if len(chords) == 0:
                return MusicUtils.get_random_scale(chord_type_allowance)
        return scale

    def chords_satisfying_chord_type_allowance(scale, chord_type_allowance):
        chords_in_scale = []
        chord_names = []
        for chord_type in chord_type_allowance.split(";"):
            [interval1, interval2] = Constants.chord_types_hash[chord_type]
            for tonic in scale.pitch_classes:
                third = (tonic + interval1) % 12
                fifth = (third + interval2) % 12
                if third in scale.pitch_classes and fifth in scale.pitch_classes:
                    chord_name = Constants.note_letters[tonic] + chord_type
                    if not chord_name in chord_names:
                        chord_names.append(chord_name)
                        chord = Chord([tonic, third, fifth], scale.tonic_letter + "_" + scale.scale_type, chord_name)
                        chords_in_scale.append(chord)
        return chords_in_scale

    def num_chords_satisfying_chord_type_allowance(scale_name, chord_type_allowance):
        return len(MusicUtils.chords_satisfying_chord_type_allowance(scale_name, chord_type_allowance))

    def closest_pitch_to_neighbours_for_pitch_class(target_pitch, pitch_class, prev_pitch, next_pitch):
        target_pitch_class = MusicUtils.pitch_class(target_pitch)
        diff = pitch_class - target_pitch_class
        posses = [target_pitch + diff, target_pitch + diff - 12, target_pitch + diff + 12]
        min_dist = 100000
        closest_pitch = posses[0]
        for poss in posses:
            dist1 = 0 if prev_pitch is None else abs(poss - prev_pitch)
            dist2 = 0 if next_pitch is None else abs(poss - next_pitch)
            dist = dist1 + dist2
            if dist < min_dist:
                min_dist = dist
                closest_pitch = poss
        return closest_pitch

    def get_passing_note_pitches(start_note, end_pitch, key_sig, policy):

        if start_note.pitch is None or end_pitch is None or start_note.pitch == end_pitch:
            return [start_note.pitch]

        direction = 1 if end_pitch > start_note.pitch else -1
        current_pitch = start_note.pitch
        passing_note_pitches = [current_pitch]
        previous_pitch = current_pitch
        current_pitch += direction
        while current_pitch != end_pitch:
            if key_sig is None:
                if abs(previous_pitch - current_pitch) > 1:
                    passing_note_pitches.append(current_pitch)
                    previous_pitch = current_pitch
            elif MusicUtils.note_is_in_scale(current_pitch, key_sig):
                passing_note_pitches.append(current_pitch)
            current_pitch += direction
        if policy == "mid":
            if len(passing_note_pitches) <= 2:
                return passing_note_pitches
            if len(passing_note_pitches) % 2 == 1:
                pos = len(passing_note_pitches)//2
                return [start_note.pitch, passing_note_pitches[pos]]
            else:
                pos = len(passing_note_pitches)//2 if bool(random.getrandbits(1)) else len(passing_note_pitches)//2 - 1
                return [start_note.pitch, passing_note_pitches[pos]]
        return passing_note_pitches

    def get_pitches_in_scale(scale):
        pitches = []
        for octave in range(0, 10):
            pitches.extend([i + (octave * 12) for i in scale.pitch_classes])
        return pitches

    def get_note_from_chord_interval(chord, focal_pitch, scale_interval):
        scale = MusicUtils.get_named_scale(chord.scale_name)
        base_pitch = MusicUtils.map_pitch_to_focal_pitch(chord.pitches[0], focal_pitch)
        pitches_in_scale = MusicUtils.get_pitches_in_scale(scale)
        base_ind = pitches_in_scale.index(base_pitch)
        return pitches_in_scale[base_ind + scale_interval]
