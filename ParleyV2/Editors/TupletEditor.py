import copy
from ParleyV2.Utils.ExtractionUtils import *
from ParleyV2.Utils.MarginUtils import *


class TupletEditor:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        track_num = self.edit_spec.get_value("track_num")
        notes = ExtractionUtils.get_notes_for_track_num(composition, track_num)
        for pair in self.edit_spec.get_value("tuplets_sought").split(";"):
            tuplet_size = pair.split(":")[0]
            range64ths = pair.split(":")[1]
            self.handle_tuplets(composition, notes, int(tuplet_size), int(range64ths))
        return composition

    def handle_tuplets(self, composition, notes, tuplet_size, range64ths):
        for ind in range(0, len(notes) - tuplet_size):
            duration64ths = 0
            start_note = notes[ind]
            if start_note.timing.start64th % range64ths == 0 and start_note.tie_type is None and start_note.timing.tuplet_length is None:
                tuplet = []
                is_ok = True
                for i in range(0, tuplet_size):
                    if notes[ind + i].tie_type is not None:
                        is_ok = False
                    duration64ths += notes[ind + i].timing.duration64ths
                    tuplet.append(notes[ind + i])
                if is_ok and duration64ths == range64ths:
                    for note in tuplet:
                        note.timing.tuplet_duration64ths = duration64ths
                        note.timing.tuplet_length = len(tuplet)
                        note.timing.normal_notes = 4 if len(tuplet) == 6 else 2
                        note.timing.tuplet_note_duration64ths = int(duration64ths / note.timing.normal_notes)
                    tuplet[0].timing.tuplet_note_type = "start"
                    tuplet[-1].timing.tuplet_note_type = "end"
                    lt = len(tuplet)
                    lt = lt - 1 if (lt % 2 == 1) else lt
                    mid_ind = int(round(lt/2))
                    tuplet[mid_ind].timing.tuplet_note_type = "mid"
