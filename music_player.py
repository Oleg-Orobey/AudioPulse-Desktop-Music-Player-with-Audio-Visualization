import pygame
from pygame import mixer
from tkinter import *
from tkinter.ttk import Progressbar
from tkinter import ttk, PhotoImage, filedialog
import os
import sys
import eyed3
import math
import wave
import ffmpeg
import pathlib
from mutagen import File
from mutagen.mp3 import MP3
from PIL import Image
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import sounddevice as sd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

audio_stream = None
sample_rate = 44100
fig, ax, bars, canvas = None, None, [], None
mp3_file = None
fig_canvas = None
muslen = 0
current_track_index = 0
visualization_enabled = True
visualization_frame = None
pygame.mixer.init(22050, -16, 2)
pygame.init()
b = False
ifplay = False
mut = False
vol = 0.2
must = 0
tek = 0
scc = 5

def mp3_to_wav(mp3_file, wav_file):
    try:
        (
            ffmpeg.input(mp3_file)
            .output(wav_file, ac=1, ar=sample_rate)
            .run(overwrite_output=True, quiet=True)
        )
    except Exception as e:
        print(f"Ошибка конвертации: {e}")

def audio_callback(indata, frames, time_info, status):
    global bars, ifplay
    if not ifplay or not visualization_enabled:
        return
    mono_audio = indata[:, 0]
    fft_values = np.abs(np.fft.fft(mono_audio)[:180])
    fft_values = fft_values / np.max(fft_values) if np.max(fft_values) > 0 else fft_values
    fft_values *= 3.0
    for i, bar in enumerate(bars):
        bar.set_height(fft_values[i] if i < len(fft_values) else 0.1)
    fig_canvas.draw_idle()

def start_visualization():
    global fig, ax, bars, audio_stream, fig_canvas
    
    if not visualization_enabled or not ifplay:
        return
        
    if fig_canvas is None:
        plt.style.use('tableau-colorblind10')
        fig, ax = plt.subplots(figsize=(4, 2))
        fig.patch.set_facecolor('#A9A9A9')
        ax.set_facecolor('#A9A9A9')
        ax.set_axis_off()
        ax.set_xlim(0, 180)
        ax.set_ylim(0, 1)
        bars = ax.bar(range(180), np.zeros(180), color='#0B3D02')
        
        fig_canvas = FigureCanvasTkAgg(fig, master=visualization_frame)
        fig_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        fig_canvas.draw()
    
    if audio_stream is None:
        audio_stream = sd.InputStream(callback=audio_callback,
                                   samplerate=sample_rate,
                                   channels=1,
                                   blocksize=256)
        audio_stream.start()

def stop_visualization():
    global audio_stream
    
    if audio_stream:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None

def play_music():
    global ifplay, mp3_file, tek
    if not mp3_file:
        return

    if not ifplay:
        pygame.mixer.music.load(mp3_file)
        pygame.mixer.music.play()
        ifplay = True
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        start_visualization()

def check_music_events():
    for event in pygame.event.get():
        if event.type == pygame.USEREVENT:
            if repeat_mode.get() == 1:
                play_selected_track(current_track_index)
            else:
                play_next()
    window.after(100, check_music_events)

def play_next():
    global mp3_file, tek, ifplay, files
    current_index = lb.curselection()[0] if lb.curselection() else 0
    next_index = current_index + 1
    
    if next_index < lb.size():
        lb.selection_clear(0, END)
        lb.selection_set(next_index)
        lb.activate(next_index)
        file = files[next_index]
        mp3_file = file
        tek = 0
        pygame.mixer.music.load(mp3_file)
        pygame.mixer.music.play()
        audio = MP3(mp3_file)
        muslen = audio.info.length
        bar['maximum'] = muslen
        efile = eyed3.load(mp3_file)
        lbt['text'] = efile.tag.title if efile.tag and efile.tag.title else "Нет названия"
        lba['text'] = efile.tag.artist if efile.tag and efile.tag.artist else "Нет артиста"
        ifplay = True

def p_next():
    global current_track_index, mp3_file, tek, ifplay
    
    if len(files) == 0:
        return
    
    current_track_index = (current_track_index + 1) % len(files)
    play_selected_track(current_track_index)

def p_previous():
    global current_track_index, mp3_file, tek, ifplay
    
    if len(files) == 0:
        return
    
    current_track_index = (current_track_index - 1) % len(files)
    play_selected_track(current_track_index)

