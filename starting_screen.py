import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import threading
from pathlib import Path

project_dir = Path(__file__).resolve().parent

#============
# colour HEX set up
#============
bg_hex_colour = "#beebe9"
bg_grey = "#323633"
active_grey = "#ccc8cf"
txt_colour_light = "#e4eff0"
txt_colour_dark = "#043f45"
font = "Small Fonts"


#============
# defining function section
#============

def run_script(difficulty):
    subprocess.run(["python", str(project_dir / "main.py"), difficulty])
    window.destroy()

def start_game(difficulty):
    threading.Thread(target=lambda: run_script(difficulty), daemon=True).start()

def select_difficulty():
    start_button.destroy()

    difficulties = [("Easy", "easy"), ("Normal", "normal"), ("Hard", "hard")]
    for i, (label, value) in enumerate(difficulties):
        btn = tk.Button(
            window,
            font=(font, 30),
            width=10,
            height=1,
            bg=bg_grey,
            fg=txt_colour_light,
            activebackground=active_grey,
            activeforeground=txt_colour_dark,
            text=label,
            command=lambda v=value: start_game(v)
        )
        # Place them vertically spaced
        canvas.create_window(
            (window_width//2, (window_height//2) + i*80),
            window=btn
        )


#============
# window setup
#============

# Start screen setup
window = tk.Tk()

window.title("Welcome to Bit Fisher 🎣")
window_width = window.winfo_screenwidth()
window_height = window.winfo_screenheight()
window.geometry("%dx%d" % (window_width, window_height))

bg_colour = bg_hex_colour
canvas = tk.Canvas(window, width=window_width, height=window_height, bg=bg_colour)
canvas.pack()


bg_image_raw = Image.open(project_dir / "images" / "starting_screen_bg.png")
resized_bg_image_raw = bg_image_raw.resize((window_width, window_height))
bg_image = ImageTk.PhotoImage(resized_bg_image_raw)
bg = canvas.create_image((window_width//2), (window_height//2), image=bg_image)


title_image_raw = Image.open(project_dir / "images" / "bitfisher_title.png")
title_image_raw = title_image_raw.resize((1000, 280))  # Resize to match radius
title_image = ImageTk.PhotoImage(title_image_raw)
title = canvas.create_image((window_width//2), (window_height-700), image=title_image)


#============
# start button config
#============

button_text = "Start Game"

start_button = tk.Button(
    window,
    font=(font, 40),
    width=15,
    height=1,
    bg=bg_grey,
    fg=txt_colour_light,
    activebackground=active_grey,
    activeforeground=txt_colour_dark,
    text=button_text,
    command=select_difficulty
)

button = canvas.create_window((window_width//2), (window_height//2), window=start_button)


window.mainloop()