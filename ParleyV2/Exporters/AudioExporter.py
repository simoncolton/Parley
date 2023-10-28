import copy
import subprocess

from mido import MidiFile, MidiTrack, Message
from ParleyV2.Utils.MidiUtils import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Utils.VolumeUtils import *
from pydub import AudioSegment
import time

class AudioExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        midi_file = MidiFile(type=1)
        performance_spec = self.export_spec.get_value("performance_spec")
        TimingUtils.add_midi_timings(composition, performance_spec)
        """
        if self.export_spec.get_value("single_bar_num_to_export") is not None:
            for bar in composition.bars:
                for ns in bar.note_sequences:
                    for note in ns.notes:
                        note.midi_timing.on_tick -= bar.start_tick
                        note.midi_timing.off_tick -= bar.start_tick
        """
        track_nums = ExtractionUtils.get_track_nums(composition)
        for track_num in track_nums:
            self.add_track(track_num, composition, midi_file)
        output_stem = self.export_spec.get_value("output_stem")
        midi_filepath = output_stem + ".mid"
        midi_file.save(midi_filepath)
        self.export_audio_formats(output_stem, midi_filepath)

        return composition

    def add_track(self, track_num, composition, midi_file):
        notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
        ordered_notes = [o for o in notes if o.midi_timing.duration_ticks > 0]
        tuples = []
        for note in ordered_notes:
            bar = composition.bars_hash[note.bar_num]
            on_tuple = (note.midi_timing.on_tick, "note_on", note)
            off_tuple = (note.midi_timing.off_tick, "note_off", note)
            tuples.extend([on_tuple, off_tuple])
        tuples.sort(key=lambda x: x[0])
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
            pitch = 10 if note.pitch is None else note.pitch
            soundfont_filepath = self.export_spec.get_value("soundfont_filepath")
            note_sequence = composition.note_sequences_hash[note.note_sequence_num]
            note_volume = VolumeUtils.adjust_volume_for_bad_soundfont(note, note_sequence, soundfont_filepath, msg_type)
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

        end_rest_ticks = self.export_spec.get_value("end_rest_ticks")
        if end_rest_ticks is not None and end_rest_ticks > 0:
            MidiUtils.add_rest_to_track(midi_track, 1, end_rest_ticks)

    def export_audio_formats(self, output_stem, midi_filepath):
        audio_formats = self.export_spec.get_value("audio_formats")
        soundfont_filepath = self.export_spec.get_value("soundfont_filepath")
        fluidsynth_cli = self.export_spec.get_value("fluidsynth_cli")
        if soundfont_filepath is not None:
            excerpt_length = self.export_spec.get_value("audio_excerpt_duration_s")
            wav_filepath = output_stem + ".wav"
            if "WAV" in audio_formats or "MP3" in audio_formats:
                process = subprocess.Popen(f"{fluidsynth_cli} {soundfont_filepath} --quiet --no-shell {midi_filepath} -T wav -F {wav_filepath} &> /dev/null", shell=True)
                process.wait()
            if "MP3" in audio_formats:
                #process doesn't seem to wait long enough for the WAV file to be written, so need to sleep
                time.sleep(1)
                mp3_filepath = output_stem + ".mp3"
                AudioSegment.from_wav(wav_filepath).export(mp3_filepath, format="mp3")
            if "WAV" not in audio_formats:
                process = subprocess.Popen("rm ./temp_delme.wav", shell=True)
                process.wait()