def play_selected_track(index):
    global mp3_file, tek, ifplay, current_track_index
    
    if index < 0 or index >= len(files):
        return
    
    current_track_index = index
    file = files[index]
    mp3_file = file
    tek = 0
    
    lb.selection_clear(0, END)
    lb.selection_set(index)
    lb.activate(index)
    lb.see(index)
    
    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play()
    pygame.mixer.music.set_endevent(pygame.USEREVENT)
    
    audio = MP3(mp3_file)
    muslen = audio.info.length
    bar['maximum'] = muslen
    efile = eyed3.load(mp3_file)
    lbt['text'] = efile.tag.title if efile.tag and efile.tag.title else "Нет названия"
    lba['text'] = efile.tag.artist if efile.tag and efile.tag.artist else "Нет артиста"
    ifplay = True
    
    if visualization_enabled:
        start_visualization()

def toggle_visualization():
    global visualization_enabled
    
    visualization_enabled = not visualization_enabled
    
    if visualization_enabled:
        toggle_btn.config(image=on_img)
        if ifplay:
            start_visualization()
        if fig_canvas:
            fig_canvas.get_tk_widget().grid()
    else:
        toggle_btn.config(image=off_img)
        stop_visualization()
        if fig_canvas:
            fig_canvas.get_tk_widget().grid_remove()
    
    visualization_frame.grid()

def resize_image(input_image_path, output_image_path, size):
    org_img = Image.open(input_image_path)
    resized_image = org_img.resize(size)
    resized_image.save(output_image_path)

def music(file):
    pygame.init()
    clock = pygame.time.Clock()
    pygame.mixer.music.load(file)
    pygame.mixer.music.play()

def play():
    global b, must, muslen, tek, ifplay, mp3_file, current_track_index
    ifplay = True
    if b:  
        b = False
        pygame.mixer.music.unpause()
        if visualization_enabled and audio_stream:
            audio_stream.start()
    else:  
        index = lb.curselection()[0]
        file = files[index]
        mp3_file = file
        tek = 0
        pygame.mixer.music.load(mp3_file)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        audio = MP3(mp3_file)
        muslen = audio.info.length
        bar['maximum'] = muslen
        efile = eyed3.load(mp3_file)
        lbt['text'] = efile.tag.title if efile.tag and efile.tag.title else "Нет названия"
        lba['text'] = efile.tag.artist if efile.tag and efile.tag.artist else "Нет артиста"
        if visualization_enabled:
            start_visualization()
        if lb.curselection():
            current_track_index = lb.curselection()[0]
            play_selected_track(current_track_index)

def pause():       
    global b, ifplay
    ifplay = False
    pygame.mixer.music.pause()
    b = True
    if audio_stream:
        audio_stream.stop()

def stop():
    global ifplay
    pygame.mixer.music.pause()
    pygame.mixer.music.stop()
    ifplay = False
    stop_visualization()

def mute():
    global mut, vol, scc
    
    mut = not mut
    
    if mut:
        bmute.config(image=mute_img)
        vol = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(0)
        sca1.set(0)
        update_slider(0)
    else:
        bmute.config(image=unmute_img)
        pygame.mixer.music.set_volume(vol)
        sca1.set(vol * 10)
        update_slider(vol * 10)

def format_time(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes:02}:{seconds:02}"

window = Tk()
window.title("Музыкальный плеер")
window.geometry('800x500')
window.configure(bg='#2E2E2E')
style = ttk.Style()
style.configure('TButton', background='#2E2E2E', foreground='white')
style.map('TButton', background=[('active', '#505050')])

start_visualization()

main_frame = Frame(window, bg='#2E2E2E')
main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
left_frame = Frame(main_frame, bg='#2E2E2E', width=200)
left_frame.grid(column=0, row=0, rowspan=4, sticky="ns", padx=(0, 10))
center_frame = Frame(main_frame, bg='#2E2E2E')
center_frame.grid(column=1, row=0, rowspan=4, sticky="nsew")
right_frame = Frame(main_frame, bg='#2E2E2E', width=120)
right_frame.grid(column=2, row=0, sticky="nswe", padx=10, pady=10)
right_frame.grid_propagate(False)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(3, weight=1)

