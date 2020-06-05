import subprocess
import os
import time


def remove_quotes(input_path: str):
    result = input_path
    if result.startswith('"'):
        result = result[1:]
    if result.endswith('"'):
        result = result[:-1]
    return result


def check_path(input_path: str):
    result = input_path
    if not result.startswith('"'):
        result = '"' + result
    if not result.endswith('"'):
        result += '"'
    return result


def wait_for_ffmpeg(file_path: str):
    while True:
        time.sleep(1)
        out = probe_info(file_path)
        if out is None:
            print('ERROR found by probe_info(' + file_path + ')')
            return
        elif len(out) > 10:
            print('rendered ' + file_path + ' out: ' + out)
            return


def probe_info(file_name: str):
    command_list = ['ffprobe', '-show_format', '-pretty', '-loglevel', 'quiet', remove_quotes(file_name)]
    p = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print("========= error ========")
        print(err)
        return None
    else:
        return str(out)


def delete_video(file: str):
    if os.path.exists(file):
        print('delete file ' + file)
        os.remove(file)
        print(file + 'deleted')


def trim_video(input_file: str, start: float, end: float, output_file: str, frame_accurate_trimming=False,
               change_resolution_to=None, change_fps_to=None):
    trim_start_time = min(start, end)
    trim_duration = abs(end - start)

    # delete existing output file
    delete_video(output_file)

    if change_resolution_to is not None:
        if change_fps_to is not None:
            resolution_command = '"'
        else:
            resolution_command = ""
        resolution_command += "scale=" + str(change_resolution_to[0]) + ":" + str(change_resolution_to[1])
        if change_fps_to is not None:
            resolution_command += ","
        resolution_command += " "
    else:
        resolution_command = ""

    if change_fps_to is not None:
        fps_command = "fps=fps=" + str(change_fps_to)
        if change_resolution_to is not None:
            fps_command += '"'
        fps_command += " "
    else:
        fps_command = ""

    if change_resolution_to is not None or change_fps_to is not None:
        pre_command = "-vf "
    else:
        pre_command = ""

    if frame_accurate_trimming:
        command = "ffmpeg -i " + check_path(input_file) + " -ss " + str(trim_start_time) + " -strict -2 -t " + str(
            trim_duration) + " " + check_path(output_file)
    else:
        """
        command = "ffmpeg -ss " + str(trim_start_time) + " -i " + input_file + " -c copy -t " + str(
            trim_duration) + " " + pre_command + resolution_command + fps_command + output_file
        """
        command = "ffmpeg -ss " + str(trim_start_time) + " -i " + check_path(input_file) + " -c copy -t " + str(
            trim_duration) + " " + check_path(output_file)
    print(command)
    os.popen(command)

    wait_for_ffmpeg(output_file)

    return None, None


def concat_videos(input_files: [], output_file: str):
    # delete existing output file (if existing)
    delete_video(output_file)

    p = os.path.join(os.getcwd(), "video_temp")
    if not os.path.exists(p):
        os.makedirs(p)
    video_list_file = os.path.join("video_temp", "list.txt")
    p = os.path.join(os.getcwd(), video_list_file)
    if os.path.exists(p):
        os.remove(p)

    # create file with list of videos
    with open(video_list_file, "w+") as f:
        text = ""
        for video_index, video in enumerate(input_files):
            new_line = "file '" + video + "'"
            if video_index == 0:
                text += new_line
            else:
                text += '\n' + new_line
        f.write(text)

    # join videos
    command = "ffmpeg -safe 0 -f concat -i " + check_path(video_list_file) + " -c copy " + check_path(output_file)
    print("command: " + command)
    os.popen(command)

    # wait until finished
    wait_for_ffmpeg(output_file)
    print("=== " + "concat of " + str(len(input_files)) + " clips completed" + " ===")


# https://stackoverflow.com/questions/42747935/cut-multiple-videos-and-merge-with-ffmpeg
# https://superuser.com/questions/459313/how-to-cut-at-exact-frames-using-ffmpeg
def trim_and_merge_video(input_file: str, sequences: [tuple], output_file: str, change_resolution_to=None,
                         change_fps_to=None):
    if len(sequences) > 0:
        temp_clips_list = []
        for index, item in enumerate(sequences):
            temp_file_name = "clip" + str(index) + ".mp4"
            p = os.path.join(os.getcwd(), "video_temp", temp_file_name)
            trim_video(input_file, item[0], item[1], p, False, change_resolution_to, change_fps_to)
            temp_clips_list.append(p)
        concat_videos(temp_clips_list, output_file)


def delete_temp_files():
    if not os.path.exists("video_temp"):
        os.makedirs("video_temp")
    files = []
    for root, dirs, files in os.walk("video_temp"):
        files.extend(files)
    if len(files) == 0:
        return None
    for f in list(set(files)):
        path = os.path.join("video_temp", f)
        os.remove(path)


def video_editing_test():
    import time
    start_time = time.time()
    seq_list = [(0, 8), (18, 38), (8, 18), (3, 9), (2, 4)]
    # seq_list = [(0, 2)]
    test_name = r"E:\DBV\AnalyseBallwechseldauer\Videos Leon\MS_WEISSKIRCHEN Max GER vs POPOV Christo " \
                r"FRA_2019 Scottish Open.mp4"
    # trim_and_merge_video('"' + test_name + '"', seq_list, "output_clip.mp4", (1600, 900), 10)
    for index, seq in enumerate(seq_list):
        trim_video(test_name, seq[0], seq[1], "output_" + str(index) + ".mp4", frame_accurate_trimming=True)
    # os.startfile("output_clip.mp4")
    # old: 24.42880415916443
    print(time.time() - start_time)


delete_temp_files()
# video_editing_test()
