import copy

from PIL import ImageDraw, Image, ImageFont
from pdf2image import convert_from_path
from ParleyV2.Utils.PDFUtils import *
from ParleyV2.Utils.VideoUtils import *
from ParleyV2.Utils.MarginUtils import *
import os
from tqdm import tqdm
import subprocess
import time

class VideoExporter:

    def __init__(self, export_spec):
        self.export_spec = export_spec

    def apply(self, start_composition):
        composition = copy.deepcopy(start_composition)
        output_stem = self.export_spec.get_value("output_stem")
        temp_mp4_output_file_path = output_stem + "_temp.mp4"
        mp4_output_file_path = output_stem + ".mp4"
        mp3_filepath = f"{output_stem}.mp3"
        fps = self.export_spec.get_value("fps")
        ffmpeg_cli = self.export_spec.get_value("ffmpeg_cli")
        pipe = VideoUtils.get_ffmpeg_pipe(fps, ffmpeg_cli, temp_mp4_output_file_path)
        pdf_file_path = output_stem + ".pdf"
        bar_boxes = PDFUtils.get_bar_bounding_boxes(pdf_file_path)
        score_images = convert_from_path(pdf_file_path, dpi=self.export_spec.get_value("dpi"))
        page_width = score_images[0].size[0]
        page_height = score_images[0].size[1]
        score_height = sum([i.size[1] for i in score_images])
        sidebar_width = int(round(page_height * 0.5))
        last_bar_box = bar_boxes[-1].scale_to_image(score_images[-1])
        score_height = min(score_height, (last_bar_box.page_num * page_height) + last_bar_box.y2 + last_bar_box.height)
        score_height = int(round(score_height))
        long_score_image_size = (page_width, score_height)
        long_score_image = Image.new('RGBA', long_score_image_size)
        thumbnail_image = Image.new('RGBA', long_score_image_size)
        y = 0
        for score_image in score_images:
            long_score_image.paste(score_image, (0, y))
            thumbnail_image.paste(score_image, (0, y))
            y += score_image.size[1]
        mult1 = page_height / thumbnail_image.size[1]
        mult2 = 1 / 5
        mult = min(mult1, mult2)
        thumb_size = (int(round(mult * thumbnail_image.size[0])), int(round(mult * thumbnail_image.size[1])))
        thumbnail_image.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        mult_diff = thumbnail_image.size[1] / thumb_size[1]
        thumb_size = thumbnail_image.size
        thumbnail_image.convert('RGBA')
        thumbnail_page_width = thumbnail_image.size[0]
        thumbnail_page_height = score_images[0].size[1] * mult * mult_diff
        thumbnail_page_size = (thumbnail_page_width, thumbnail_page_height)
        thumbnail_x_offset = int(round(thumbnail_page_width * 0.1))
        thumbnail_y_offset = int(round((page_height - thumb_size[1]) / 2))
        w, h = score_images[0].size
        w = (w // 2) * 2
        h = (h // 2) * 2
        image_width = w + thumbnail_x_offset + thumbnail_page_width + sidebar_width
        image_width = (image_width // 2) * 2
        image_size = (image_width, h)
        overall_frame_num = fps
        bar_ticks_so_far = 0
        bar_frames_so_far = 0
        bars = composition.bars
        y_offset = 0
        is_over_half = False
        composition_ticks = bars[-1].start_tick + bars[-1].duration_ticks
        performance_spec = self.export_spec.get_value("performance_spec")
        if performance_spec.get_value("end_sustain_pedal_beats") is not None:
            last_bar = composition.bars[-1]
            composition_ticks = last_bar.end_tick + int((last_bar.duration_ticks / 4) * performance_spec.get_value("end_sustain_pedal_beats"))
        composition_ms = (composition_ticks / 960) * 1000
        composition_frames = int(round((composition_ms / 1000) * fps))
        num_end_ms = self.export_spec.get_value("end_rest_ms")
        composition_frames += int(round((num_end_ms / 1000) * fps))
        pixels_to_move = score_height - page_height
        y_move_per_frame = 0
        image = Image.new('RGBA', image_size)
        image_context = ImageDraw.Draw(image, 'RGBA')
        image_rect = ((0, 0), image_size)
        image_context.rectangle(image_rect, fill="white")
        sidebar_image, overlaid_long_score_image, tagged_thumbnail_image = self.get_annotated_images(score_images,
                                                                                                     long_score_image,
                                                                                                     thumbnail_image,
                                                                                                     sidebar_width,
                                                                                                     bars, bar_boxes)
        long_score_image = overlaid_long_score_image
        thumbnail_image = tagged_thumbnail_image
        thumbnail_page_width = thumbnail_image.size[0]
        thumb_size = thumbnail_image.size

        for bar_ind in tqdm(range(0, len(composition.bars)), desc="Exporting video"):
            bar = composition.bars[bar_ind]
            bar_ticks_so_far += bar.duration_ticks
            bar_ms_so_far = (bar_ticks_so_far / 960) * 1000
            total_bar_frames_required = int(round((bar_ms_so_far / 1000) * fps))
            num_frames = total_bar_frames_required - bar_frames_so_far
            bar_frames_so_far += num_frames
            if bar_ind < len(bar_boxes):
                bar_box = bar_boxes[bar_ind]
                thumb_box = bar_box.scale_to_image_size(thumbnail_page_size)
                thumb_add = int(round(bar_box.page_num * thumbnail_page_height))
                thumb_rect = (thumb_box.x1, thumb_box.y1 + thumb_add), (thumb_box.x2, thumb_box.y2 + thumb_add)
                thumb_highlight_image = Image.new('RGBA', thumb_size, (0, 0, 0, 0))
                thumb_context = ImageDraw.Draw(thumb_highlight_image, 'RGBA')
                thumb_context.rectangle(thumb_rect, fill=(255, 0, 0, 125))
                composite_image = Image.alpha_composite(thumbnail_image, thumb_highlight_image)
                image.paste(composite_image, (thumbnail_x_offset, thumbnail_y_offset))
                page_y_move = page_height * bar_box.page_num
                for frame_num in range(0, num_frames):
                    indent_pc = 4 if bar_box.is_line_start_box else 0
                    indent_pc = 5.5 if bar_ind == 0 else indent_pc
                    indent = int(round(page_width * indent_pc / 100))
                    prop = frame_num / num_frames
                    line = bar_box.scale_to_image(score_image).get_line(prop, indent)
                    if not is_over_half and line[0][1] > page_height / 3:
                        is_over_half = True
                        num_frames_to_end = composition_frames - overall_frame_num
                        y_move_per_frame = (pixels_to_move + page_height / 2) / num_frames_to_end
                    image.paste(long_score_image, (thumbnail_x_offset + thumbnail_page_width, int(round(y_offset))))
                    sidebar_pos = (thumbnail_x_offset + thumbnail_page_width + page_width, int(round(y_offset)))
                    image.paste(sidebar_image, sidebar_pos)
                    if overall_frame_num == fps:
                        image.paste(thumbnail_image, (thumbnail_x_offset, thumbnail_y_offset))
                        for i in range(0, fps):
                            if self.export_spec.get_value("video_fade_in") == True:
                                fade_in_frame_image = self.get_fade_in_frame(i / fps, image)
                            else:
                                fade_in_frame_image = image
                            VideoUtils.pass_to_ffmpeg_pipe(pipe, fade_in_frame_image)
                        image.paste(composite_image, (thumbnail_x_offset, thumbnail_y_offset))
                    moved_line = \
                        (line[0][0] + thumbnail_x_offset + thumbnail_page_width, line[0][1] + y_offset + page_y_move),\
                        (line[1][0] + thumbnail_x_offset + thumbnail_page_width, line[1][1] + y_offset + page_y_move)
                    image_context.line(moved_line, fill="red", width=5)
                    VideoUtils.pass_to_ffmpeg_pipe(pipe, image)
                    if y_offset - y_move_per_frame + score_height > page_height:
                        y_offset -= y_move_per_frame
                    overall_frame_num += 1
        end_image = Image.new('RGBA', image_size)
        end_image_context = ImageDraw.Draw(end_image, 'RGBA')
        end_image_rect = ((0, 0), image_size)
        end_image_context.rectangle(end_image_rect, fill="white")
        end_image.paste(thumbnail_image, (thumbnail_x_offset, thumbnail_y_offset))
        end_image.paste(long_score_image, (thumbnail_x_offset + thumbnail_page_width, int(round(y_offset))))
        sidebar_pos = (thumbnail_x_offset + thumbnail_page_width + page_width, int(round(y_offset)))
        end_image.paste(sidebar_image, sidebar_pos)
        num_end_frames = (composition_frames - overall_frame_num) + fps
        for fn in range(0, num_end_frames):
            VideoUtils.pass_to_ffmpeg_pipe(pipe, end_image)
        VideoUtils.close_pipe(pipe)
        process = subprocess.Popen(f"ffmpeg -hide_banner -loglevel error -i {temp_mp4_output_file_path} -itsoffset 1 -i {mp3_filepath} -c:v copy -map 0:v -map 1:a -y {mp4_output_file_path}", shell=True)
        process.wait()
        subprocess.run(f"rm {temp_mp4_output_file_path}", shell=True)
        return composition

    def get_annotated_images(self, score_images, long_score_image, thumbnail_image, sidebar_width, bars, bar_boxes):
        font = ImageFont.truetype('Tahoma.ttf', 20)
        sidebar_height = long_score_image.size[1]
        sidebar_image = Image.new('RGBA', (sidebar_width, sidebar_height), (255, 255, 255, 255))
        sidebar_overlay_image = Image.new('RGBA', (sidebar_width, sidebar_height), (255, 255, 255, 0))
        sidebar_context = ImageDraw.Draw(sidebar_image)
        sidebar_overlay_context = ImageDraw.Draw(sidebar_overlay_image)
        overlaid_long_score_image = Image.new('RGBA', long_score_image.size, (255, 255, 255, 0))
        wide_thumbnail_size = (int(round(thumbnail_image.size[0] * 1.2)), thumbnail_image.size[1])
        wide_thumbnail_image = Image.new('RGBA', wide_thumbnail_size, (255, 255, 255, 255))
        wide_thumbnail_image.paste(thumbnail_image)
        overlay_thumbnail_image = Image.new('RGBA', wide_thumbnail_size, (255, 255, 255, 0))

        thumbnail_tag_x_pos = int(round(thumbnail_image.size[0] * 1.04))
        thumbnail_y_mult = thumbnail_image.size[1] / long_score_image.size[1]
        thumbnail_context = ImageDraw.Draw(overlay_thumbnail_image)
        long_score_context = ImageDraw.Draw(overlaid_long_score_image)
        colours = {"red": (255, 0, 0, 30), "green": (0, 255, 0, 30), "blue": (0, 0, 255, 30),
                   "grey": (100, 100, 100, 30), "brown": (205, 150, 84, 30), "yellow": (255, 255, 0),
                   "purple": (128, 0, 128), "orange": (255, 165, 0)}
        thumb_colours = {"red": (255, 0, 0, 100), "green": (0, 255, 0, 100), "blue": (0, 0, 255, 100),
                         "grey": (100, 100, 100, 100), "brown": (205, 150, 84, 100), "yellow": (255, 255, 0, 100),
                         "purple": (128, 0, 128, 100), "orange": (255, 165, 0, 100)}
        previous_bottom = 0
        bars_with_comments = [b for b in bars if b.margin_comments is not None and len(b.margin_comments) > 0]
        multi_comments_hash = {}
        ignore_comments = []
        for bar in bars_with_comments:
            for comment in bar.margin_comments:
                id = f"{bar.bar_num}_{comment.comment_text}"
                if id not in ignore_comments:
                    ind = bars_with_comments.index(bar) + 1
                    bar_set = [bar]
                    while ind < len(bars_with_comments):
                        bar2 = bars_with_comments[ind]
                        if bar_boxes[bar.bar_num - 1].y1 == bar_boxes[bar2.bar_num - 1].y1:
                            if MarginUtils.has_comment(bar2, comment.comment_text):
                                bar_set.append(bar2)
                            ind += 1
                        else:
                            break
                    if len(bar_set) > 1:
                        multi_comment = f"{bar_set[0].bar_num}"
                        for ind in range(1, len(bar_set) - 1):
                            multi_comment += f", {bar_set[ind].bar_num}"
                        multi_comment += f" and {bar_set[-1].bar_num}: {comment.comment_text}"
                        multi_comments_hash[id] = multi_comment
                        ignore_set = [f"{b.bar_num}_{comment.comment_text}" for b in bar_set if b != bar]
                        ignore_comments.extend(ignore_set)

        for bar in bars_with_comments:
            for sn in bar.margin_comments:
                fill = colours[sn.comment_colour]
                tag_fill = thumb_colours[sn.comment_colour]
                bar_box = bar_boxes[bar.bar_num - 1].scale_to_image(score_images[0])
                y = bar_box.y1 + (bar_box.page_num * score_images[0].size[1])
                y2 = bar_box.y2 + (bar_box.page_num * score_images[0].size[1])
                rect = ((bar_box.x1, y), (bar_box.x2, y2))
                long_score_context.rectangle(rect, fill)
                while y - 10 <= previous_bottom:
                    y += 1
                score_note = f"{bar.bar_num}: {sn.comment_text}"
                key = f"{bar.bar_num}_{sn.comment_text}"
                if key in multi_comments_hash:
                    score_note = multi_comments_hash[key]
                if key not in ignore_comments:
                    sidebar_context.text((50, y), score_note, font=font, fill=(0, 0, 0))
                    text_size = font.getsize(score_note)
                    box = ((45, y - 5), (50 + text_size[0] + 5, y + text_size[1] + 5))
                    sidebar_overlay_context.rectangle(box, fill=fill)
                    thumbnail_tag_y_pos = int(round(y * thumbnail_y_mult))
                    rad = int(round(text_size[1] * thumbnail_y_mult))

                    tag_box = ((thumbnail_tag_x_pos, thumbnail_tag_y_pos),
                               (thumbnail_tag_x_pos + (rad * 3), thumbnail_tag_y_pos + rad))
                    thumbnail_context.rectangle(tag_box, fill=tag_fill)
                    previous_bottom = y + text_size[1]
        final_sidebar_image = Image.alpha_composite(sidebar_image, sidebar_overlay_image)
        final_long_score_image = Image.alpha_composite(long_score_image, overlaid_long_score_image)
        final_tagged_thumbnail_image = Image.alpha_composite(wide_thumbnail_image, overlay_thumbnail_image)
        return final_sidebar_image, final_long_score_image, final_tagged_thumbnail_image

    def get_fade_in_frame(self, trans_prop, image):
        transparency = int(round((1 - (trans_prop * 2)) * 255))
        transparency = max(0, transparency)
        overlay_image = Image.new('RGBA', image.size, (255, 255, 255, transparency))
        return Image.alpha_composite(image, overlay_image)