lb = Listbox(left_frame, width=25, height=20, font=("Yandex Sans", 9, "bold"), 
            bg='#3E3E3E', fg='white', selectbackground='#0B3D02')
lb.pack(fill=BOTH, expand=True)

visualization_frame = Frame(center_frame, width=400, height=200, bg='#A9A9A9')
visualization_frame.grid(column=0, row=0, sticky="nsew", pady=(0, 10))
visualization_frame.grid_propagate(False)

controls_frame = Frame(center_frame, bg='#2E2E2E')
controls_frame.grid(column=0, row=1, sticky="ew")
right_content = Frame(right_frame, bg='#2E2E2E')
right_content.pack(fill='both', padx=5, pady=5)
left_frame.grid_propagate(False)
right_frame.grid_propagate(False)
right_content.pack_configure(padx=10, pady=10)

bar = Progressbar(center_frame, length=350, style='black.Horizontal.TProgressbar', max=100)
bar.grid(column=0, row=2, sticky="ew", pady=5)

info_frame = Frame(center_frame, bg='#2E2E2E')
info_frame.grid(column=0, row=3, sticky="ew")

def seek_music(event):
    global tek, muslen, ifplay
    new_time = (event.x / bar.winfo_width()) * muslen
    tek = int(new_time)
    pygame.mixer.music.play(start=tek)
    bar['value'] = tek

bar.bind("<Button-1>", seek_music)

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

IMAGE_PATHS = {
    "play": r"images/play.png",
    "pause": r"images/pause.png",
    "stop": r"images/stop.png",
    "mute": r"images/mute.png",
    "unmute": r"images/mute_off.png",
    "prev": r"images/prev.png",
    "povz": r"images/povz.png",
    "next": r"images/next.png",
    "toggle_on": r"images/toggle_on.png",
    "toggle_off": r"images/toggle_off.png",
}
resize_image(IMAGE_PATHS['play'], IMAGE_PATHS['play'], (40, 40))
resize_image(IMAGE_PATHS['pause'], IMAGE_PATHS['pause'], (40, 40))
resize_image(IMAGE_PATHS['stop'], IMAGE_PATHS['stop'], (40, 40))
resize_image(IMAGE_PATHS['mute'], IMAGE_PATHS['mute'], (40, 40))
resize_image(IMAGE_PATHS['unmute'], IMAGE_PATHS['unmute'], (40, 40))
resize_image(IMAGE_PATHS['prev'], IMAGE_PATHS['prev'], (40, 40))
resize_image(IMAGE_PATHS['povz'], IMAGE_PATHS['povz'], (40, 40))
resize_image(IMAGE_PATHS['next'], IMAGE_PATHS['next'], (40, 40))
resize_image(IMAGE_PATHS['toggle_on'], IMAGE_PATHS['toggle_on'], (60, 30))
resize_image(IMAGE_PATHS['toggle_off'], IMAGE_PATHS['toggle_off'], (60, 30))
play_img = PhotoImage(file=IMAGE_PATHS['play'])
pause_img = PhotoImage(file=IMAGE_PATHS['pause'])
stop_img = PhotoImage(file=IMAGE_PATHS['stop'])
mute_img = PhotoImage(file=IMAGE_PATHS['mute'])
unmute_img = PhotoImage(file=IMAGE_PATHS['unmute'])
prev_img = PhotoImage(file=IMAGE_PATHS['prev'])
povz_img = PhotoImage(file=IMAGE_PATHS['povz'])
next_img = PhotoImage(file=IMAGE_PATHS['next'])
on_img = PhotoImage(file=IMAGE_PATHS['toggle_on'])
off_img = PhotoImage(file=IMAGE_PATHS['toggle_off'])

Button(controls_frame, image=prev_img, command=p_previous, width=40, height=40, bd=0, 
      bg='#2E2E2E', activebackground='#505050').grid(column=0, row=0, padx=5)
Button(controls_frame, image=play_img, command=play, width=40, height=40, bd=0, 
      bg='#2E2E2E', activebackground='#505050').grid(column=1, row=0, padx=5)
Button(controls_frame, image=pause_img, command=pause, width=40, height=40, bd=0, 
      bg='#2E2E2E', activebackground='#505050').grid(column=2, row=0, padx=5)
Button(controls_frame, image=next_img, command=p_next, width=40, height=40, bd=0, 
      bg='#2E2E2E', activebackground='#505050').grid(column=3, row=0, padx=5)

