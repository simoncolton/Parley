from ParleyV2.Specifications.ConstrainedSpecification import *


class TotalExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec
        self.output_stem = None

    def apply(self, composition):
        self.output_stem = self.export_spec.get_value("output_stem")
        params_list = self.export_spec.parameters.values()
        if self.export_spec.get_value("export_score"):
            ParameterisedSpecification(params_list, {"applier_class_name": "ScoreExporter"}).apply(composition)
        if self.export_spec.get_value("export_audio"):
            ParameterisedSpecification(params_list, {"applier_class_name": "AudioExporter"}).apply(composition)
        if self.export_spec.get_value("export_data"):
            ParameterisedSpecification(params_list, {"applier_class_name": "DataExporter"}).apply(composition)
        if self.export_spec.get_value("export_video"):
            ParameterisedSpecification(params_list, {"applier_class_name": "VideoExporter"}).apply(composition)
        if self.export_spec.get_value("export_bars_wav_zip"):
            ParameterisedSpecification(params_list, {"applier_class_name": "BarAudioExporter"}).apply(composition)
        return composition
