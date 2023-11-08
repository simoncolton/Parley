from subprocess import Popen, PIPE


class VideoUtils:

    def get_ffmpeg_pipe(fps, ffmpeg_cli, output_file_path, codec):
        fps_s = f"{fps}"
#        parts = [ffmpeg_cli, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-r', fps_s, '-i', '-', '-vcodec', 'mpeg4',
#                   '-qscale', '5', '-r', fps_s, output_file_path]

        parts = [ffmpeg_cli, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-pix_fmt', 'yuv420p',
                 '-vcodec', 'mjpeg', '-r', fps_s, '-i', '-', '-vcodec', codec,
                 '-qscale', '5', '-r', fps_s, output_file_path]

        return Popen(parts, stdin=PIPE)

    def pass_to_ffmpeg_pipe(pipe, image):
        rgb_image = image.convert('RGB')
        rgb_image.save(pipe.stdin, 'JPEG')

    def close_pipe(pipe):
        pipe.stdin.close()
        pipe.wait()