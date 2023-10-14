from Exporters.AudioExporter import *
from Specifications.ConstrainedSpecification import *
from tqdm import tqdm

class BarAudioExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec

    def apply(self, start_composition):
        output_stem = self.export_spec.get_value("output_stem")
        wav_filepath = output_stem + ".wav"
        for bar in tqdm(start_composition.bars, desc="Exporting bar WAVs"):
            start_s = bar.start_tick/960
            duration_s = bar.duration_ticks/960
            bar_wav_filepath = f"{output_stem}_{bar.bar_num}_{bar.pc_change}.wav"
            os.system(f"ffmpeg -y -ss {start_s} -i {wav_filepath} -t {duration_s} -hide_banner -c copy {bar_wav_filepath} &> /dev/null")
        os.system(f"zip {output_stem}_bars.zip {output_stem}_*_*.wav &> /dev/null")
        os.system(f"rm {output_stem}_*_*.wav")
        return start_composition
