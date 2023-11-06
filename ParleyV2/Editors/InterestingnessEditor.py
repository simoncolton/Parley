import copy
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.ListeningUtils import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Utils.DiscordancyUtils import *
import tensorflow as tf
import numpy as np
from tqdm import tqdm


class InterestingnessEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec
        self.listening_model = None

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        self.listening_model = ListeningUtils.build_interestingness_model(ListeningUtils.classical_checkpoint_dir)
        track_num = self.edit_spec.get_value("track_num")
        for episode_num in tqdm(range(1, composition.num_episodes + 1), desc=f"Likelihood editing track {track_num}"):
            all_notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            episode_notes = [n for n in all_notes if composition.bars_hash[n.bar_num].episode_num == episode_num]
            self.apply_to_episode(composition, episode_notes, all_notes)
        return composition

    def apply_to_episode(self, composition, episode_notes, all_notes):
        for ind, note in enumerate(episode_notes):
            bar = composition.bars_hash[note.bar_num]
            spec = self.edit_spec.instantiate_me(composition, bar, note)
            if random.uniform(0, 1) < spec["application_probability_pc"]/100:
                passover_this_note = spec["passover_notes"]
                if passover_this_note is None:
                    passover_this_note = False
                if note.pitch is not None and not passover_this_note:
                    if note.tie_type is None or note.tie_type == "start":
                        self.update_note_pitch(composition, episode_notes, note)
                    else:
                        all_notes_ind = all_notes.index(note)
                        note.pitch = all_notes[all_notes_ind - 1].pitch
                        note.score_colour = all_notes[all_notes_ind - 1].score_colour

    def update_note_pitch(self, composition, episode_notes, note):
        bar = composition.bars_hash[note.bar_num]
        note_sequence = composition.note_sequences_hash[note.note_sequence_num]
        spec = self.edit_spec.instantiate_me(composition, bar, note)
        note_types = spec["note_types_to_change"]
        if note_types == "all" or note.type_type == note_types:
            is_first_note = note_sequence.notes.index(note) == 0
            pitch_repetition_allowed = (is_first_note and spec["over_bar_repetition"]) or (not is_first_note and spec["in_bar_repetition"])
            ind = episode_notes.index(note)
            previous_pitch_class = None
            if ind > 0:
                previous_pitch = episode_notes[ind - 1].pitch
                if previous_pitch is None:
                    pitch_repetition_allowed = True
                else:
                    previous_pitch_class = MusicUtils.pitch_class(previous_pitch)
            seed_pitch_classes = self.get_seed_pitch_classes(spec, episode_notes, note)
            current_pitch_class = MusicUtils.pitch_class(note.pitch)
            input_eval = tf.expand_dims(seed_pitch_classes, 0)
            self.listening_model.reset_states()
            predictions = self.listening_model(input_eval)
            activations = predictions[-1][-1]
            pitch_classes_allowed = None
            fixed_scale = spec["fixed_scale"]
            if fixed_scale is not None:
                pitch_classes_allowed = fixed_scale.pitch_classes
            sorted_pitch_classes = list(np.argsort(activations))
            sorted_pitch_classes.reverse()
            pos = 0
            is_ok = False
            chord_notes_fixed = spec["chord_notes_fixed"]
            while not is_ok and pos < len(sorted_pitch_classes):
                new_pitch_class = sorted_pitch_classes[pos]
                is_ok = self.set_pitch(composition, spec, pitch_repetition_allowed, chord_notes_fixed,
                                       previous_pitch_class, current_pitch_class, pitch_classes_allowed,
                                       note, episode_notes, new_pitch_class, ind, bar)
                pos += 1

            # Relax pitch class repetition constraint
            if not is_ok and not pitch_repetition_allowed:
                pos = 0
                while not is_ok and pos < len(sorted_pitch_classes):
                    new_pitch_class = sorted_pitch_classes[pos]
                    is_ok = self.set_pitch(composition, spec, True, chord_notes_fixed,
                                           previous_pitch_class, current_pitch_class, pitch_classes_allowed,
                                           note, episode_notes, new_pitch_class, ind, bar)
                    pos += 1

            # Relax chord notes constraint
            if not is_ok and not chord_notes_fixed:
                pos = 0
                while not is_ok and pos < len(sorted_pitch_classes):
                    new_pitch_class = sorted_pitch_classes[pos]
                    is_ok = self.set_pitch(composition, spec, True, True,
                                           previous_pitch_class, current_pitch_class, pitch_classes_allowed,
                                           note, episode_notes, new_pitch_class, ind, bar)
                    pos += 1

            note.score_colour = "blue"
            if sorted_pitch_classes.index(current_pitch_class) < sorted_pitch_classes.index(new_pitch_class):
                note.score_colour = "purple"
            if sorted_pitch_classes.index(current_pitch_class) > sorted_pitch_classes.index(new_pitch_class):
                note.score_colour = "green"
            if not is_ok:
                note.score_colour = "red"
            note.sorted_pitch_classes = [int(i) for i in sorted_pitch_classes] # transform from numpy.int64 AAAAAAGGGGHHHH

    def set_pitch(self, composition, spec, pitch_repetition_allowed, chord_notes_fixed,
                  previous_pitch_class, current_pitch_class,
                  pitch_classes_allowed, note, episode_notes, new_pitch_class, ind, bar):

        original_pitch = note.pitch
        discordancy_avoid_spec = spec["discordancy_avoid"]
        is_ok = pitch_classes_allowed is None or new_pitch_class in pitch_classes_allowed
        parent_chord = composition.chords_hash[note.chord_num]
        current_is_bb = MusicUtils.pitch_class_is_backbone_for_chord(current_pitch_class, parent_chord)
        new_is_bb = MusicUtils.pitch_class_is_backbone_for_chord(new_pitch_class, parent_chord)
        if chord_notes_fixed and current_is_bb and not new_is_bb:
            is_ok = False
        if is_ok and previous_pitch_class is not None and not pitch_repetition_allowed and new_pitch_class == previous_pitch_class:
            is_ok = False

        if is_ok:
            prev_pitch = None if ind == 0 else episode_notes[ind - 1].pitch
            next_pitch = None if ind == len(episode_notes) - 1 else episode_notes[ind + 1].pitch
            edited_pitch = MusicUtils.closest_pitch_to_neighbours_for_pitch_class(note.pitch, new_pitch_class, prev_pitch, next_pitch)
            if spec["focal_pitch"] is not None:
                edited_pitch = MusicUtils.map_pitch_to_focal_pitch(edited_pitch, spec["focal_pitch"])
            note.pitch = int(edited_pitch)  # transform from numpy.int64
            is_ok = DiscordancyUtils.discordancy_is_ok(composition, note, discordancy_avoid_spec, bar)
            if not is_ok:
                note.pitch = original_pitch
        return is_ok

    def get_seed_pitch_classes(self, spec, episode_notes, note):
        seed_length = spec["seed_length"]
        episode_pitch_classes = [MusicUtils.pitch_class(n.pitch) for n in episode_notes if n.pitch is not None and (n.tie_type is None or n.tie_type == "start")]
        seed_length = min(len(episode_pitch_classes), seed_length)
        ind = episode_notes.index(note)
        seed_pitch_classes = episode_pitch_classes[max(0, ind - seed_length):ind]
        num_missing = seed_length - len(seed_pitch_classes)
        if num_missing > 0:
            seed_pitch_classes = episode_pitch_classes[-num_missing:] + seed_pitch_classes
        return seed_pitch_classes

