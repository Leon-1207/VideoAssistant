__author__ = "Leon"

from time import sleep
import os

import logging
LOG_FILENAME = 'video_assistant.log'
log_config_filename = "log_level_config.txt"
log_level = logging.ERROR
if not os.path.exists(log_config_filename):
    file = open(log_config_filename, "w+")
    file.close()
with open(log_config_filename, "r") as log_level_f:
    log_level_f_text = str(log_level_f.read()).lower().strip()
    if log_level_f_text == "debug":
        log_level = logging.DEBUG
    elif log_level_f_text == "info":
        log_level = logging.INFO
    elif log_level_f_text == "error":
        log_level = logging.ERROR
logging.basicConfig(filename=LOG_FILENAME, level=log_level)
del log_config_filename


# enables cProfile
profile_mode = False

# import standard libraries
try:
    import copy
    import pathlib
    import time
    import tkinter as tk
    from threading import Thread, Event
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename
    from tkinter.filedialog import asksaveasfilename
    logging.info("standard libraries imported")
except Exception as e:  # work on python 3.x
    logging.error('Failed to import standard libraries: ' + str(e))

if profile_mode:
    import cProfile

# import pillow
try:
    from PIL import ImageTk, Image, ImageDraw
except Exception as e:
    logging.error('Failed to import PIL: ' + str(e))

# import video_editing
try:
    import video_editing
except Exception as e:  # work on python 3.x
    logging.error('video_editing: error: ' + str(e))

# vlc
try:
    from ctypes import windll
    windll.kernel32.SetDllDirectoryW(None)
    print("from ctypes import windll loaded")
except Exception as e:  # work on python 3.x
    msg = 'ERROR: ' + str(e)
    logging.error(msg)
    print("ERROR", msg)

try:
    import vlc
    print("vlc loaded")
except FileNotFoundError:
    logging.error("VLC NOT FOUND")
    print("VLC NOT FOUND")


# COLORS
def _from_rgb(rgb):
    return "#%02x%02x%02x" % rgb


GREEN_2 = _from_rgb((80, 255, 0))
RED_2 = _from_rgb((255, 50, 0))
BACKGROUND = 'gray25'
TAG_COLORS = ['green2', 'deep sky blue', 'dark orange2', 'navy']
ACCEPT_GREEN = 'lawn green'
CANCEL_RED = 'firebrick2'

pr = None
flash_period = False
player = None
sequences = []
use_frame_accurate_trimming = True


def render_video(window):
    if window is not None:
        window.destroy()

    global player
    if player is None:
        return
    my_player = get_player()

    def get_sub_clips():
        local_result = {"A": [], "B": [], "C": [], "D": []}
        for local_s in sequences:
            local_s_type = local_s[2]
            if 1 <= local_s_type <= 4:
                tag_char = "ABCD"[local_s_type - 1]
                new_seq = local_s[0] / 1000, local_s[1] / 1000
                local_result[tag_char].append(new_seq)
        return local_result

    render_settings = my_player.render_settings
    input_file = my_player.video_path
    tag_string = "ABCD"
    seq_list = get_sub_clips()

    # resolution
    # fps
    # remove_audio
    # output_path
    # output_base_name
    # export_option
    # create_folder_structure

    if len(str(render_settings["output_base_name"]).strip()) < 1:
        render_settings["output_base_name"] = "untitled"
    base_output_path = render_settings["output_path"]
    if render_settings["create_folder_structure"]:
        base_output_path = os.path.join(base_output_path, render_settings["output_base_name"])
    if not os.path.exists(base_output_path):
        os.makedirs(base_output_path)

    # open "rendering video" window
    bar_border_width = 2
    bar_width = 400
    bar_height = 30
    bar_main_color = "white"
    bar_progress_color = "green"

    new_win = tk.Toplevel(bg=BACKGROUND, width=bar_width, padx=20, pady=20)  # Popup -> Toplevel()
    new_win.title('Rendering Video')
    new_win.iconbitmap("p_icon.ico")
    text_var = tk.StringVar()
    text_var_bar_2 = tk.StringVar()
    label = tk.Label(new_win, textvariable=text_var, bg=BACKGROUND, fg='white')
    label.grid(row=0, sticky="W")

    progress_bar_1 = tk.Canvas(new_win, width=bar_width, height=bar_height, bd=0, relief=tk.RIDGE,
                               highlightthickness=0, bg=BACKGROUND)
    # progress_bar_1.pack(side=tk.LEFT)
    progress_bar_1.grid(row=1, sticky="W")
    progress_bar_2 = None

    def update_progress_bar(input_bar: tk.Canvas, progress: float):
        canvas = input_bar

        if canvas is None:
            return None

        canvas.delete(tk.ALL)

        def round_rectangle(x1, y1, x2, y2, draw_progress=1, radius=25, left=True, **kwargs):
            if draw_progress <= 0 and left:
                return None
            if draw_progress >= 1 and not left:
                return None
            r = radius
            nonlocal canvas
            points = (
                x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
                x2, y2,
                x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r,
                x1, y1)
            if draw_progress < 1:
                val = (max(x1, x2) - min(x1, x2)) * draw_progress
                if left:
                    max_x = val
                    points = [p if i % 2 != 0 else min(max_x, p) for i, p in enumerate(points)]
                else:
                    min_x = val
                    points = [p if i % 2 != 0 else max(min_x, p) for i, p in enumerate(points)]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        round_rectangle(bar_border_width, bar_border_width, bar_width-2*bar_border_width,
                        bar_height-2*bar_border_width,
                        draw_progress=progress,
                        left=True,
                        radius=15,
                        fill=bar_progress_color,
                        width=bar_border_width,
                        outline=bar_main_color)
        round_rectangle(bar_border_width, bar_border_width, bar_width - 2 * bar_border_width,
                        bar_height - 2 * bar_border_width,
                        draw_progress=progress,
                        left=False,
                        radius=15,
                        fill=BACKGROUND,
                        width=bar_border_width,
                        outline=bar_main_color)

    update_progress_bar(progress_bar_1, progress=0)
    new_win.attributes("-topmost", True)
    new_win.update()

    for tag_index, tag in enumerate(tag_string):
        if render_settings["export_option"] == 0:
            video_text = "video"
        else:
            video_text = "videos"
        text_var.set("Rendering " + video_text + " for tag: " + str(tag) +
                     " (" + str(tag_index + 1) + "/" + str(len(tag_string)) + ")")
        update_progress_bar(progress_bar_1, progress=tag_index/len(tag_string))
        new_win.update()
        if render_settings["export_option"] == 0:
            # join clips to single video
            output_file_name = render_settings["output_base_name"] + "_" + my_player.get_tag_name_for_tag_char(tag) \
                               + ".mp4"
            output_path = os.path.join(base_output_path, output_file_name)
            video_editing.trim_and_merge_video(input_file, seq_list[tag], output_path, render_settings["resolution"],
                                               render_settings["fps"])
        else:
            # save small clips
            if progress_bar_2 is None:
                tk.Label(new_win, textvariable=text_var_bar_2, bg=BACKGROUND, fg='white').grid(row=2, sticky="W")
                progress_bar_2 = tk.Canvas(new_win, width=bar_width, height=bar_height, bd=0, relief=tk.RIDGE,
                                           highlightthickness=0, bg=BACKGROUND)
                progress_bar_2.grid(row=3, sticky="W")
                new_win.update()
            for seq_index, seq in enumerate(seq_list[tag]):
                text_var_bar_2.set("Creating clip " + str(seq_index + 1) + "/" + str(len(seq_list[tag])))
                update_progress_bar(progress_bar_2, progress=seq_index/len(seq_list[tag]))
                new_win.update()
                output_file_name = render_settings["output_base_name"] + "_" + \
                                   my_player.get_tag_name_for_tag_char(tag) + "_" + str(seq_index) + ".mp4"
                output_path = None
                if render_settings["create_folder_structure"]:
                    check_path = os.path.join(base_output_path, my_player.get_tag_name_for_tag_char(tag))
                    if not os.path.exists(check_path):
                        os.makedirs(check_path)
                    output_path = os.path.join(base_output_path, my_player.get_tag_name_for_tag_char(tag),
                                               output_file_name)
                if output_path is not None:
                    video_editing.trim_video(input_file, seq[0], seq[1], output_path, use_frame_accurate_trimming)
                    # render_settings["resolution"],
                    # render_settings["fps"])

        video_editing.delete_temp_files()

    update_progress_bar(progress_bar_1, 1)
    new_win.update()
    sleep(.75)
    for widget in new_win.winfo_children():
        widget.destroy()
    tk.Label(new_win, font='Helvetica 30 bold', text="Complete", bg=BACKGROUND, fg="green").pack()


