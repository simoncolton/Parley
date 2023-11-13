from ParleyV2.Utils.EditingUtils import *
from ParleyV2.Utils.MTGListeningModelUtils import *
from tqdm import tqdm

class MTGListeningModelEditor:

    def __init__(self, edit_spec):
      self.edit_spec = edit_spec

    def apply(self, start_composition):
      composition = copy.deepcopy(start_composition)
      performance_spec = self.edit_spec.get_value("performance_spec")
      soundfont_filepath = self.edit_spec.get_value("soundfont_filepath")
      fluidsynth_cli = self.edit_spec.get_value("fluidsynth_cli")
      MTGListeningModelUtils.add_bar_activations(composition, performance_spec, soundfont_filepath, fluidsynth_cli)
      print("\n")
      for ep_num in range(1, composition.num_episodes + 1):
        self.apply_to_episode(composition, ep_num)
      return composition

    def apply_to_episode(self, composition, ep_num):
      bars_in_episode = ExtractionUtils.get_bars_for_episode_num(composition, ep_num)
      spec = self.edit_spec.instantiate_me(composition, bars_in_episode[0])
      target_tag = MTGListeningModelUtils.get_full_tag(spec["target_tag"])
      pc_bars_to_edit = int(spec["pc_bars_per_episode"])
      num_trials = int(spec["num_hill_climb_trials_per_bar"])
      fixed_scale = spec["fixed_scale"]
      bars_to_edit = self.get_bars_to_edit(composition, bars_in_episode, target_tag, pc_bars_to_edit)
      if len(bars_to_edit) > 0:
        ep_num = bars_to_edit[0].episode_num
        num_rounds = int(self.edit_spec.get_value("num_rounds"))
        for round in range(0, num_rounds):
          #print("\n================= Episode", ep_num, "Round", round + 1, "Bars", [b.bar_num for b in bars_to_edit], "target:", target_tag, "=================")
          for original_bar in tqdm(bars_to_edit, desc=f"Listening to episode {ep_num} (round {round + 1})", leave=False):
          #for original_bar in bars_to_edit:
            self.edit_bar(composition, target_tag, num_trials, original_bar, fixed_scale)

    def get_bars_to_edit(self, composition, bars_in_episode, target_tag, pc_bars_required):
      if pc_bars_required == 100:
          return bars_in_episode
      num_bars_required = int(len(bars_in_episode) * pc_bars_required/100)
      bars_to_edit = sorted(bars_in_episode, key=lambda x: x.mtg_activations_hash[target_tag], reverse=True)
      bars_to_edit = bars_to_edit[0:num_bars_required]
      bars_to_edit.sort(key=lambda x: x.bar_num)
      return bars_to_edit

    def edit_bar(self, composition, target_tag, num_trials, original_bar, fixed_scale):
      altered_bars = []
      change_details_used = []
      tries = 0
      while len(altered_bars) < num_trials and tries < (num_trials * 10):
        altered_bar = self.get_altered_bar(composition, original_bar, target_tag, fixed_scale)
        if altered_bar is not None:
          if altered_bar.pitch_change_info not in change_details_used:
            altered_bars.append(altered_bar)
            change_details_used.append(altered_bar.pitch_change_info)
        tries += 1
      bar_num = original_bar.bar_num
      if len(altered_bars) > 0:
        previous_bar = None if bar_num == 1 else composition.bars_hash[bar_num - 1]
        original_bar_copy = self.add_activations_to_bars(composition, previous_bar, original_bar, altered_bars)
        current_activation = original_bar_copy.mtg_activations_hash[target_tag]
        improved_bars = [a for a in altered_bars if a.mtg_activations_hash[target_tag] > current_activation]
        improved_bars.sort(key=lambda x: x.mtg_activations_hash[target_tag], reverse=True)
        global_mean = MTGListeningModelUtils.mtg_distribution[target_tag].mean
        #print("Bar:", bar_num, "Current activation:", f"{current_activation/global_mean:.4f}", "Better activations:", [f"{b.mtg_activations_hash[target_tag]/global_mean:.4f}" for b in improved_bars])
        if len(improved_bars) > 0:
          best_bar = improved_bars[0]
          new_activation = best_bar.mtg_activations_hash[target_tag]
          if new_activation > current_activation:
            pos = altered_bars.index(best_bar)
            self.change_composition(composition, original_bar, best_bar, target_tag)
      else:
        pass
        #print("Bar:", bar_num, "No alterations possible")

    def get_altered_bar(self, composition, original_bar, target_tag, fixed_scale, depth=1):
      altered_bar = copy.deepcopy(original_bar)
      track_num = self.edit_spec.get_value("track_num")
      discordancy_spec = self.edit_spec.get_value("discordancy_spec")
      allow_repetition = self.edit_spec.get_value("allow_repetition")
      note_sequence = [ns for ns in altered_bar.note_sequences if ns.track_num == track_num][0]
      notes_available = [n for n in note_sequence.notes if n.tie_type is None or n.tie_type == "start"]
      if len(notes_available) == 0:
        return None
      else:
        note = random.choice(notes_available)
        original_pitch = note.pitch
        new_pitches = [original_pitch + i for i in range(-6, 6) if i != 0]
        allowed_pitches = []
        for new_pitch in new_pitches:
          if EditingUtils.can_change_pitch(composition, note, new_pitch, allow_repetition, discordancy_spec, fixed_scale):
            allowed_pitches.append(new_pitch)
        if len(allowed_pitches) > 0:
          note.pitch = random.choice(allowed_pitches)
          note_num = note_sequence.notes.index(note)
          altered_bar.pitch_change_info = [(note_num, original_pitch, note.pitch)]
          return altered_bar
        else:
          return None

    def add_activations_to_bars(self, composition, previous_bar, original_bar, altered_bars):
      original_bar_copy = copy.deepcopy(original_bar)
      previous_bar_copy = copy.deepcopy(previous_bar) if previous_bar is not None else None

      # REMOVE THIS TO INCLUDE THE PREVIOUS BAR (SLOWER)
      previous_bar_copy = None

      all_bars = [original_bar_copy] + altered_bars
      performance_spec = self.edit_spec.get_value("performance_spec")
      soundfont_filepath = self.edit_spec.get_value("soundfont_filepath")
      fluidsynth_cli = self.edit_spec.get_value("fluidsynth_cli")
      excerpts_composition = EditingUtils.get_excerpts_composition(composition, previous_bar_copy, all_bars)
      MTGListeningModelUtils.add_bar_activations(excerpts_composition, performance_spec, soundfont_filepath, fluidsynth_cli)
      return original_bar_copy

    def change_composition(self, composition, original_bar, altered_bar, target_tag):
      original_bar.mtg_activation_vectors = altered_bar.mtg_activation_vectors
      original_bar.mtg_activations_hash = altered_bar.mtg_activations_hash
      track_num = self.edit_spec.get_value("track_num")
      short_tag = target_tag.split("__")[1]
      note_sequence = [n for n in original_bar.note_sequences if n.track_num == track_num][0]
      altered_note_sequence = [n for n in altered_bar.note_sequences if n.track_num == track_num][0]
      for (ind, _, new_pitch) in altered_bar.pitch_change_info:
        altered_note = altered_note_sequence.notes[ind]
        note_to_change = note_sequence.notes[ind]
        note_to_change.tags["listening edit improvement"] = "improvement"
        EditingUtils.change_note_pitch(composition, note_to_change, altered_note.pitch)
      comment = f"{short_tag} improvement"
      MarginUtils.add_margin_comment(original_bar, comment, "listening edit improvement")
