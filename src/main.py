import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
import mss
import threading
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk
import time

# ---------------- CONFIG ----------------

FPS = 60
FRAME_TIME = 1 / FPS

BG = "#1e1e1e"
GREEN = "#6bd66b"
RED = "#ff6b6b"
BLUE = "#4da6ff"
TEXT = "#d0d0d0"

HANDLE_SIZE = 8

recording = False
frames = []
output_path = os.getcwd()
frame_visible = True

# ---------------- ROOT ----------------

root = tk.Tk()
root.title("MRS Recorder")
root.geometry("320x140")
root.resizable(False, False)
root.minsize(320,140)
root.maxsize(320,140)
root.configure(bg=BG)

# ---------------- PLAY / STOP BUTTON ----------------

def make_button(color, mode):

    size = 200
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    draw.ellipse((10,10,size-10,size-10), fill=color)

    if mode == "play":
        draw.polygon([(80,60),(80,140),(140,100)], fill="white")
    else:
        draw.rectangle((75,75,125,125), fill="white")

    img = img.resize((70,70), Image.LANCZOS)

    return ImageTk.PhotoImage(img)

play_img = make_button(GREEN,"play")
stop_img = make_button(RED,"stop")

# ---------------- OVERLAY ----------------

overlay = tk.Toplevel()
overlay.overrideredirect(True)
overlay.geometry("420x300+500+300")
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor","black")

canvas_overlay = tk.Canvas(
    overlay,
    bg="black",
    highlightthickness=2,
    highlightbackground=BLUE
)

canvas_overlay.pack(fill="both", expand=True)

handles = {}
resize_mode = None

# ---------------- HANDLES ----------------

def draw_handles():

    if not frame_visible:
        return

    canvas_overlay.delete("handle")

    w = canvas_overlay.winfo_width()
    h = canvas_overlay.winfo_height()

    positions = {
        "nw":(0,0),"n":(w/2,0),"ne":(w,0),
        "e":(w,h/2),"se":(w,h),
        "s":(w/2,h),"sw":(0,h),"w":(0,h/2)
    }

    for key,(x,y) in positions.items():

        handle = canvas_overlay.create_oval(
            x-HANDLE_SIZE,y-HANDLE_SIZE,
            x+HANDLE_SIZE,y+HANDLE_SIZE,
            fill=BLUE,
            outline="",
            tags=("handle",key)
        )

        handles[handle] = key

# ---------------- SHOW / HIDE FRAME ----------------

def toggle_frame():

    global frame_visible
    frame_visible = not frame_visible

    if frame_visible:
        canvas_overlay.configure(highlightthickness=2)
        draw_handles()
        eye_canvas.itemconfig(eye_icon, text="👁")
    else:
        canvas_overlay.configure(highlightthickness=0)
        canvas_overlay.delete("handle")
        eye_canvas.itemconfig(eye_icon, text="🚫")

# ---------------- MOVE / RESIZE ----------------

def start_action(event):

    global resize_mode

    items = canvas_overlay.find_overlapping(event.x, event.y, event.x, event.y)

    resize_mode = None

    for item in items:
        if item in handles:
            resize_mode = handles[item]
            break

    if resize_mode is None:
        resize_mode = "move"
        overlay.start_x = event.x
        overlay.start_y = event.y


def perform_action(event):

    global resize_mode

    x = overlay.winfo_x()
    y = overlay.winfo_y()
    w = overlay.winfo_width()
    h = overlay.winfo_height()

    dx = event.x_root - overlay.winfo_rootx()
    dy = event.y_root - overlay.winfo_rooty()

    if resize_mode == "move":

        new_x = overlay.winfo_x() + (event.x-overlay.start_x)
        new_y = overlay.winfo_y() + (event.y-overlay.start_y)

        overlay.geometry(f"+{new_x}+{new_y}")
        return

    new_w,new_h,new_x,new_y = w,h,x,y

    if "e" in resize_mode: new_w = dx
    if "s" in resize_mode: new_h = dy

    if "w" in resize_mode:
        new_w = w-dx
        new_x = x+dx

    if "n" in resize_mode:
        new_h = h-dy
        new_y = y+dy

    new_w = max(120,new_w)
    new_h = max(80,new_h)

    overlay.geometry(f"{int(new_w)}x{int(new_h)}+{int(new_x)}+{int(new_y)}")


