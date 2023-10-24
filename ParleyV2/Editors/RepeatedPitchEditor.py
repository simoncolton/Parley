import copy
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.TiedNotesUtils import *


class RepeatedPitchEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        track_num = self.edit_spec.get_value("track_num")
        notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
        ind = 0
        tuples = []
        while ind < len(notes):
            note = notes[ind]
            if note.pitch is not None:
                if len(tuples) == 0 or note.pitch != tuples[-1][0].pitch:
                    new_tuple = [note]
                    tuples.append(new_tuple)
                else:
                    tuples[-1].append(note)
            ind += 1
        tuples = [t for t in tuples if len(t) > 1]
        for tuple in tuples:
            bar = composition.bars_hash[tuple[0].bar_num]
            previous_repetition_style = None
            previous_note = None
            for note in tuple:
                spec = self.edit_spec.instantiate_me(composition, bar, note)
                repetition_style = spec["repetition"]
                is_last_note_in_tuple = (note == tuple[-1])
                if note.timing.start64th <= 4:
                    repetition_style = "tie"
                if previous_repetition_style is None:
                    if repetition_style == "leave":
                        pass
                    elif repetition_style == "staccato":
                        note.cutoff_prop = 0.5
                    elif repetition_style == "tie":
                        note.tie_type = "start"
                elif previous_repetition_style == "leave":
                    if repetition_style == "leave":
                        pass
                    elif repetition_style == "staccato":
                        note.cutoff_prop = 0.5
                    elif repetition_style == "tie" and not is_last_note_in_tuple:
                        note.tie_type = "start"
                elif previous_repetition_style == "staccato":
                    if repetition_style == "leave":
                        pass
                    elif repetition_style == "staccato":
                        note.cutoff_prop = 0.5
                    elif repetition_style == "tie" and not is_last_note_in_tuple:
                        note.tie_type = "start"
                elif previous_repetition_style == "tie":
                    if previous_note.tie_type == "start":
                        note.tie_type = "end"
                    elif previous_note.tie_type == "mid":
                        if repetition_style == "tie":
                            note.tie_type = "end"
                        elif repetition_style == "leave":
                            previous_note.tie_type = "end"
                        elif repetition_style == "staccato":
                            note.cutoff_prop = 0.5
                    elif previous_note.tie_type == "end":
                        if repetition_style == "tie":
                            previous_note.tie_type = "mid"
                            note.tie_type = "end"
                        elif repetition_style == "leave":
                            pass
                        elif repetition_style == "staccato":
                            note.cutoff_prop = 0.5
                previous_repetition_style = repetition_style
                previous_note = note

        TiedNotesUtils.simplify_tied_notes(composition, track_num)
        return composition