def load_settings_and_render_video(variable_list: [], window):
    valid_settings = load_render_settings_from_variables(variable_list)
    if valid_settings is True:
        render_video(window)


def load_render_settings_from_variables(variable_list: []):
    # variables
    """
    resolution_vars = tk.StringVar(), tk.StringVar()
    fps_var = tk.StringVar()
    remove_audio_var = tk.BooleanVar()
    output_path_var = tk.StringVar()
    output_path_var.set("C:\\")
    output_base_name_var = tk.StringVar()
    output_base_name_var.set("unnamed")
    export_option_var = tk.IntVar()
    export_option_var.set(0)
    create_folder_structure_var = tk.BooleanVar()
    create_folder_structure_var.set(True)
    """
    # 0
    resolution = 0, 0
    var = variable_list[0]
    for index in range(2):
        old_value = var[index].get()
        new_value = ""
        for c in old_value:
            if c.isdigit():
                new_value += c
        if len(new_value) == 0:
            return False
        if index == 0:
            resolution = int(new_value), 0
        else:
            resolution = resolution[0], int(new_value)
    if min(resolution[0], resolution[1]) < 1:
        return False

    # 1
    fps = 0
    var = variable_list[1]
    old_value = var.get()
    new_value = ""
    dot_placed = False
    for c in old_value:
        if c.isdigit():
            new_value += c
        elif dot_placed is False and c == '.':
            dot_placed = True
            new_value += '.'
    if new_value.endswith('.'):
        new_value = new_value.replace('.', '')
    if new_value.startswith('.'):
        new_value = '0' + new_value
    if len(new_value) == 0:
        return False
    fps = float(new_value)
    if not fps > 0:
        return False

    # 2
    remove_audio: bool
    var = variable_list[2]
    remove_audio = var.get()

    # 3
    var = variable_list[3]
    output_path = var.get()
    if not os.path.exists(output_path):
        print("ERROR wrong output path")
        return False

    # 4
    var = variable_list[4]
    output_base_name = var.get()

    # 5
    var = variable_list[5]
    export_option = var.get()

    # 6
    var = variable_list[6]
    create_folder_structure = var.get()

    global player
    if player is None:
        return False

    player.save_render_settings(resolution, fps, remove_audio, output_path, output_base_name, export_option,
                                create_folder_structure)

    return True


def add_sequence(start: int, end: int, sequence_type: int):
    logging.debug("add_sequence")
    global sequences
    index = 0
    new_sequence = start, end, sequence_type
    print("new_sequence:", new_sequence)

    def get_seq_type(_t: int):
        for _s in sequences:
            if _s[0] <= _t <= _s[1]:
                return _s[2]
        return None

    def put_new_seq_in_list(_new_seq):
        for _index, _s in enumerate(sequences):
            if _s[0] >= end:
                sequences.insert(_index, _new_seq)
                return None
        if len(sequences) == 0:
            sequences.append(_new_seq)
        else:
            if sequences[0][0] < start:
                sequences.append(_new_seq)
            else:
                sequences.insert(0, _new_seq)

    global player
    if player is not None:
        if player.video_duration > 0:
            if len(sequences) > 0:
                seq_type_before_new_seq = get_seq_type(start - 1)
                seq_type_after_new_seq = get_seq_type(end + 1)
                new_seq_list = []
                for s in sequences:
                    new_seq_inside_seq = s[0] <= start and end <= s[1]
                    if start <= s[0] <= end or start <= s[1] <= end or new_seq_inside_seq:
                        # do not copy this sequence
                        pass
                    else:
                        new_seq_list.append(s)
                sequences = new_seq_list
                if len(sequences) == 0:
                    sequences.append(new_sequence)
                else:
                    put_new_seq_in_list(new_sequence)
                # fill empty gaps
                # gap before new sequence
                print(seq_type_before_new_seq, seq_type_after_new_seq)
                if seq_type_before_new_seq != -1:
                    new_seq_index = sequences.index(new_sequence)
                    if new_seq_index == 0:
                        gap_start = 0
                    else:
                        gap_start = sequences[new_seq_index - 1][1]
                    gap_end = start
                    gap_type = seq_type_before_new_seq
                    if gap_end > gap_start:
                        # length of t > 0
                        t = gap_start, gap_end, gap_type
                        sequences.insert(new_seq_index, t)
                # gap after new sequence
                if seq_type_after_new_seq != -1:
                    new_seq_index = sequences.index(new_sequence)
                    if new_seq_index == len(sequences) - 1:
                        gap_end = player.video_duration
                    else:
                        gap_end = sequences[new_seq_index + 1][0]
                    gap_start = end
                    gap_type = seq_type_after_new_seq
                    if gap_end > gap_start:
                        # length of t > 0
                        t = gap_start, gap_end, gap_type
                        if new_seq_index == len(sequences) - 1:
                            sequences.append(t)
                        else:
                            sequences.insert(new_seq_index + 1, t)
            else:
                # sequence list is empty
                sequences.append(new_sequence)

    # concat sequences
    index = 1
    while index < len(sequences):
        if sequences[index - 1][2] == sequences[index][2]:
            # same type --> concat
            s_start = sequences[index - 1][0]
            s_end = sequences[index][1]
            s_type = sequences[index][2]
            t = s_start, s_end, s_type
            sequences[index - 1] = t
            sequences.pop(index)
        else:
            index += 1

    update_sequence_image()
    if player is not None:
        player.render_sequences()


