from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.MusicUtils import *
from ParleyV2.Utils.DiscordancyUtils import *
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.TimingUtils import *
import copy
import random


class HarmonisationEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        previous_pitch = None
        new_track_num = self.edit_spec.get_value("track_num")
        for bar in composition.bars:
            spec = self.edit_spec.instantiate_me(composition, bar)
            note_types = spec["note_types"]
            track_num_to_harmonise = spec["track_num_to_harmonise"]
            discordancy_avoid_spec = spec["discordancy_avoid"]
            pitch_range_low = spec["pitch_range_low"]
            pitch_range_high = spec["pitch_range_high"]
            notes = []
            NoteSequence.next_note_sequence_num += 1
            note_sequence = NoteSequence(note_sequence_num=NoteSequence.next_note_sequence_num,
                                         instrument_num=spec["instrument_num"], voice_id=spec["voice_id"],
                                         track_num=new_track_num, channel_num=spec["channel_num"],
                                         notes=notes, bar_num=bar.bar_num)
            bar.note_sequences.append(note_sequence)
            composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
            track_notes = [n.notes for n in bar.note_sequences if n.track_num == track_num_to_harmonise][0]
            for ind, note in enumerate(track_notes):
                repetition_allowed = (ind == 0 and spec["over_bar_repetition"]) or (ind > 0 and spec["in_bar_repetition"])
                new_note = self.get_harmony_note(composition, bar, note, previous_pitch, spec, repetition_allowed,
                                                 discordancy_avoid_spec, note_types, pitch_range_low, pitch_range_high,
                                                 note_sequence.note_sequence_num)
                notes.append(new_note)
                previous_pitch = new_note.pitch

        ind = 0
        new_track_notes = ExtractionUtils.get_notes_for_track_num(composition, new_track_num)
        while ind < len(new_track_notes):
            note = new_track_notes[ind]
            bar = composition.bars_hash[note.bar_num]
            spec = self.edit_spec.instantiate_me(composition, bar, note)
            if spec["keep_ties"] and note.tie_type == "start":
                pitch = note.pitch
                ind += 1
                note = new_track_notes[ind]
                while ind < len(new_track_notes) and note.tie_type is not None and note.tie_type != "start":
                    note.pitch = pitch
                    ind += 1
                    if ind < len(new_track_notes):
                        note = new_track_notes[ind]
                ind -= 1
            ind += 1

        return composition

    def get_harmony_note(self, composition, bar, note, previous_pitch, spec, repetition_allowed,
                         discordancy_avoid_spec, note_types, pitch_range_low, pitch_range_high,
                         note_sequence_num):

        new_note = copy.deepcopy(note)
        new_note.pitch = None
        new_note.note_sequence_num = note_sequence_num

        directly_preceding_notes = TimingUtils.get_directly_preceding_notes(new_note, 3, composition)
        directly_following_notes = TimingUtils.get_directly_following_notes(new_note, 3, composition)
        surrounding_notes = directly_preceding_notes + directly_following_notes

        if note.pitch is None:
            return new_note
        if note_types != "all" and note.note_type != note_types:
            return new_note

        intervals = spec["intervals_allowed"].copy()
        if spec["randomise_intervals"]:
            random.shuffle(intervals)

        for interval in intervals:
            is_ok = False
            new_pitch = note.pitch + interval
            new_pitch = MusicUtils.mapped_to_pitch_range(new_pitch, pitch_range_low, pitch_range_high)
            fixed_scale = spec["fixed_scale"]
            if fixed_scale is None or MusicUtils.note_is_in_scale(new_pitch, fixed_scale):
                if previous_pitch is None or repetition_allowed or new_pitch != previous_pitch:
                    new_note.pitch = new_pitch
                    is_ok = DiscordancyUtils.discordancy_is_ok(composition, new_note, discordancy_avoid_spec, bar)
                    if is_ok:
                        for snote in surrounding_notes:
                            if snote.pitch == new_pitch:
                                is_ok = False
            if not is_ok:
                new_note.pitch = None
            else:
                break
        if new_note.pitch is None and spec["map_to_scale"]:
            for interval in intervals:
                is_ok = False
                new_pitch = MusicUtils.map_to_scale(note.pitch + interval, fixed_scale)
                new_pitch = MusicUtils.mapped_to_pitch_range(new_pitch, pitch_range_low, pitch_range_high)
                if previous_pitch is None or repetition_allowed or new_pitch != previous_pitch:
                    new_note.pitch = new_pitch
                    is_ok = DiscordancyUtils.discordancy_is_ok(composition, new_note, discordancy_avoid_spec, bar)
                if not is_ok:
                    new_note.pitch = None
                else:
                    new_note.score_colour = "orange"
                    break

        return new_note
