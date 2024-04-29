from PIL import Image, ImageDraw, ImageFont
from mido import MidiFile, MidiTrack, Message
import numpy as np
import subprocess
from ParleyV2.Utils.VideoUtils import *
import smoothfit

class PianorollCommunicator:

    def __init__(self, comm_spec):
        self.comm_spec = comm_spec

    def make_pianoroll_image(self, midi_filepath, img_width, img_height):
        midi = MidiFile(midi_filepath)
        total_time = sum([msg.time for msg in midi])
        max_pitch = max([msg.note for msg in midi if msg.type == "note_on"])
        min_pitch = min([msg.note for msg in midi if msg.type == "note_on"])
        above_midc = max_pitch - 60
        below_midc = 60 - min_pitch
        x = max(above_midc, below_midc)
        max_pitch = max(max_pitch, 60 + x)
        min_pitch = min(min_pitch, 60 - x)
        timestamp = 0
        pixels_per_second = img_width / total_time
        notes = []
        for msg in midi:
            timestamp += msg.time
            if msg.type == "note_on":
                if msg.velocity == 0:
                    for tuple in notes:
                        if tuple[0] == msg.note:
                            tuple.append(timestamp)
                            break
                else:
                    notes.insert(0, [msg.note, timestamp, msg.velocity])
        notes.reverse()
        for n in [n for n in notes if len(n) == 3]:
            n.append(n[1] + 5)
        img = Image.new("RGB", (img_width, img_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        num_pitches = max_pitch - min_pitch + 1
        band_height = int(img_height / num_pitches)
        y_up = int((img_height - (num_pitches * band_height)) / 2)
        y_up = 0
        for i in range(-1, num_pitches + 1):
            colour = (230, 230, 230, 255) if i % 2 == 0 else (250, 250, 250, 255)
            if min_pitch + i == 60:
                colour = (250, 100, 100, 255)
            y = int(img_height - ((i + 1) * band_height)) + int(band_height / 2) - y_up
            draw.line((0, y, img_width, y), colour, width=(int(band_height)))
        for tuple in notes:
            start_x = int(tuple[1] * pixels_per_second)
            end_x = int(tuple[3] * pixels_per_second)
            end_x = min(end_x, int(pixels_per_second * (total_time))) - 1
            if end_x == start_x:
                end_x = start_x + 1
            band_num = tuple[0] - min_pitch
            y = int(img_height - ((band_num + 1) * band_height)) + int(band_height / 2) - y_up
            line_coords = (start_x, y, end_x, y)
            c = int((100 - tuple[2])/100 * 200)
            self.draw_pianoroll_line(draw, line_coords, band_height, tuple[2])
        return img

    def draw_pianoroll_line(self, draw, line_coords, band_height, velocity):
        c = 255 - int(velocity * 3)
        for x in range(line_coords[0], line_coords[2] + 1):
            draw.line((x, line_coords[1], x + 1, line_coords[3]), (c, c, c + 40, 255), width=int(band_height))
            c += 7
            if c > 230:
                break


class TimelineCommunicator:

    def __init__(self, comm_spec):
        self.comm_spec = comm_spec

    def get_timeline_video(self, summaries_csv_filepath, csv_filepath, midi_filepath, mp3_filepath,
                           tags_to_plot, img_width, img_height, bottom_margin,
                           fps, mp4_filepath, temp_mp4_filepath):
        prc = PianorollCommunicator(None)
        half_height = int((img_height - bottom_margin)/2)
        pianoroll_image = prc.make_pianoroll_image(midi_filepath, img_width, half_height)
        mlmgc = MTGListeningModelGraphCommunicator(None)
        plot_image = mlmgc.get_graph_image(summaries_csv_filepath, csv_filepath, tags_to_plot, img_width, half_height)
        vis_image = Image.new("RGBA", (img_width, img_height), (255, 255, 255, 255))
        vis_image.paste(pianoroll_image, (0, int((img_height - bottom_margin)/2)))
        vis_image.paste(plot_image, (0, 0))
        midi = MidiFile(midi_filepath)
        total_time = sum([msg.time for msg in midi])
        num_frames = int(fps * total_time)
        x_move = (img_width + 4) / num_frames
        pipe = VideoUtils.get_ffmpeg_pipe(fps, "ffmpeg", temp_mp4_filepath)
        for frame_num in range(0, num_frames):
            x_pos = int(x_move * frame_num) - 2
            frame_img = Image.new("RGB", (img_width, img_height), (255, 255, 255, 255))
            frame_img.paste(vis_image)
            draw = ImageDraw.Draw(frame_img)
            draw.line((x_pos, 0, x_pos, img_height - bottom_margin), fill=(0, 0, 0, 255), width=2)
            VideoUtils.pass_to_ffmpeg_pipe(pipe, frame_img)
        VideoUtils.close_pipe(pipe)
        process = subprocess.Popen(
            f"ffmpeg -hide_banner -loglevel error -i {temp_mp4_filepath} -itsoffset 0 -i {mp3_filepath} -c:v copy -map 0:v -map 1:a -y {mp4_filepath}",
            shell=True)
        process.wait()
        subprocess.run(f"rm {temp_mp4_filepath}", shell=True)

stem = "large-abs-ft_jazz_1000_97"
midi_filepath = f"/Users/Simon/Dropbox/Code/PycharmProjects/Parley/experiments/aria_1000token_corpus/{stem}.mid"
summaries_csv_filepath = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/experiments/aria_final_corpus/summaries.csv"
csv_filepath = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/experiments/aria_final_corpus/large_ft_jazz_87.csv"
tags_to_plot = ["mtg_jamendo_genre__jazz", "mtg_jamendo_genre__classical"]
img_width = 600
img_height = 400
bottom_margin = 100
fps = 10
mp3_filepath = f"/Users/Simon/Dropbox/Code/PycharmProjects/Parley/experiments/aria_1000token_corpus/{stem}.mp3"
mp4_filepath = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/axx.mp4"
temp_mp4_filepath = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/temp.mp4"
tlc = TimelineCommunicator(None)
tlc.get_timeline_video(summaries_csv_filepath, csv_filepath, midi_filepath, mp3_filepath,
                       tags_to_plot, img_width, img_height, bottom_margin, fps, mp4_filepath,
                       temp_mp4_filepath)