def old_add_sequence(start: int, end: int, sequence_type: int):
    logging.debug("add_sequence")
    global sequences
    index = 0
    new_sequence = start, end, sequence_type
    print("new_sequence:", new_sequence)
    if len(sequences) > 0:
        done = False
        new_sequence_added = False
        while index < len(sequences) and not done:
            s = sequences[index]
            s_start, s_end, s_type = s
            if s == new_sequence:
                index += 1
                if index == len(sequences):
                    done = True
            else:
                if s_start > end:
                    # done
                    done = True
                if s_end < start:
                    # do not need to care about this sequence
                    pass
                else:
                    if start <= s_start and s_end <= end:
                        # delete s
                        print("delete", index, s)
                        sequences.pop(index)
                    elif start > s_start and s_end >= end:
                        # split s --> s | new sequence | s
                        print("need to split sequence", s, "(s | new sequence | s)")
                        t = s_start, start, s_type
                        sequences[index] = t
                        t = end, s_end, s_type
                        if index + 1 == len(sequences):
                            sequences.append(new_sequence)
                            sequences.append(t)
                        else:
                            sequences.insert(index + 1, new_sequence)
                            sequences.insert(index + 2, t)
                        new_sequence_added = True
                        done = True
                    elif s_end >= start:
                        if start > s_start:
                            # length of s > 0
                            t = s_start, start, s_type
                            sequences[index] = t
                            if index + 1 == len(sequences):
                                sequences.append(new_sequence)
                            else:
                                sequences.insert(index + 1, new_sequence)
                        else:
                            print(s, new_sequence, (s_start, start, s_type), "length less 0")
                            sequences[index] = new_sequence
                        new_sequence_added = True
                    elif s_start <= end:
                        if s_end > end:
                            # length of s > 0
                            t = end, s_end, s_type
                            sequences[index] = t
                            sequences.insert(index, new_sequence)
                        else:
                            sequences[index] = new_sequence
                        new_sequence_added = True
                index += 1

        if not new_sequence_added:
            sequences.append(new_sequence)
    else:
        sequences.append(new_sequence)

    update_sequence_image()
    if player is not None:
        player.render_sequences()


def update_sequence_image():
    logging.debug("update_sequence_image()")
    global player, sequences
    if player is not None:
        player.draw_canvas.update()
        size_x = player.draw_canvas.winfo_width()
        rect_h = 50
        time_pixel_factor = size_x / max(1, player.video_duration)
        for seq in sequences:
            x1 = int(seq[0] * time_pixel_factor)
            x2 = int(seq[1] * time_pixel_factor)
            if seq[2] == 0:
                rect_c = 'red'
            else:
                rect_c = TAG_COLORS[seq[2] - 1]
            player.draw_canvas.create_rectangle(x1, 0, x2, rect_h, fill=rect_c, width=0)


def reset_sequences(video_length: int):
    print("reset_sequences()")
    logging.debug("reset_sequences()")
    global sequences
    sequences = []
    add_sequence(0, video_length, 0)
    update_sequence_image()
    global player
    if player is not None:
        player.render_sequences()


def check_saves_folder():
    p = os.getcwd().replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    p += "saved_data"
    if not os.path.exists(p):
        os.makedirs(p)


def save_data():
    check_saves_folder()
    p = os.getcwd().replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    p += "saved_data"
    fullname = asksaveasfilename(initialdir=p, title="Save data")

    # if canceled
    if fullname is None:
        return

    if not str(fullname).endswith(".txt"):
        fullname = str(fullname) + ".txt"
    with open(fullname, "w+") as f:
        f.write("")

    if os.path.isfile(fullname):
        dir_name = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        logging.debug("dir_name: " + str(dir_name) + "filename: " + str(filename))
        path = dir_name.replace("\\", "/")
        if not path.endswith("/"):
            path += "/"
        path += filename
        print(path)
        if os.path.exists(path):
            save_data_to_file(path)


def save_data_to_file(input_data_file: str):
    print("save_data_to_file", input_data_file)
    global sequences
    if sequences is None:
        return
    text = ""
    for s_index, s in enumerate(sequences):
        if s_index != 0:
            text += "\n"
        line = ""
        for element_index, element in enumerate(s):
            if element_index != 0:
                line += ";"
            line += str(element)
        text += line
    with open(input_data_file, "w") as f:
        f.write(text)


def load_data():
    check_saves_folder()
    p = os.getcwd().replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    p += "saved_data"
    fullname = askopenfilename(initialdir=p, title="choose your file",
                               filetypes=(("txt files", "*.txt"), ("all files", "*.*")))
    if os.path.isfile(fullname):
        dir_name = os.path.dirname(fullname)
        filename = os.path.basename(fullname)
        logging.debug("dir_name: " + str(dir_name) + "filename: " + str(filename))
        path = dir_name.replace("\\", "/")
        if not path.endswith("/"):
            path += "/"
        path += filename

        with open(path, "r") as f:
            load_sequence_data_from_text(f.read())


def load_sequence_data_from_text(input_text: str):
    global sequences

    convert_badminton_tool_data = input_text.__contains__(',')

    if convert_badminton_tool_data and player is not None:
        reset_sequences(player.video_duration)
        lines = input_text.replace(',', ';').splitlines()
        if lines.__contains__('-'):
            text_list = lines[:lines.index('-')]
        else:
            text_list = lines
        for line in text_list:
            v1, v2, v3 = line.split(';')[:3]
            if int(v3) == 0:
                new_t = 1
            else:
                mew_t = 0
            add_sequence(int(v1), int(v2), new_t)
    else:
        sequences = []
        for line in input_text.splitlines():
            v1, v2, v3 = line.split(';')
            new_seq = int(v1), int(v2), int(v3)
            sequences.append(new_seq)

    update_sequence_image()


