import os
from mido import MidiFile, MidiTrack, Message
from ParleyV2.Utils.MathUtils import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.VolumeUtils import *


class MidiUtils:

    def play_midi_file(midi_filepath, soundfont_filepath):
        os.system(f"fluidsynth {soundfont_filepath} --quiet --no-shell {midi_filepath}")

    def get_note_on_message(channel, pitch, volume, time):
        return Message(type='note_on', channel=channel, note=pitch, velocity=MathUtils.clamp(volume, 0, 127), time=time)

    def get_note_off_message(channel, pitch, volume, time):
        return Message(type='note_off', channel=channel, note=pitch, velocity=MathUtils.clamp(volume, 0, 127), time=time)

    def note_on_message(channel, pitch, volume):
        return Message(type='note_on', channel=channel, note=pitch, velocity=MathUtils.clamp(volume, 0, 127), time=0)

    def note_off_message(channel, pitch, volume, duration):
        return Message(type='note_off', channel=channel, note=pitch, velocity=MathUtils.clamp(volume, 0, 127), time=duration)

    def add_note_to_track(track, channel, pitch, volume, duration):
        track.append(MidiUtils.note_on_message(channel, pitch, MathUtils.clamp(volume, 0, 127)))
        track.append(MidiUtils.note_off_message(channel, pitch, MathUtils.clamp(volume, 0, 127), duration))

    def add_rest_to_track(track, channel, duration):
        track.append(MidiUtils.note_on_message(channel, 60, 0))
        track.append(MidiUtils.note_off_message(channel, 60, 0, duration))

    def get_midi_file(composition, performance_spec, soundfont_filepath, bar_nums=None):
        midi_file = MidiFile(type=1)
        TimingUtils.add_midi_timings(composition, performance_spec)
        track_nums = ExtractionUtils.get_track_nums(composition)
        for track_num in track_nums:
            MidiUtils.add_track(track_num, composition, midi_file, soundfont_filepath, bar_nums)
        return midi_file

    def add_track(track_num, composition, midi_file, soundfont_filepath, bar_nums=None):
        notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
        ordered_notes = [o for o in notes if o.midi_timing.duration_ticks > 0]
        tuples = []
        for note in ordered_notes:
            bar = composition.bars_hash[note.bar_num]
            if bar_nums is None or bar.bar_num in bar_nums:
                on_tuple = [note.midi_timing.on_tick, "note_on", note]
                off_tuple = [note.midi_timing.off_tick, "note_off", note]
                tuples.extend([on_tuple, off_tuple])
        tuples.sort(key=lambda x: x[0])

        if bar_nums is not None:
            start_tick = tuples[0][0]
            for tuple in tuples:
                tuple[0] -= start_tick

        midi_track = MidiTrack()
        note_sequence = composition.note_sequences_hash[notes[0].note_sequence_num]
        instrument_num = note_sequence.instrument_num
        midi_track.append(Message('program_change', channel=note_sequence.channel_num,
                                   program=instrument_num, time=0))
        midi_file.tracks.append(midi_track)
        previous_tick = 0
        notes_on_hash = {}
        for ind, (tick, msg_type, note) in enumerate(tuples):
            note_sequence = composition.note_sequences_hash[note.note_sequence_num]
            old_instrument_num = instrument_num
            instrument_num = note_sequence.instrument_num
            if old_instrument_num != instrument_num:
                midi_track.append(Message('program_change', channel=note_sequence.channel_num, program=instrument_num, time=0))

            separation = tick - previous_tick
            pitch = 0 if note.pitch is None else note.pitch
            note_sequence = composition.note_sequences_hash[note.note_sequence_num]
            note_volume = VolumeUtils.adjust_volume_for_bad_soundfont(note, note_sequence, soundfont_filepath, msg_type)
            if pitch == 0:
                note_volume = 0
            if msg_type == "note_on":
                msg = MidiUtils.get_note_on_message(note_sequence.channel_num, pitch, note_volume, separation)
                notes_on_hash[pitch] = note.midi_timing.off_tick
            else:
                if pitch in notes_on_hash:
                    note_on_until = notes_on_hash[pitch]
                    if note_on_until > tick:
                        pitch = 0
                    else:
                        notes_on_hash.pop(pitch)
                msg = MidiUtils.get_note_off_message(note_sequence.channel_num, pitch, note_volume, separation)
            midi_track.append(msg)
            previous_tick = tick
        for p in notes_on_hash.keys():
            msg = MidiUtils.get_note_off_message(note_sequence.channel_num, p, 0, 0)
            midi_track.append(msg)
