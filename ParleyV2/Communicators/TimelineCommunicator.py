from ParleyV2.Communicators.PianorollCommunicator import *
from ParleyV2.Communicators.MTGListeningModelGraphCommunicator import *
from PIL import Image, ImageDraw
from mido import MidiFile

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
