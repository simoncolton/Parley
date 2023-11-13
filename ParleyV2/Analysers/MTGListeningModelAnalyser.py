import copy
from ParleyV2.Utils.EditingUtils import *
from ParleyV2.Utils.MTGListeningModelUtils import *


class MTGListeningModelAnalyser:

    def __init__(self, analysis_spec):
        self.analysis_spec = analysis_spec

    def apply(self, start_composition):
      composition = copy.deepcopy(start_composition)
      performance_spec = self.analysis_spec.get_value("performance_spec")
      soundfont_filepath = self.analysis_spec.get_value("soundfont_filepath")
      fluidsynth_cli = self.analysis_spec.get_value("fluidsynth_cli")
      MTGListeningModelUtils.add_bar_activations(composition, performance_spec, soundfont_filepath, fluidsynth_cli)
      self.add_local_tags(composition)
      self.add_global_tags(composition)
      return composition

    def add_local_tags(self, composition):
      tag_list = list(MTGListeningModelUtils.full_tag_hash.keys())
      full_tag = None
      pc_bars_to_tag = int(self.analysis_spec.get_value("pc_bars_to_tag"))
      num_bars_to_tag = int(len(composition.bars) * pc_bars_to_tag/100)
      bar_tags_hash = {}
      for tag in [t for t in tag_list if t != "none"]:
        full_tag = MTGListeningModelUtils.get_full_tag(tag)
        pairs = [(bar.mtg_activations_hash[full_tag], bar.bar_num) for bar in composition.bars]
        pairs.sort(reverse=True)
        for ind in range(0, num_bars_to_tag):
          bar_num = pairs[ind][1]
          if bar_num in bar_tags_hash:
            bar_tags_hash[bar_num].append(tag)
          else:
            bar_tags_hash[bar_num] = [tag]
      for bar_num in bar_tags_hash.keys():
        bar = composition.bars_hash[bar_num]
        comment = ""
        for tag in bar_tags_hash[bar_num]:
          comment += ", " + tag
        MarginUtils.add_margin_comment(bar, comment[2:], "bar listening tag")

    def add_global_tags(self, composition):
      for bar in composition.bars:
        bar.mtg_activation_highlights = []
      pc_bars_to_tag = int(self.analysis_spec.get_value("pc_bars_to_tag"))
      num_bars_to_highlight = int(len(composition.bars) * pc_bars_to_tag/100)
      if num_bars_to_highlight > 0:
        possible_bars_for_highlight = []
        for std_more in [4, 3.5, 3, 2.5, 2, 1.5, 1]:
          for ind, tag in enumerate(MTGListeningModelUtils.all_activation_tags):
            if "moodtheme" in tag:
              for bar in composition.bars:
                if bar.mtg_activations_hash[tag] >= MTGListeningModelUtils.mtg_distribution[tag].mean + (std_more * MTGListeningModelUtils.mtg_distribution[tag].std):
                  short_tag = tag.split("__")[1]
                  if short_tag not in bar.mtg_activation_highlights:
                    bar.mtg_activation_highlights.append(short_tag)
                  if bar not in possible_bars_for_highlight:
                    possible_bars_for_highlight.append(bar)
          if len(possible_bars_for_highlight) >= num_bars_to_highlight:
            random.shuffle(possible_bars_for_highlight)
            bars_to_highlight = possible_bars_for_highlight[0:num_bars_to_highlight]
            for bar in bars_to_highlight:
              comment = ""
              for highlight in bar.mtg_activation_highlights[0:3]:
                comment += ", " + highlight + "*"
              MarginUtils.append_margin_comment_to_existing(bar, comment[2:], "bar listening tag")
            break

        return composition
