from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.DiscordancyUtils import *
from ParleyV2.Utils.TimingUtils import *
from ParleyV2.Utils.MusicUtils import *
import copy


class EditingUtils:

    def can_change_pitch(composition, note, new_pitch, allow_repetition, discordance_spec, fixed_scale):
        bar = composition.bars_hash[note.bar_num]
        spec = discordance_spec.instantiate_me(composition, bar, note)
        original_pitch = note.pitch
        note.pitch = new_pitch
        if fixed_scale is not None and not MusicUtils.note_is_in_scale(new_pitch, fixed_scale):
            note.pitch = original_pitch
            return False
        if not DiscordancyUtils.discordancy_is_ok(composition, note, discordance_spec, bar):
            note.pitch = original_pitch
            return False
        if not allow_repetition:
            directly_preceding_notes = TimingUtils.get_directly_preceding_notes(note, 3, composition)
            directly_following_notes = TimingUtils.get_directly_following_notes(note, 3, composition)
            overlapping_notes = TimingUtils.get_overlapping_notes(note, composition)
            surrounding_notes = directly_preceding_notes + directly_following_notes + overlapping_notes
            reps = [s for s in surrounding_notes if s.pitch == note.pitch]
            if len(reps) > 0:
                note.pitch = original_pitch
                return False
        note.pitch = original_pitch
        return True

    def change_note_pitch(composition, note, new_pitch):
        note.pitch = new_pitch
        track_num = composition.note_sequences_hash[note.note_sequence_num].track_num
        if note.tie_type == "start":
            track_notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            tie_type = "x"
            if note in track_notes:
                ind = track_notes.index(note) + 1
                while tie_type != "start" and tie_type is not None and ind < len(track_notes):
                    track_notes[ind].pitch = note.pitch
                    track_notes[ind].score_colour = note.score_colour
                    tie_type = track_notes[ind].tie_type
                    ind += 1

    def get_excerpts_composition(self, composition, previous_bar, altered_bars):
      excerpts_composition = copy.deepcopy(composition)
      excerpts_composition.bars = []
      excerpts_composition.bars_hash = {}
      if previous_bar is not None:
        for note_sequence in previous_bar.note_sequences:
          if note_sequence.notes[0].tie_type == "mid":
            note_sequence.notes[0].tie_type = "start"
          if note_sequence.notes[0].tie_type == "end":
            note_sequence.notes[0].tie_type = None

      for ind, altered_bar in enumerate(altered_bars):
        for note_sequence in altered_bar.note_sequences:
          if previous_bar is None:
            if note_sequence.notes[0].tie_type == "mid":
              note_sequence.notes[0].tie_type = "start"
            if note_sequence.notes[0].tie_type == "end":
              note_sequence.notes[0].tie_type = None
          if note_sequence.notes[-1].tie_type == "mid":
            note_sequence.notes[-1].tie_type = "end"
          if note_sequence.notes[-1].tie_type == "start":
            note_sequence.notes[-1].tie_type = None
        if previous_bar is not None:
          excerpts_composition.bars.append(copy.deepcopy(previous_bar))
          excerpts_composition.bars.append(altered_bar)
        else:
          excerpts_composition.bars.append(altered_bar)
      tick = 0
      start64th = 0
      for ind, bar in enumerate(excerpts_composition.bars):
        bar.start64th = start64th
        bar.start_tick = tick
        bar.end_tick = tick + bar.duration_ticks
        bar.bar_num = ind + 1
        excerpts_composition.bars_hash[bar.bar_num] = bar
        for note_sequence in bar.note_sequences:
          note_sequence.bar_num = bar.bar_num
          for note in note_sequence.notes:
            note.bar_num = bar.bar_num
        tick += bar.duration_ticks
        start64th += 16
      return excerpts_composition




