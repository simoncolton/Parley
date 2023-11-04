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
        performance_spec = self.export_spec.get_value("performance_spec")
        soundfont_filepath = self.export_spec.get_value("soundfont_filepath")
        midi_file = MidiUtils.get_midi_file(composition, performance_spec, soundfont_filepath)
        output_stem = self.export_spec.get_value("output_stem")
        midi_filepath = output_stem + ".mid"
        midi_file.save(midi_filepath)
        audio_formats = self.export_spec.get_value("audio_formats")
        fluidsynth_cli = self.export_spec.get_value("fluidsynth_cli")
        if soundfont_filepath is not None:
            wav_filepath = output_stem + ".wav"
            if "WAV" in audio_formats or "MP3" in audio_formats:
                process = subprocess.Popen(f"{fluidsynth_cli} {soundfont_filepath} --quiet --no-shell {midi_filepath} -T wav -F {wav_filepath} > /dev/null", shell=True)
                process.wait()
            if "MP3" in audio_formats:
                mp3_filepath = output_stem + ".mp3"
                AudioSegment.from_wav(wav_filepath).export(mp3_filepath, format="mp3")
                if "WAV" not in audio_formats:
                    process = subprocess.Popen(f"rm {wav_filepath}", shell=True)
                    process.wait()
        return composition
