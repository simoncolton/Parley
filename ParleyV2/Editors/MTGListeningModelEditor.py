import copy
import random
import subprocess
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.MidiUtils import *
from ParleyV2.Utils.MusicUtils import *
from tqdm import tqdm

class MTGListeningModelEditor:

    def __init__(self, edit_spec):
      self.edit_spec = edit_spec

    def apply(self, start_composition):
      composition = copy.deepcopy(start_composition)

      # Here, pass the bars through the listening model to get the activations

      for ep_num in range(1, composition.num_episodes + 1):
          self.apply_to_episode(composition, ep_num)
      return composition

    def apply_to_episode(self, composition, ep_num):
        bars_in_episode = ExtractionUtils.get_bars_for_episode_num(composition, ep_num)

        # REMOVE THIS
        for bar in bars_in_episode:
            bar.mtg_activations_hash["mtg_jamendo_moodtheme__happy"] = random.uniform(0.1, 0.2)
            bar.mtg_activations_hash["mtg_jamendo_moodtheme__sad"] = random.uniform(0.1, 0.2)

        # TO HERE
        spec = self.edit_spec.instantiate_me(composition, bars_in_episode[0])
        target_tag = spec["target_tag"]
        num_bars_to_edit = spec["num_bars_per_episode"]
        num_trials = spec["num_hill_climb_trials_per_bar"]
        fixed_scale = spec["fixed_scale"]
        bars_to_edit = self.get_bars_to_edit(composition, bars_in_episode, target_tag, num_bars_to_edit)
        for bar in tqdm(bars_to_edit, desc=f"Listening to episode {bar.episode_num}"):
            self.edit_bar(composition, target_tag, num_trials, bar, fixed_scale)

    def get_bars_to_edit(self, composition, bars_in_episode, target_tag, num_bars_required):
        if num_bars_required >= len(bars_in_episode):
            return bars_in_episode
        # NEED TO USE LISTENING MODELS HERE TO IDENTIFY WORST BARS WRT TAG
        # DO NEED TO SORT THE BARS IN ORDER OF APPEARANCE
        bars_to_edit = random.sample(bars_in_episode, num_bars_required)
        bars_to_edit.sort(key=lambda x: x.bar_num)
        return bars_to_edit

    def edit_bar(self, composition, target_tag, num_trials, bar, fixed_scale):
        current_activation = bar.mtg_activations_hash[target_tag]
        trial_bars = []
        for trial_num in range(0, num_trials):
            trial_bars.append(self.get_altered_bar(composition, bar, target_tag, fixed_scale))
        trial_bars.sort(key=lambda x: x.mtg_activations_hash[target_tag])
        best_bar = trial_bars[-1]
        if best_bar.mtg_activations_hash[target_tag] > current_activation:
            composition.bars[best_bar.bar_num - 1] = best_bar
            composition.bars_hash[best_bar.bar_num] = best_bar

    def get_altered_bar(self, composition, original_bar, target_tag, fixed_scale):
        current_activation = original_bar.mtg_activations_hash[target_tag]
        altered_bar = copy.deepcopy(original_bar)
        track_num = self.edit_spec.get_value("track_num")
        note_sequence = [ns for ns in altered_bar.note_sequences if ns.track_num == track_num][0]
        note = random.choice(note_sequence.notes)
        original_pitch = note.pitch
        note.score_colour = "orange"
        while note.pitch == original_pitch or (fixed_scale is not None and not MusicUtils.note_is_in_scale(note.pitch, fixed_scale)):
            note.pitch = original_pitch + random.choice([i for i in range(-6, 6) if i != 0])
        new_activation = self.get_activation(composition, altered_bar, target_tag)
        altered_bar.mtg_activations_hash[target_tag] = new_activation
        # Hill climbing here
        if new_activation >= current_activation:
            return self.get_altered_bar(composition, altered_bar, target_tag, fixed_scale)
        else:
            return altered_bar

    def get_activation(self, composition, altered_bar, target_tag):
        copy_composition = copy.deepcopy(composition)
        copy_composition.bars[altered_bar.bar_num - 1] = altered_bar
        copy_composition.bars_hash[altered_bar.bar_num] = altered_bar
        performance_spec = self.edit_spec.get_value("performance_spec")
        soundfont_filepath = self.edit_spec.get_value("soundfont_filepath")
        fluidsynth_cli = self.edit_spec.get_value("fluidsynth_cli")
        ffmpeg_cli = self.edit_spec.get_value("ffmpeg_cli")
        temp_dir = self.edit_spec.get_value("temp_dir")
        abn = altered_bar.bar_num
        bar_nums = [abn] if abn == 0 else [abn-1, abn]
        midi_file = MidiUtils.get_midi_file(copy_composition, performance_spec, soundfont_filepath, bar_nums)
        r = f"{altered_bar.bar_num}_{random.randint(1, 1000)}"
        midi_filepath = f"{temp_dir}/{r}.mid"
        wav_filepath = f"{temp_dir}/{r}.wav"
        cropped_wav_filepath = f"{temp_dir}/{r}_cropped.wav"
        midi_file.save(midi_filepath)
        cmd = f"{fluidsynth_cli} {soundfont_filepath} --quiet --no-shell {midi_filepath} -T wav -F {wav_filepath} &> /dev/null"
        process = subprocess.Popen(cmd, shell=True)
        process.wait()
        start_s = 0 if len(bar_nums) == 1 else (composition.bars_hash[bar_nums[0]].duration_ticks/960)
        end_s = start_s + (altered_bar.duration_ticks/960)
        cmd = f"{ffmpeg_cli} -y -hide_banner -loglevel error -ss {start_s} -t {end_s - start_s} -i {wav_filepath} {cropped_wav_filepath} > /dev/null"
        process = subprocess.Popen(cmd, shell=True)
        process.wait()
        cmd = f"rm -f {midi_filepath}; rm -f {wav_filepath}"
        process = subprocess.Popen(cmd, shell=True)
        process.wait()
        return random.uniform(0.1, 0.2)