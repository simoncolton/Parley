from PIL import Image, ImageDraw, ImageFont

class MTGListeningModelGraphCommunicator:

    def __init__(self, comm_spec):
        self.comm_spec = comm_spec
        self.mins_hash = {}
        self.means_hash = {}
        self.maxes_hash = {}
        self.stds_hash = {}

    def get_temporal_vectors(self, csv_filepath, all_activation_tags, tags_to_plot):
        temporal_vectors = []
        with open(csv_filepath) as f:
            lines = [l.strip() for l in f.readlines()]
            for tag in tags_to_plot:
                temporal_vector = []
                pos = all_activation_tags.index(tag)
                vs = [float(l.split(",")[pos]) for l in lines[1:]]
                vs = [(v - self.means_hash[tag])/self.stds_hash[tag] for v in vs]
                temporal_vectors.append(vs)

        return temporal_vectors

    def load_summaries(self, summaries_csv_filepath, all_activation_tags):

        with open(summaries_csv_filepath) as f:
            lines = f.readlines()
            vals = [float(v) for v in lines[0].split(",")[1:]]
            for ind, tag in enumerate(all_activation_tags):
                self.mins_hash[tag] = vals[ind]
            vals = [float(v) for v in lines[1].split(",")[1:]]
            for ind, tag in enumerate(all_activation_tags):
                self.means_hash[tag] = vals[ind]
            vals = [float(v) for v in lines[2].split(",")[1:]]
            for ind, tag in enumerate(all_activation_tags):
                self.maxes_hash[tag] = vals[ind]
            vals = [float(v) for v in lines[3].split(",")[1:]]
            for ind, tag in enumerate(all_activation_tags):
                self.stds_hash[tag] = vals[ind]

    def get_graph_image(self, summaries_csv_filepath, csv_filepath, tags_to_plot, img_width, img_height):
        image = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(image, "RGBA")
        with open(csv_filepath) as f:
            all_activation_tags = [l.strip().split(",") for l in f.readlines()][0]
            self.load_summaries(summaries_csv_filepath, all_activation_tags)
            vs = self.get_temporal_vectors(csv_filepath, all_activation_tags, tags_to_plot)
        colours = [(50, 50, 200), (190, 190, 250), (0, 0, 255)]
        max_dist = 0
        for v in vs:
            max_dist = max(max_dist, max([abs(val) for val in v]))
        # font = ImageFont.truetype("LiberationMono-Regular", 12)
        font = ImageFont.truetype("Arial.ttf", 12)
        smoothed_vs = []
        for data in vs:
            basis, coeffs = smoothfit.fit1d(range(0, len(data)), data, 0, len(data), img_width - 1, degree=1, lmbda=5.0e-2)
            smoothed_vs.append(coeffs)

        for i in range(-10, 10):
            y = img_height/2 - (i/max_dist * img_height * 0.45)
            if 5 < y < img_height - 5:
                if i == 0:
                    draw.line((0, y, img_width, y), (200, 200, 200), 1)
                else:
                    draw.line((0, y, img_width, y), (240, 240, 240), 1)
                draw.text((20, y), f"{i}", font=font, fill=(50, 50, 50, 255), anchor="mm")
        for colour_ind, ma_vec in enumerate(smoothed_vs):
            for ind in range(0, len(ma_vec)-1):
                x1 = int(img_width * ind/(len(ma_vec) - 1))
                x2 = int(img_width * (ind + 1)/(len(ma_vec) - 1))
                y1 = int(img_height/2 - (ma_vec[ind]/max_dist * img_height * 0.45))
                y2 = int(img_height/2 - (ma_vec[ind + 1]/max_dist * img_height * 0.45))
                draw.line((x1, y1, x2, y2), colours[colour_ind], 2)
        total_height = 0
        max_width = 0
        for ind, tag in enumerate([t.split("__")[1] for t in tags_to_plot]):
            bbox = draw.textbbox((10, 0), tag, font=font, anchor="lt")
            max_width = max(max_width, bbox[2])
            total_height += bbox[3]
        y_add = int(total_height/len(tags_to_plot))
        bx = img_width - max_width - 10
        draw.rectangle((bx, 5, bx+max_width, 15 + total_height), fill=(255, 255, 255, 255), outline="gray")
        for ind, tag in enumerate([t.split("__")[1] for t in tags_to_plot]):
            draw.text((img_width - max_width - 5, 10 + y_add * ind), tag, font=font, fill=colours[ind], anchor="lt")
        return image
