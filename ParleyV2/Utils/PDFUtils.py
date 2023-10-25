from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LTLine
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from ParleyV2.Utils.MathUtils import *

class OnScoreBox:

    def __init__(self, page_num, x1, y1, x2, y2):
        self.page_num = page_num
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.height = self.y2 - self.y1
        self.width = self.x2 - self.x1
        self.is_line_start_box = False

    def get_line(self, prop, indent):
        dist = self.x2 - self.x1
        x = int(self.x1 + indent + (prop * (dist - indent)))
        return (x, self.y1), (x, self.y2)

    def score(self):
        score = self.page_num * 1000000
        score += self.y1 * 1000
        score += self.x1
        return score

    def scale_to_image(self, image):
        return self.scale_to_image_size(image.size)

    def scale_to_image_size(self, size):
        w = size[0]
        h = size[1]
        x1 = int(self.x1 * w)
        y1 = int(self.y1 * h)
        x2 = int(self.x2 * w)
        y2 = int(self.y2 * h)
        return OnScoreBox(self.page_num, x1, y1, x2, y2)

    def distance_to(self, other_line):
        d1 = MathUtils.euclidean_distance(self.x1, self.y1, other_line.x1, other_line.y1)
        d2 = MathUtils.euclidean_distance(self.x1, self.y1, other_line.x2, other_line.y2)
        d3 = MathUtils.euclidean_distance(self.x2, self.y2, other_line.x1, other_line.y1)
        d4 = MathUtils.euclidean_distance(self.x2, self.y2, other_line.x2, other_line.y2)
        return min([d1, d2, d3, d4])

    def is_lh_double_line_with(self, other_line):
        return self.y1 == other_line.y1 and self.x1 < other_line.x1 and (abs((other_line.x1 * 2048) - (self.x1 * 2048)) < 5)

    def should_join_to(self, other_line):
        if self.page_num != other_line.page_num:
            return False
        return (self.distance_to(other_line) * 2048) <= 0.01

    def joined_with(self, other_line):
        d = MathUtils.euclidean_distance(self.x1, self.y1, other_line.x1, other_line.y1)
        if (d * 2048) <= 0.1:
            return OnScoreBox(self.page_num, self.x2, self.y2, other_line.x2, other_line.y2)

        d = MathUtils.euclidean_distance(self.x1, self.y1, other_line.x2, other_line.y2)
        if (d * 2048) <= 0.1:
            return OnScoreBox(self.page_num, self.x2, self.y2, other_line.x1, other_line.y1)

        d = MathUtils.euclidean_distance(self.x2, self.y2, other_line.x1, other_line.y1)
        if (d * 2048) <= 0.1:
            return OnScoreBox(self.page_num, self.x1, self.y1, other_line.x2, other_line.y2)

        d = MathUtils.euclidean_distance(self.x2, self.y2, other_line.x2, other_line.y2)
        if (d * 2048) <= 0.1:
            return OnScoreBox(self.page_num, self.x1, self.y1, other_line.x1, other_line.y1)

        return None


class PDFUtils:

    def get_bar_lines(pdf_filepath):
        document = open(pdf_filepath, 'rb')
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        bar_lines = []
        stave_lines = []
        for page_ind, page in enumerate(PDFPage.get_pages(document)):
            w = page.mediabox[2]
            h = page.mediabox[3]
            interpreter.process_page(page)
            layout = device.get_result()
            for element in layout:
                if isinstance(element, LTLine):
                    line = OnScoreBox(page_ind, element.x0/w, 1 - element.y0/h, element.x1/w, 1 - element.y1/h)
                    if element.x0 == element.x1 and element.linewidth == 4.464:
                        bar_lines.append(line)
                    elif element.x0 == element.x1 and element.linewidth == 3.25:
                        bar_lines.append(line)
                    elif element.y0 == element.y1 and element.linewidth == 2.728:
                        stave_lines.append(line)
#        bar_lines = PDFUtils.remove_double_lines(bar_lines)

        joined_lines = PDFUtils.join_lines(bar_lines)
        while len(joined_lines) != len(bar_lines):
            bar_lines = joined_lines
            joined_lines = PDFUtils.join_lines(bar_lines)
        bar_lines.sort(key=lambda x: x.score())
        return bar_lines

    def get_bar_bounding_boxes(pdf_filepath):
        bar_lines = PDFUtils.get_bar_lines(pdf_filepath)
        bar_boxes = []
        start_line_x = min([b.x1 for b in bar_lines])
        for bar_ind in range(0, len(bar_lines) - 1):
            line1 = bar_lines[bar_ind]
            line2 = bar_lines[bar_ind + 1]
            if line1.page_num == line2.page_num and line1.x1 < line2.x1 and line1.y1 == line2.y1:
                min_y = min(line1.y1, line2.y1)
                max_y = max(line1.y2, line2.y2)
                bar_box = OnScoreBox(line1.page_num, line1.x1, min_y, line2.x2, max_y)
                bar_box.is_line_start_box = (line1.x1 == start_line_x) or bar_ind == 0
                bar_boxes.append(bar_box)

        return bar_boxes

    def remove_double_lines(lines):
        new_lines = []
        for line in lines:
            line.has_been_removed = False

        for ind1 in range(0, len(lines)):
            line1 = lines[ind1]
            if not line1.has_been_removed:
                for ind2 in range(ind1 + 1, len(lines)):
                    line2 = lines[ind2]
                    if line1.is_lh_double_line_with(line2):
                        line2.has_been_removed = True
                new_lines.append(line1)
        return new_lines

    def join_lines(lines):
        joined_lines = []
        for line in lines:
            line.has_been_joined = False
        for ind1 in range(0, len(lines)):
            line1 = lines[ind1]
            if not line1.has_been_joined:
                has_joined = False
                for ind2 in range(ind1 + 1, len(lines)):
                    line2 = lines[ind2]
                    if line1.should_join_to(line2):
                        joined_line = line1.joined_with(line2)
                        joined_lines.append(joined_line)
                        has_joined = True
                        line2.has_been_joined = True
                if not has_joined:
                    joined_lines.append(line1)
        return joined_lines
