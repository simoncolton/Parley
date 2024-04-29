import dataclasses
from dataclasses import asdict
from ParleyV2.Utils.XMLUtils import *
from ParleyV2.Artefacts.Artefacts import *
import copy


class DataExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec
        self.doc = None

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        output_stem = self.export_spec.get_value("output_stem")
        docu, root = XMLUtils.get_doc_and_root("composition", self.get_attributes(composition))
        self.doc = docu
        episodes_elem = XMLUtils.add_child(self.doc, root, "episodes")
        for key in composition.episodes_hash:
            XMLUtils.add_child(self.doc, episodes_elem, "episode", self.get_attributes(composition.episodes_hash[key]))
        if composition.chords_hash is not None:
            chords_elem = XMLUtils.add_child(self.doc, root, "chords")
            for key in composition.chords_hash.keys():
                XMLUtils.add_child(self.doc, chords_elem, "chord", self.get_attributes(composition.chords_hash[key]))
        self.add_xml(root, composition)
        doc_string = XMLUtils.prettify(self.doc)
        xml_filepath = f"{output_stem}.xml"
        f = open(xml_filepath, "w")
        f.write(doc_string)
        f.close()
        return composition

    def get_attributes(self, artefact):
        attributes_dict = {}
        if dataclasses.is_dataclass(artefact) or isinstance(artefact, dict):
            dictionary = artefact if not dataclasses.is_dataclass(artefact) else asdict(artefact)
            for key in dictionary.keys():
                val = dictionary[key]
                if isinstance(val, (str, int, float, bool)):
                    attributes_dict[key] = f"{val}"
                elif isinstance(val, list):
                    ground_list = self.get_ground_list(dictionary[key])
                    if ground_list is not None:
                        attributes_dict[key] = ground_list
                elif type(val).__name__ == "NoneType":
                    attributes_dict[key] = "None"
                elif isinstance(val, dict):
                    if "start64th" in val.keys():
                        attributes_dict[key] = self.get_timing_string(val)
                    if "on_tick" in val.keys():
                        attributes_dict[key] = self.get_midi_timing_string(val)
        return attributes_dict

    def get_timing_string(self, val):
        s = "timing:"
        s += str(val["start64th"])
        s += "," + str(val["duration64ths"])
        s += "," + str(val["tuplet_duration64ths"])
        s += "," + str(val["normal_notes"])
        s += "," + str(val["tuplet_length"])
        s += "," + str(val["tuplet_note_type"])
        s += "," + str(val["tuplet_note_duration64ths"])
        return s

    def get_midi_timing_string(self, val):
        s = "midi_timing:" + str(val["on_tick"])
        s += "," + str(val["duration_ticks"])
        s += "," + str(val["off_tick"])
        return s

    def add_xml(self, element, artefact):
        if dataclasses.is_dataclass(artefact) or isinstance(artefact, dict):
            dictionary = artefact if not dataclasses.is_dataclass(artefact) else asdict(artefact)
            for key in dictionary.keys():
                val = dictionary[key]
                if isinstance(val, list):
                    ground_list = self.get_ground_list(dictionary[key])
                    if ground_list is None:
                        list_el = XMLUtils.add_child(self.doc, element, child_name=key)
                        for sub_artefact in val:
                            e = XMLUtils.add_child(self.doc, list_el, child_name=key[0:-1], attributes_dict=self.get_attributes(sub_artefact))
                            self.add_xml(e, sub_artefact)

    def get_ground_list(self, l):
        ground_list = "list:"
        for val in l:
            if isinstance(val, (str, int, float, bool)):
                ground_list += f"{val},"
            else:
                return None
        if len(l) == 0:
            return "list:"
        return ground_list[0:-1]