toggle_frame = Frame(controls_frame, bg='#2E2E2E')
toggle_frame.grid(column=4, row=0, padx=10)
Label(toggle_frame, text="Визуализация:", bg='#2E2E2E', fg='white').pack()
toggle_btn = Button(toggle_frame, image=on_img, command=toggle_visualization, bd=0, 
                   bg='#2E2E2E', activebackground='#505050')
toggle_btn.pack()

lbt = Label(info_frame, text='Название трека', font=('Arial Bold', 14), bg='#2E2E2E', fg='white')
lbt.pack()
lbi = Label(info_frame, text="00:00/00:00", font=('Arial Bold', 10), bg='#2E2E2E', fg='white')
lbi.pack()
lba = Label(info_frame, text='Исполнитель', font=('Arial Bold', 12), bg='#2E2E2E', fg='white')
lba.pack()

repeat_frame = Frame(controls_frame, bg='#2E2E2E')
repeat_frame.grid(column=5, row=0, padx=10)
repeat_mode = IntVar()
repeat_check = Checkbutton(repeat_frame, text="Повтор", variable=repeat_mode, 
                         bg='#2E2E2E', fg='white', selectcolor='#0B3D02',
                         activebackground='#2E2E2E', activeforeground='white')
repeat_check.pack()

files = [f for f in os.listdir() if f.endswith('.mp3')]
for f in files:
    try:
        audio_file = eyed3.load(f)
        title = audio_file.tag.title if audio_file.tag and audio_file.tag.title else f
        artist = audio_file.tag.artist if audio_file.tag and audio_file.tag.artist else ""
        lb.insert(END, f"{title} - {artist}")
    except:
        lb.insert(END, f)

def update():
    global window, ifplay, tek
    if ifplay:
        tek += 1
        bar['value'] = tek
        s = format_time(tek) + "/" + format_time(muslen)
        lbi['text'] = s
    else:
        ifplay = False
        pygame.mixer.music.pause()
    window.after(1000, update)


def scii(val):
    pygame.mixer.music.set_volume(float(val) / 10)
    update_slider(val)

def update_slider(val):
    y_pos = int(280 - (float(val) / 10) * 280)
    canvas.coords(slider_circle, 5, y_pos - 10, 25, y_pos + 10)
    canvas.coords(slider_fill, 12, y_pos, 18, 290)

def move_slider(event):
    if 10 <= event.y <= 290:
        value = round((290 - event.y) / 280 * 10, 1)
        sca1.set(value)
        update_slider(value)

volume_frame = Frame(right_content, bg='#2E2E2E')
volume_frame.pack(fill='x')

Label(volume_frame, text="Громкость", bg='#2E2E2E', 
      fg='white', font=('Arial', 10)).pack()    



def on_closing():
    stop()
    pygame.mixer.quit()
    window.destroy()


window.protocol("WM_DELETE_WINDOW", on_closing)

canvas = Canvas(volume_frame, width=40, height=300, bg='#2E2E2E', highlightthickness=0)
canvas.pack()

canvas.bind("<B1-Motion>", move_slider)
canvas.bind("<Button-1>", move_slider)

slider_fill = canvas.create_rectangle(12, 150, 18, 290, fill='#808080', outline='#808080')
slider_circle = canvas.create_oval(5, 140, 25, 160, fill='#0B3D02', outline='#0B3D02')
sca1 = Scale(window, orient=VERTICAL, length=280, from_=0, to=10, resolution=0.1,
             command=scii, showvalue=0, sliderlength=1, width=0, bd=0,
             troughcolor='#555', bg='#2E2E2E', fg='white', highlightthickness=0)
sca1.set(scc)
sca1.pack()

bmute = Button(volume_frame, image=unmute_img, command=mute, width=40, height=40, bd=0, 
              bg='#2E2E2E', activebackground='#505050')
bmute.pack(pady=10)


bmute.bind("<Enter>", lambda e: bmute.config(bg='#505050'))
bmute.bind("<Leave>", lambda e: bmute.config(bg='#2E2E2E'))

window.tk_setPalette(background='#2E2E2E')
sca1.configure(activebackground='#0B3D02')



window.protocol("WM_DELETE_WINDOW", on_closing)

update()
window.after(100, check_music_events)
window.mainloop()