class TtkTimer(Thread):
    """a class serving same function as wxTimer... but there may be better ways to do this
    """

    def __init__(self, callback, tick):
        Thread.__init__(self)
        self.callback = callback
        self.stopFlag = Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        global flash_period
        while not self.stopFlag.wait(self.tick):
            flash_period = not flash_period
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters


class Player(tk.Frame):
    """The main window has to deal with events.
    """

    def __init__(self, parent, title=None):
        tk.Frame.__init__(self, parent)

        # style
        # self.style = ttk.Style()

        self.draw_objects = []

        self.play_speed = 1
        self.parent = parent

        main_bg = None

        if title is None:
            title = "tk_vlc"
        self.parent.title(title)

        # Menu Bar
        #   Options Menu
        menu_bar = tk.Menu(self.parent)
        self.parent.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar)
        video_menu = tk.Menu(menu_bar)
        tag_menu = tk.Menu(menu_bar)
        video_menu.add_command(label="Open Video", underline=0, command=self.on_open)
        video_menu.add_command(label="Render Video", underline=0, command=self.on_render_video)
        video_menu.add_command(label="Render Settings", underline=0, command=self.on_open_render_settings)
        file_menu.add_command(label="Save Data", underline=2, command=save_data)
        file_menu.add_command(label="Load Data", underline=3, command=load_data)
        file_menu.add_command(label="Reset Data", underline=4, command=self.on_reset_data)
        file_menu.add_command(label="Exit", underline=5, command=_quit)
        tag_menu.add_command(label="Edit Tags", underline=0, command=self.on_edit_tags)
        tag_menu.add_command(label="Open Tagging Settings", underline=0, command=self.open_tagging_settings)
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Video", menu=video_menu)
        menu_bar.add_cascade(label="Tag", menu=tag_menu)

        self.marker_mode = -1  # -1: marking nothing, 0: pause, 1: rally
        self.marker_start_time = 0
        self.window_size_x = 750
        self.video_path = None
        self.tag_moment_interval_vars = tk.DoubleVar(value=-8), tk.DoubleVar(value=4)
        self.render_settings = None
        self.zoom_preview_start = None
        self.zoom_preview_end = None

        # The second panel holds controls
        self.player = None
        self.media = None
        self.play_pause_button_symbol = tk.StringVar()
        self.play_pause_button_symbol.set("c")
        self.play_pause_button_color = "green"
        self.video_duration = 0
        self.set_time_to = -1
        self.videopanel = ttk.Frame(self.parent)
        self.canvas = tk.Canvas(self.videopanel, bg=main_bg).pack(fill=tk.BOTH, expand=1)
        self.videopanel.pack(fill=tk.BOTH, expand=1)

        ctrlpanel = ttk.Frame(self.parent)
        self.go_back_button_15 = tk.Button(ctrlpanel, text="-15", fg="black", command=self.on_go_back_15)
        self.go_back_button_5 = tk.Button(ctrlpanel, text="-5", fg="black", command=self.on_go_back_5)
        self.go_back_button_1 = tk.Button(ctrlpanel, text="-1", fg="black", command=self.on_go_back_1)
        self.play_pause_button = tk.Button(ctrlpanel, text="test", fg="black", command=self.on_toggle_play_pause)
        self.go_back_button_15.pack(side=tk.LEFT, padx=5)
        self.go_back_button_5.pack(side=tk.LEFT, padx=5)
        self.go_back_button_1.pack(side=tk.LEFT, padx=5)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)

        self.speed_var = tk.DoubleVar()
        self.speed_slider = tk.Scale(ctrlpanel, variable=self.speed_var, command=self.speed_sel,
                                     from_=0, to=10, orient=tk.HORIZONTAL, length=600, digits=3, resolution=0.1)
        self.speed_slider.pack(side=tk.LEFT)
        self.tag_label_var = tk.StringVar()
        self.tag_label_var.set("-")
        self.tag_label = tk.Label(ctrlpanel, textvariable=self.tag_label_var, font='Helvetica 10 bold')
        self.tag_label.pack(side=tk.RIGHT)
        ctrlpanel.pack(side=tk.BOTTOM)

        # ctrlpanel2
        ctrlpanel2 = ttk.Frame(self.parent)
        self.scale_var = tk.DoubleVar()
        self.time_slider_last_val = ""
        self.time_slider = tk.Scale(ctrlpanel2, variable=self.scale_var, command=self.scale_sel,
                                    from_=0, to=1000, orient=tk.HORIZONTAL, length=500)
        self.time_slider.pack(side=tk.BOTTOM, fill=tk.X, expand=1)
        self.time_slider_last_update = time.time()
        ctrlpanel2.pack(side=tk.BOTTOM, fill=tk.X)

        # draw canvas
        self.draw_canvas = tk.Canvas(self.parent, width=500, height=20, bg=main_bg)
        self.draw_canvas.pack(side=tk.BOTTOM, fill=tk.X)
        self.draw_canvas.bind("<Enter>", self.on_mouse_enter_timeline)
        self.draw_canvas.bind("<Leave>", self.on_mouse_leave_timeline)
        self.zoom_preview = None

        # tags
        self.selected_tag_index = 0
        self.tag_name_var_list = []
        for num in range(4):
            new_var = tk.StringVar()
            new_var.set("")
            self.tag_name_var_list.append(new_var)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()

        self.timer = TtkTimer(self.OnTimer, 1)
        self.timer.start()
        self.parent.update()

        self.update_play_pause_button(False)

        # for windows, on_open does does this
        self.player.set_hwnd(self.get_handle())

        self.update_tag_label()

    def on_mouse_enter_timeline(self, event):
        if self.video_duration > 1:
            self.update_zoom_preview(event)
            self.draw_canvas.bind("<Motion>", self.update_zoom_preview)

    def on_mouse_leave_timeline(self, event):
        if self.zoom_preview is not None:
            # self.draw_canvas.unbind("<Motion>", self.update_zoom_preview)
            self.zoom_preview.destroy()
            self.zoom_preview = None
            self.zoom_preview_start = None
            self.zoom_preview_end = None
            self.render_sequences()

    def update_zoom_preview(self, event):
        print("event:", event)
        zoom_rect_width = 200
        zoom_rect_height = 20

        if self.zoom_preview is None:
            # create frame
            self.zoom_preview = tk.Canvas(self.parent, width=zoom_rect_width, height=zoom_rect_height,
                                          bg=BACKGROUND)
            self.zoom_preview.pack()

        # render preview
        def render_zoom_preview():
            nonlocal self, event
            self.zoom_preview: tk.Canvas
            preview_duration = 60 * 1000

            # self.zoom_preview.create_rectangle(0, 0, zoom_rect_width, zoom_rect_height, fill='yellow')

            vid_duration = self.video_duration
            if vid_duration < 1:
                return
            draw_canvas_width = self.draw_canvas.winfo_width()
            factor = vid_duration / draw_canvas_width

            event_time = event.x * factor
            print(event_time, draw_canvas_width)

            preview_start_time = event_time - preview_duration // 2
            preview_end_time = event_time + preview_duration // 2

            self.zoom_preview_start = preview_start_time
            self.zoom_preview_end = preview_end_time

            pixel_time_factor = zoom_rect_width / preview_duration

            for s in sequences:
                s_start, s_end, s_type = s
                if s_start > preview_end_time:
                    # finished
                    return
                elif s_end < preview_start_time:
                    # too early
                    pass
                else:
                    x0 = (max(preview_start_time, s_start) - preview_start_time) * pixel_time_factor
                    x1 = (min(preview_end_time, s_end) - preview_start_time) * pixel_time_factor
                    y0 = 0
                    y1 = zoom_rect_height
                    if s_type == 0:
                        rect_c = 'red'
                    else:
                        rect_c = TAG_COLORS[s_type - 1]
                    self.zoom_preview.create_rectangle(x0, y0, x1, y1, fill=rect_c, width=0)

        render_zoom_preview()

        x = event.x - zoom_rect_width / 2
        y = self.draw_canvas.winfo_y() - self.draw_canvas.winfo_height()
        self.zoom_preview.place(x=x, y=y)
        self.render_sequences()

    def get_video_data(self, data):
        if self.player is None:
            return None
        if self.player.get_media() is None:
            return None
        if data == 'fps':
            return float(self.player.get_fps())
        elif data == 'resolution':
            video_w = int(self.player.video_get_width())
            video_h = int(self.player.video_get_height())
            return video_w, video_h
        else:
            print('error: get_video_data: ask for wrong data type: ' + str(data))
            return None

    def get_video_fps(self):
        result = self.get_video_data('fps')
        if result is not None:
            return result
        return 0

    def get_video_resolution(self):
        result = self.get_video_data('resolution')
        if result is not None:
            return result
        return 0, 0

    def save_render_settings(self, resolution: tuple, fps: float, remove_audio: bool, output_path: str,
                             output_base_name: str, export_option: int, create_folder_structure: bool):
        self.render_settings = {
            "resolution": resolution,
            "fps": fps,
            "remove_audio": remove_audio,
            "output_path": output_path,
            "output_base_name": output_base_name,
            "export_option": export_option,
            "create_folder_structure": create_folder_structure
        }

    def load_default_render_settings(self):
        def get_default_output_path():
            check_saves_folder()
            program_path = os.getcwd()
            p = os.path.join(program_path, "saved_data")
            return str(p)

        self.save_render_settings(
            self.get_video_resolution(),
            self.get_video_fps(),
            False,
            get_default_output_path(),
            "unnamed",
            0,
            True
        )

    def on_open_render_settings(self):
        self.open_render_settings(False)

    def on_render_video(self):
        self.open_render_settings(True)

    def open_render_settings(self, render_option: bool):
        new_win = tk.Toplevel(bg=BACKGROUND)  # Popup -> Toplevel()
        new_win.iconbitmap("p_icon.ico")
        if render_option:
            win_title = 'Render video'
        else:
            win_title = 'Render settings'
        new_win.title(win_title)

        self.get_video_resolution()

        # free space
        free_side_space = 20
        free_top_space = 25

        # variables
        # create variables
        resolution_vars = tk.StringVar(), tk.StringVar()
        fps_var = tk.StringVar()
        remove_audio_var = tk.BooleanVar()
        output_path_var = tk.StringVar()
        output_base_name_var = tk.StringVar()
        export_option_var = tk.IntVar()
        create_folder_structure_var = tk.BooleanVar()

        # create list of all tk variables
        var_list = [
            resolution_vars,
            fps_var,
            remove_audio_var,
            output_path_var,
            output_base_name_var,
            export_option_var,
            create_folder_structure_var
        ]

        # set variable values
        if self.render_settings is None:
            # load default values
            self.load_default_render_settings()
        # set resolution value
        for res_var_index, res_var in enumerate(resolution_vars):
            res_var.set(self.render_settings["resolution"][res_var_index])
        # set other values
        for tk_var, value in zip(var_list, self.render_settings.values()):
            if type(tk_var) != tuple:
                var_type = type(tk_var.get())
                if var_type == bool:
                    converted_value = bool(value)
                elif var_type == int:
                    converted_value = int(value)
                elif var_type == str:
                    converted_value = str(value)
                else:
                    converted_value = float(value)
                tk_var.set(converted_value)

        def set_output_path():
            path = asksaveasfilename()
            if path is None:
                return
            path_split = os.path.split(path)
            if len(path_split) > 1:
                if os.path.exists(path_split[0]):
                    output_path_var.set(path_split[0])
                    output_base_name_var.set(path_split[1])

        def validate_number_entries(event):
            print(event)
            # resolution (int)
            for v in resolution_vars:
                old_value = v.get()
                new_value = ""
                for c in old_value:
                    if c.isdigit():
                        new_value += c
                v.set(new_value)
            # fps (float)
            old_value = fps_var.get()
            new_value = ""
            dot_placed = False
            for c in old_value:
                if c.isdigit():
                    new_value += c
                elif dot_placed is False and c == '.':
                    dot_placed = True
                    new_value += c
            if new_value.endswith('.'):
                new_value += '0'
            fps_var.set(new_value)

        # body
        main_body_size_x, main_body_size_y = free_side_space, free_top_space
        for index in range(9):
            line_size_y = 40
            line_size_x = 0
            line_frame = tk.Frame(new_win, bg=BACKGROUND)
            if index == 0:
                # output resolution
                wid = tk.Label(line_frame, text='Resolution: ', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                for item_index, item in enumerate(['Width', 'Height']):
                    # label
                    wid = tk.Label(line_frame, text=item, bg=BACKGROUND, fg='white')
                    wid.pack(side=tk.LEFT)
                    line_size_x += wid.winfo_reqwidth()
                    # entry
                    wid = tk.Entry(line_frame, width=6, textvariable=resolution_vars[item_index], state='disabled')
                    wid.pack(side=tk.LEFT)
                    line_size_x += wid.winfo_reqwidth()
                    wid.bind("<KeyRelease>", validate_number_entries)
            elif index == 1:
                # fps
                # label
                wid = tk.Label(line_frame, text='Framerate: ', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # entry
                wid = tk.Entry(line_frame, width=4, textvariable=fps_var, state='disabled')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                wid.bind("<KeyRelease>", validate_number_entries)
            elif index == 2:
                # remove audio
                # label
                """
                wid = tk.Label(line_frame, text='Remove audio: ', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # checkbox
                wid = tk.Checkbutton(line_frame, variable=remove_audio_var, activebackground=BACKGROUND, bg=BACKGROUND)
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                """
            elif index == 3:
                # free line
                pass
            elif index == 4:
                # output path
                # label
                wid = tk.Label(line_frame, text='Path: ', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # label (path)
                wid = tk.Label(line_frame, textvariable=output_path_var, bg='grey', fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # button
                wid = tk.Button(line_frame, text='Set', command=set_output_path)
                wid.pack(side=tk.LEFT, padx=5)
                line_size_x += wid.winfo_reqwidth()
            elif index == 5:
                # base name
                # label
                wid = tk.Label(line_frame, text='Base name: ', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # entry
                wid = tk.Entry(line_frame, width=12, textvariable=output_base_name_var)
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
            elif index == 6 or index == 7:
                # export option
                if index == 6:
                    val = 0
                    text = "Join clips of same tag"
                else:
                    val = 1
                    text = "Export clips separated"
                # radiobutton
                wid = tk.Radiobutton(line_frame, bg=BACKGROUND, activebackground=BACKGROUND, value=val,
                                     variable=export_option_var)
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # label
                wid = tk.Label(line_frame, text=text, bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
            elif index == 8:
                # create folder structure
                # label
                wid = tk.Label(line_frame, text='Create folder structure', bg=BACKGROUND, fg='white')
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
                # checkbox
                wid = tk.Checkbutton(line_frame, variable=create_folder_structure_var, activebackground=BACKGROUND,
                                     bg=BACKGROUND)
                wid.pack(side=tk.LEFT)
                line_size_x += wid.winfo_reqwidth()
            delta_y = line_size_y
            main_body_size_y += delta_y
            main_body_size_x = max(main_body_size_x, line_size_x + 2*free_side_space)
            line_frame.place(x=free_side_space, y=free_top_space + index * line_size_y)
        # create placeholder for main body
        tk.Frame(new_win, bg='blue').pack(padx=main_body_size_x // 2, pady=main_body_size_y // 2)

        # bottom buttons
        def back_and_apply():
            load_render_settings_from_variables(var_list)
            new_win.destroy()
        # back/ cancel button
        button_frame = tk.Frame(new_win, bg=BACKGROUND)
        if render_option:
            b_text = 'Cancel'
        else:
            b_text = 'Back'
        b = tk.Button(button_frame, text=b_text, command=back_and_apply, bg=CANCEL_RED)
        b.pack(side=tk.LEFT, padx=10, pady=10)
        # render button
        if render_option:
            b = tk.Button(button_frame, text='Render',
                          command=lambda: load_settings_and_render_video(var_list, new_win), bg=ACCEPT_GREEN)
            b.pack(side=tk.RIGHT, padx=10, pady=10)
        button_frame.pack(pady=20)

        new_win.transient(self.parent)  # Popup reduction impossible
        new_win.grab_set()  # Interaction with window impossible game
        self.parent.wait_window(new_win)

    def open_tagging_settings(self):
        # start
        new_win = tk.Toplevel(bg=BACKGROUND)  # Popup -> Toplevel()
        new_win.title('Tagging Settings')
        new_win.iconbitmap("p_icon.ico")

        # body
        emtpy_top_frame = tk.Frame(new_win, bg=BACKGROUND, height=10)
        emtpy_top_frame.pack(side=tk.TOP)

        tag_moment_interval_frame = tk.Frame(new_win, bg=BACKGROUND)
        label = tk.Label(tag_moment_interval_frame, text="Tag moment interval:")
        label.pack(side=tk.LEFT, padx=2)
        string_var_list = []
        for var_index in range(2):
            # create new string var to show and modify interval value
            str_var = tk.StringVar()

            # set str_var text to current value
            str_var.set(str(self.get_tag_moment_interval()[var_index]))

            entry = tk.Entry(tag_moment_interval_frame, textvariable=str_var, width=5)
            string_var_list.append(str_var)
            entry.pack(side=tk.LEFT, padx=2)

        reset_button = tk.Button(tag_moment_interval_frame, text="Reset",
                                 command=lambda: self.on_reset_tag_moment_interval_button(string_var_list))
        reset_button.pack(side=tk.LEFT, padx=2)

        tag_moment_interval_frame.pack(padx=25, pady=10)

        # back button
        b = tk.Button(new_win, text='Back', command=new_win.destroy)
        b.pack(padx=10, pady=10)

        # end
        new_win.transient(self.parent)  # Popup reduction impossible
        new_win.grab_set()  # Interaction with window impossible game
        self.parent.wait_window(new_win)

        # apply interval values
        value_list = []
        for var in string_var_list:
            value = float(var.get())
            value_list.append(value)
        self.set_tag_moment_interval(value_list[0], value_list[1])

    def on_reset_tag_moment_interval_button(self, var_list):
        self.reset_tag_moment_interval()
        number_values = self.get_tag_moment_interval()
        for var_index in range(2):
            number = number_values[var_index]
            new_text = str(number)
            var_list[var_index].set(new_text)

    def reset_tag_moment_interval(self):
        self.set_tag_moment_interval(-8, 4)

    def set_tag_moment_interval(self, input_start, input_end):
        var1, var2 = self.tag_moment_interval_vars
        var1.set(input_start)
        var2. set(input_end)

    def get_tag_moment_interval(self):
        var1, var2 = self.tag_moment_interval_vars
        return var1.get(), var2.get()

    def tag_moment(self):
        self.stop_marker()
        t = self.selected_tag_index + 1
        a, b = self.get_tag_moment_interval()
        c_time = self.get_real_time()
        start = int(min(a, b) * 1000) + c_time
        end = int(max(a, b) * 1000) + c_time
        if end - start >= 200:
            add_sequence(start, end, t)

    def update_tag_label(self):
        tag_char = "ABCD"[self.selected_tag_index]
        tag_name = self.get_tag_name()
        if len(tag_name) > 0:
            text_end = tag_name + ' (' + tag_char + ')'
        else:
            text_end = tag_char
        text = 'Selected Tag: ' + text_end
        self.tag_label_var.set(text)
        text_color = TAG_COLORS[self.selected_tag_index]
        self.tag_label.configure(fg=text_color)

    def get_tag_name_for_tag_char(self, tag_char):
        result = self.tag_name_var_list["ABCD".index(tag_char)].get()
        if len(result) > 0:
            return result
        else:
            return tag_char

    def get_tag_name(self):
        return self.tag_name_var_list[self.selected_tag_index].get()

    def select_tag(self, new_tag: str):
        old_val = "ABCD"[self.selected_tag_index], self.get_tag_name()
        self.selected_tag_index = "abcd".index(new_tag.lower())
        new_val = "ABCD"[self.selected_tag_index], self.get_tag_name()
        if old_val != new_val:
            print(old_val, '-->', new_val)
        self.update_tag_label()

    def on_edit_tags(self):
        new_win = tk.Toplevel(bg=BACKGROUND)  # Popup -> Toplevel()
        new_win.title('Edit Tags')
        new_win.iconbitmap("p_icon.ico")
        for index, c in enumerate("ABCD"):
            line_frame = tk.Frame(new_win)
            tk.Label(line_frame, text=c+":", fg=TAG_COLORS[index], font='Helvetica 10 bold', bg=BACKGROUND)\
                .pack(side=tk.LEFT)
            tk.Entry(line_frame, textvariable=self.tag_name_var_list[index]).pack(side=tk.RIGHT)
            line_frame.pack(padx=10, pady=10)
        tk.Button(new_win, text='Back', command=new_win.destroy).pack(padx=10, pady=10)
        new_win.transient(self.parent)  # Popup reduction impossible
        new_win.grab_set()  # Interaction with window impossible game
        self.parent.wait_window(new_win)
        self.update_tag_label()

    def is_typing(self):
        return str(self.focus_get()).strip() != '.'

    def on_return_pressed(self):
        self.master.focus()

    def on_reset_data(self):
        if self.player is not None:
            d = self.video_duration
        else:
            d = 0
        reset_sequences(d)

    def update_play_pause_button(self, forced_data=None):
        logging.debug("update_play_pause_button()")
        if self.player is not None:
            if forced_data is None:
                display_play_symbol = self.player.is_playing() == 1
            else:
                display_play_symbol = forced_data
            if display_play_symbol:
                self.play_pause_button.configure(text="▶", fg="green")
            else:
                self.play_pause_button.configure(text="II", fg="red")

    def on_toggle_play_pause(self):
        logging.debug("on_toggle_play_pause()")
        if self.player is not None:
            if self.player.is_playing() == 1:
                self.player.pause()
                self.update_play_pause_button(True)
            else:
                self.player.play()
                self.update_play_pause_button(False)
        else:
            self.update_play_pause_button()

    def on_go_back_15(self):
        self.go_t_back(15)

    def on_go_back_5(self):
        self.go_t_back(5)

    def on_go_back_1(self):
        self.go_t_back(1)

    def go_t_back(self, t_in_sec):
        logging.debug("on_go_back " + str(t_in_sec))
        self.stop_marker()
        current_time = self.get_real_time()
        new_time = max(0, int(current_time - t_in_sec * 1000))
        self.player.set_time(new_time)

    def toggle_mark_rally(self):
        logging.debug("toggle_mark_rally")
        if self.marker_mode > 0:
            self.stop_marker()
        else:
            self.start_rally()

    def toggle_mark_pause(self):
        logging.debug("toggle_mark_pause")
        if self.marker_mode == 0:
            self.stop_marker()
        else:
            self.start_pause()

    def start_rally(self):
        logging.debug("start_rally()")
        self.stop_marker()
        self.marker_start_time = self.get_real_time()
        self.marker_mode = self.selected_tag_index + 1

    def start_pause(self):
        logging.debug("start_pause()")
        self.stop_marker()
        self.marker_start_time = self.get_real_time()
        self.marker_mode = 0

    def stop_marker(self):
        logging.debug("stop_marker()")
        if self.marker_mode == -1:
            # marking nothing
            pass
            # do nothing
        elif self.marker_mode > -1:
            # marking rally
            time_val = self.get_real_time()
            if time_val > self.marker_start_time:
                add_sequence(self.marker_start_time, time_val, self.marker_mode)
            self.marker_mode = -1

    def cancel_marker(self):
        self.marker_mode = -1
        self.marker_start_time = self.get_real_time()
        self.render_sequences()

    def on_resize(self, event):
        # called after resize window
        new_val = int(event.width)
        self.window_size_x = new_val
        self.draw_canvas.config(width=new_val - 5, height=20)
        update_sequence_image()
        self.render_sequences()

    def on_open(self):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """

        # delete render_settings
        self.render_settings = None

        # if a file is already running, then stop it.
        self.on_stop()

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        p = pathlib.Path(os.path.expanduser("~"))
        fullname = askopenfilename(initialdir=p, title="choose your file",
                                   filetypes=(("all files", "*.*"), ("mp4 files", "*.mp4")))
        if os.path.isfile(fullname):
            input_video_path = fullname
            self.video_path = input_video_path
            self.media = self.Instance.media_new(input_video_path)
            self.player.set_media(self.media)

            # set the window id where to render vlc video output
            self.player.set_hwnd(self.get_handle())
            self.on_play()

            # set speed slider to 1
            self.speed_slider.set(1)

            # load video duration
            self.video_duration = -1
            while self.video_duration == -1:
                self.video_duration = self.media.get_duration()
            logging.debug("self.video_duration: " + str(self.video_duration))

            root = self.parent
            a, b = root.winfo_screenwidth(), root.winfo_screenheight()
            w, h = int(a / 2), int(b / 2)
            root.geometry("%dx%d+0+0" % (w, h))

            reset_sequences(video_length=self.video_duration)
        self.update_play_pause_button()

    def on_play(self):
        """Toggle the status to Play/Pause.
                If no file is loaded, open the dialog window.
                """
        # check if there is a file to play, otherwise open a
        # Tk.FileDialog to select a file
        if not self.player.get_media():
            self.on_open()
        else:
            # Try to launch the media, if this fails display an error message
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")
        self.update_play_pause_button()

    def get_handle(self):
        return self.videopanel.winfo_id()

    # def on_pause(self, evt):
    def on_pause(self):
        """Pause the player.
        """
        self.player.pause()
        self.update_play_pause_button()

    def on_stop(self):
        """Stop the player.
        """
        self.player.stop()
        # reset the time slider
        self.time_slider.set(0)
        self.update_play_pause_button()

    def OnTimer(self):
        """Update the time slider according to the current movie time.
        """
        if self.player is None:
            return

        if self.set_time_to != -1:
            logging.debug("OnTimer: set time, " + "self.set_time_to=" + str(self.set_time_to))
            self.player.set_time(self.set_time_to)
            self.set_time_to = -1

        # since the self.player.get_length can change while playing,
        # re-set the time_slider to the correct range.
        length = self.player.get_length()
        dbl = length * 0.001
        self.time_slider.config(to=dbl)

        # update the time on the slider
        t_val = self.get_real_time()
        dbl = t_val * 0.001
        self.time_slider_last_val = ("%.0f" % dbl) + ".0"
        # don't want to programatically change slider while user is messing with it.
        # wait 2 seconds after user lets go of slider
        if time.time() > (self.time_slider_last_update + 2.0):
            self.time_slider.set(dbl)

    def scale_sel(self, evt):
        if self.player is None:
            return

        self.render_sequences()

        nval = self.scale_var.get()
        sval = str(nval)
        if self.time_slider_last_val != sval:
            # this is a hack. The timer updates the time slider.
            # This change causes this rtn (the 'slider has changed' rtn) to be invoked.
            # I can't tell the difference between when the user has manually moved the slider and when
            # the timer changed the slider. But when the user moves the slider tkinter only notifies
            # this rtn about once per second and when the slider has quit moving.
            # Also, the tkinter notification value has no fractional seconds.
            # The timer update rtn saves off the last update value (rounded to integer seconds) in time_slider_last_val
            # if the notification time (sval) is the same as the last saved time time_slider_last_val then
            # we know that this notification is due to the timer changing the slider.
            # otherwise the notification is due to the user changing the slider.
            # if the user is changing the slider then I have the timer routine wait for at least
            # 2 seconds before it starts updating the slider again (so the timer doesn't start fighting with the
            # user)

            self.stop_marker()

            self.time_slider_last_update = time.time()
            mval = "%.0f" % (nval * 1000)
            self.player.set_time(int(mval))  # expects milliseconds

            self.marker_mode = -1
            self.marker_start_time = self.get_real_time()

    def render_sequences(self):
        if self.player is not None:
            if self.player.is_playing() == 0:
                if str(self.player.get_state()) == "State.Ended":
                    logging.debug("State.Ended")
                    logging.debug("restart")
                    input_video_path = self.video_path
                    if input_video_path is not None:
                        if input_video_path != "":
                            self.stop_marker()
                            self.media = self.Instance.media_new(input_video_path)
                            self.player.set_media(self.media)
                            self.speed_slider.set(1)
                            self.player.play()
                            self.update_play_pause_button()

        global sequences

        size_x = self.draw_canvas.winfo_width()
        rect_h = 50
        time_pixel_factor = size_x / max(1, self.video_duration)

        # clear old drawing
        for o in self.draw_objects:
            self.draw_canvas.delete(o)
        self.draw_objects = []

        # x2 = current x position in video
        x2 = int(self.get_real_time() * time_pixel_factor)

        # render current action
        if self.marker_mode != -1:
            x1 = int(self.marker_start_time * time_pixel_factor)
            if x1 < x2:
                if flash_period:
                    if self.marker_mode > 0:
                        rect_c = GREEN_2
                    else:
                        rect_c = RED_2
                else:
                    if self.marker_mode > 0:
                        rect_c = TAG_COLORS[self.selected_tag_index]
                    else:
                        rect_c = 'red'
                self.draw_objects.append(self.draw_canvas.create_rectangle(x1, 0, x2, rect_h, fill=rect_c))

        # highlight video position
        self.draw_objects.append(self.draw_canvas.create_line(x2, 0, x2, rect_h, width=3))

        # mark zoom preview start and end
        if self.zoom_preview_start is not None and self.zoom_preview_end is not None:
            for line in [self.zoom_preview_start, self.zoom_preview_end]:
                x = time_pixel_factor * line
                self.draw_objects.append(self.draw_canvas.create_line(x, 0, x, rect_h, width=2))

    def get_real_time(self):
        return self.player.get_time()

    def speed_sel(self, evt):
        if self.player is None:
            return

        new_speed = self.speed_var.get()
        if new_speed <= 0.01:
            self.player.pause()
        else:
            self.play_speed = new_speed
            self.player.play()
            self.player.set_rate(new_speed)
        self.update_play_pause_button()

    def error_dialog(self, error_message):
        """Display a simple error dialog.
        """
        tk.tkMessageBox.showerror(self, 'Error', error_message)


def tk_get_root():
    if not hasattr(tk_get_root, "root"):  # (1)
        tk_get_root.root = tk.Tk()  # initialization call is inside the function
    return tk_get_root.root


def _quit():
    logging.debug("_quit: bye")
    root = tk_get_root()
    root.quit()  # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    if profile_mode:
        pr.disable()
        pr.print_stats(sort="calls")

    os._exit(1)


def is_second_window_open():
    root = tk_get_root()
    return tk.Toplevel in [type(item) for item in root.winfo_children()]


def key(event):
    if is_second_window_open():
        return None

    if event.char == event.keysym:
        msg = 'Normal Key %r' % event.char
        # logging.debug(msg)
    elif len(event.char) == 1:
        msg = 'Punctuation Key %r (%r)' % (event.keysym, event.char)
        if msg == "Punctuation Key 's' ('\\x13')":
            save_data()
        elif msg == "Punctuation Key 'space' (' ')":
            if not get_player().is_typing():
                get_player().on_toggle_play_pause()
        elif msg == "Punctuation Key 'Return' ('\\r')":
            if get_player() is not None:
                get_player().on_return_pressed()
    else:
        msg = 'Special Key %r' % event.keysym
        if not get_player().is_typing():
            if msg == "Special Key 'Right'":
                delta_t = -1
            elif msg == "Special Key 'Left'":
                delta_t = 1
            else:
                delta_t = 0
            if delta_t != 0:
                get_player().go_t_back(delta_t)
    if msg.lower() == "normal key 'y'":
        if not get_player().is_typing():
            get_player().toggle_mark_rally()
    elif msg.lower() == "normal key 'x'":
        get_player().toggle_mark_pause()
    elif msg.lower() == "normal key 'm'":
        get_player().cancel_marker()
    elif not get_player().is_typing() and msg.lower() == "normal key 'v'":
        get_player().tag_moment()
    else:
        if not get_player().is_typing():
            for num in range(4):
                c = "abcd"[num]
                if msg.lower() == "normal key '" + c + "'":
                    get_player().select_tag(c)


def get_player():
    result: Player
    if player is not None:
        result = player
    else:
        result = Player(tk_get_root())
    return result


def main():
    global player

    # Create a tk.App(), which handles the windowing system event loop
    root = tk_get_root()
    # root.wm_attributes("-alpha", 0.9)

    root.protocol("WM_DELETE_WINDOW", _quit)

    # set window icon
    root.iconbitmap("p_icon.ico")

    # bind key events
    root.bind_all('<Key>', key)

    player = Player(root, title="Video Assistant")

    # show the player window centred and run the application
    root.mainloop()


if __name__ == "__main__":
    if profile_mode:
        pr = cProfile.Profile()
        pr.enable()
    main()
