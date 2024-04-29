import copy
import numpy as np
from ParleyV2.Utils.ExtractionUtils import *

class ExpressionAnalyser:

    def __init__(self, analysis_spec):
        self.analysis_spec = analysis_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        durations_hash = {}
        for track_num in ExtractionUtils.get_track_nums(composition):
            track_notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            for ind, note in enumerate(track_notes[0:-1]):
                key = note.timing.duration64ths if note.timing.tuplet_length is None else note.timing.duration64ths/note.timing.tuplet_length
                next_note = track_notes[ind + 1]
                note_ticks = next_note.midi_timing.on_tick - note.midi_timing.on_tick
                if key not in durations_hash:
                    durations_hash[key] = []
                durations_hash[key].append(note_ticks)
        averages_hash = {}
        stds_hash = {}
        for d in durations_hash.keys():
            if len(durations_hash[d]) > 0:
                averages_hash[d] = np.mean(durations_hash[d])
                stds_hash[d] = np.std(durations_hash[d])
        for track_num in ExtractionUtils.get_track_nums(composition):
            track_notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
            for ind, note in enumerate(track_notes[0:-1]):
                next_note = track_notes[ind + 1]
                note_ticks = next_note.midi_timing.on_tick - note.midi_timing.on_tick
                key = note.timing.duration64ths if note.timing.tuplet_length is None else note.timing.duration64ths/note.timing.tuplet_length
                av_note_ticks = averages_hash[key]
                diff = (note_ticks - av_note_ticks)/stds_hash[key]
                if diff >= 1:
                    note.tags["speed"] = "slow"
                if diff >= 2:
                    note.tags["speed"] = "very slow"
        return composition
