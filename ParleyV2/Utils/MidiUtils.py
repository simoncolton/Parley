import os
from mido import MidiFile, MidiTrack, Message
from ParleyV2.Utils.MathUtils import *


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
