from IPython.display import Audio
from pdf2image import convert_from_path
import copy
from PIL import Image


class ColabDisplayCommunicator:

    def __init__(self, edit_spec):
        self.edit_spec = edit_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        print("\n" + self.edit_spec.get_value("text") + "\n")
        postfix = self.edit_spec.get_value("pdf_postfix")
        if postfix is not None:
          pdf_filepath = f"Outputs/flaneur_{composition.random_seed}_{postfix}.pdf"
          self.show_pdf(pdf_filepath)
          if self.edit_spec.get_value("show_mp3"):
            mp3_filepath = f"Outputs/flaneur_{composition.random_seed}_{postfix}.mp3"
            print("")
            display(Audio(mp3_filepath))
        return composition

    def show_pdf(self, pdf_filepath):
      frac = 10
      images = convert_from_path(pdf_filepath)
      im = images[0]
      s = (int(im.size[0]/10), int(im.size[1]/10))
      margin = 1
      total_margin = (2 * margin) + (margin * (len(images) - 1))
      wide_size = (s[0] * len(images) + total_margin, s[1] + (margin * 2))
      wide_image = Image.new('RGBA', wide_size, (200, 200, 200, 200))
      for ind, image in enumerate(images):
        small_image = image.resize(s, resample=Image.LANCZOS)
        box = (margin + ((small_image.size[0] + margin) * ind), margin)
        wide_image.paste(small_image, box)
      display(wide_image)
