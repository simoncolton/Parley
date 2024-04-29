import copy
from ParleyV2.Utils.XMLUtils import *
from ParleyV2.Artefacts.Artefacts import *
from ParleyV2.Utils.ExtractionUtils import *


class LoadCompositionGenerator:

    def __init__(self, gen_spec):
        self.gen_spec = gen_spec

    def apply(self, start_composition):
        composition = Composition()
        file_path = self.gen_spec.get_value("file_path")
        doc = XMLUtils.open_xml_doc(file_path)
        composition_elem = doc.getElementsByTagName("composition")[0]
        self.set_attributes(composition, composition_elem)
        composition.episodes_hash = {}
        composition.chords_hash = {}
        composition.note_sequences_hash = {}
        composition.bars = []
        composition.bars_hash = {}
        for episode_elem in doc.getElementsByTagName("episode"):
            self.add_episode(composition, episode_elem)
        for chord_elem in doc.getElementsByTagName("chord"):
            self.add_chord(composition, chord_elem)
        for bar_elem in doc.getElementsByTagName("bar"):
            self.add_bar(composition, bar_elem)
        for note in ExtractionUtils.get_notes_in_composition(composition):
            note.tags = {}
        for bar in composition.bars:
            if bar.margin_comments == []:
                bar.margin_comments = None
        return composition

    def add_episode(self, composition, episode_elem):
        episode = Episode()
        self.set_attributes(episode, episode_elem)
        composition.episodes_hash[episode.episode_num] = episode

    def add_chord(self, composition, chord_elem):
        chord = Chord()
        self.set_attributes(chord, chord_elem)
        composition.chords_hash[chord.chord_num] = chord

    def add_bar(self, composition, bar_elem):
        bar = Bar()
        self.set_attributes(bar, bar_elem)
        bar.chords = []
        for chord_elem in bar_elem.getElementsByTagName("chord"):
            chord = Chord()
            self.set_attributes(chord, chord_elem)
            bar.chords.append(chord)
        bar.note_sequences = []
        for note_sequence_elem in bar_elem.getElementsByTagName("note_sequence"):
            note_sequence = self.get_note_sequence(note_sequence_elem)
            bar.note_sequences.append(note_sequence)
            composition.note_sequences_hash[note_sequence.note_sequence_num] = note_sequence
        bar.margin_comments = []
        for margin_comment_elem in bar_elem.getElementsByTagName("margin_comment"):
            margin_comment = MarginComment()
            self.set_attributes(margin_comment, margin_comment_elem)
            bar.margin_comments.append(margin_comment)
        composition.bars.append(bar)
        composition.bars_hash[bar.bar_num] = bar

    def get_note_sequence(self, note_sequence_elem):
        note_sequence = NoteSequence()
        note_sequence.notes = []
        self.set_attributes(note_sequence, note_sequence_elem)
        for note_elem in note_sequence_elem.getElementsByTagName("note"):
            note = Note()
            self.set_attributes(note, note_elem)
            note_sequence.notes.append(note)
        return note_sequence

    def set_attributes(self, artefact, elem):
        attributes = elem.attributes
        if attributes is not None:
            for i in range(0, attributes.length):
                attribute = attributes.item(i)
                artefact.__setattr__(attribute.name, self.get_typed_value(attribute.value))

    def get_typed_value(self, str_val):
        if str_val == 'None':
            return None
        try: return int(str_val)
        except: pass
        try: return float(str_val)
        except: pass
        if str_val == "True" or str_val == "False":
            return bool(str_val)
        if "list:" in str_val:
            l = []
            rhs = str_val.split(":")[1]
            if rhs != "":
                for v in rhs.split(","):
                    l.append(self.get_typed_value(v))
            return l
        if "timing:" in str_val and "midi_timing:" not in str_val:
            parts = str_val.split(":")[1].split(",")
            t = Timing(start64th=int(parts[0]), duration64ths=int(parts[1]))
            if parts[2] != "None":
                t.tuplet_duration64ths = int(parts[2])
            if parts[3] != "None":
                t.normal_notes = int(parts[3])
            if parts[4] != "None":
                t.tuplet_length = int(parts[4])
            if parts[5] != "None":
                t.tuplet_note_type = parts[5]
            if parts[6] != "None":
                t.tuplet_note_duration64ths = int(parts[6])
            return t

        if "midi_timing:" in str_val:
            parts = str_val.split(":")[1].split(",")
            mt = MidiTiming(int(parts[0]), int(parts[1]), int(parts[2]))
            return mt
        return str_val
