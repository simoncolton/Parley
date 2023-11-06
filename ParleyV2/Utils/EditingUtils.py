from ParleyV2.Utils.ExtractionUtils import *

class EditingUtils:

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