def stop_action(event):

    global resize_mode
    resize_mode = None
    draw_handles()

canvas_overlay.bind("<Button-1>",start_action)
canvas_overlay.bind("<B1-Motion>",perform_action)
canvas_overlay.bind("<ButtonRelease-1>",stop_action)
canvas_overlay.bind("<Configure>",lambda e: draw_handles())

# ---------------- RECORD ----------------

def record_screen():

    global recording, frames

    with mss.mss() as sct:

        while recording:

            start = time.time()

            x = overlay.winfo_x()
            y = overlay.winfo_y()
            w = overlay.winfo_width()
            h = overlay.winfo_height()

            monitor = {"top":y,"left":x,"width":w,"height":h}

            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame,cv2.COLOR_BGRA2BGR)

            frames.append(frame)

            elapsed = time.time() - start
            sleep_time = FRAME_TIME - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)

# ---------------- BUTTON ----------------

btn_canvas = tk.Canvas(root,width=70,height=70,bg=BG,highlightthickness=0)
btn_canvas.pack(pady=10)

button_img = btn_canvas.create_image(35,35,image=play_img)

# ---------------- START / STOP ----------------

def toggle_record(event=None):

    global recording,frames

    if not recording:

        frames=[]
        recording=True
        btn_canvas.itemconfig(button_img,image=stop_img)

        threading.Thread(target=record_screen,daemon=True).start()

    else:

        recording=False
        btn_canvas.itemconfig(button_img,image=play_img)

        if frames:

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recording_{timestamp}.avi"

            full_path = os.path.join(output_path,filename)

            h,w,_ = frames[0].shape

            fourcc = cv2.VideoWriter_fourcc(*"XVID")

            out = cv2.VideoWriter(full_path,fourcc,20,(w,h))

            for f in frames:
                out.write(f)

            out.release()

            print("Saved:",full_path)

btn_canvas.bind("<Button-1>",toggle_record)

# ---------------- PATH ----------------

path_frame = tk.Frame(root,bg=BG)
path_frame.pack(fill="x",padx=20)

path_var = tk.StringVar(value=output_path)

path_entry = tk.Entry(
    path_frame,
    textvariable=path_var,
    bg=BG,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat"
)

path_entry.pack(side="left",fill="x",expand=True,ipady=5)

# ---- undo / redo ----

undo_stack = []
redo_stack = []

def save_state(event=None):
    undo_stack.append(path_var.get())

def undo(event=None):
    if undo_stack:
        redo_stack.append(path_var.get())
        path_var.set(undo_stack.pop())

def redo(event=None):
    if redo_stack:
        undo_stack.append(path_var.get())
        path_var.set(redo_stack.pop())

path_entry.bind("<Key>",save_state)
path_entry.bind("<Control-z>",undo)
path_entry.bind("<Control-y>",redo)

# ---- folder button ----

def choose_path():

    global output_path

    folder = filedialog.askdirectory()

    if folder:
        output_path = folder
        path_var.set(folder)

folder_btn = tk.Canvas(
    path_frame,
    width=28,
    height=28,
    bg=BG,
    highlightthickness=0
)

folder_btn.create_text(
    14,
    14,
    text="📁",
    fill=TEXT,
    font=("Segoe UI Emoji", 12)
)

folder_btn.pack(side="right")
folder_btn.bind("<Button-1>", lambda e: choose_path())

# ---------------- EYE BUTTON ----------------

eye_canvas = tk.Canvas(root,width=28,height=28,bg=BG,highlightthickness=0)
eye_canvas.place(x=5,y=5)

eye_icon = eye_canvas.create_text(
    14,
    14,
    text="👁",
    fill=TEXT,
    font=("Segoe UI Emoji", 12)
)

eye_canvas.bind("<Button-1>", lambda e: toggle_frame())

draw_handles()

root.mainloop()