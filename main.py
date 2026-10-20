import tkinter as tk
from PIL import Image, ImageTk
import math
import random
import os
import sys
import csv
import matplotlib.pyplot as plt

# ============================
# Colour HEX value set up
# ============================

bg_colour = "#beebe9"
bg_grey = "#323633"
active_grey = "#ccc8cf"
bg_green = "#448249"
active_green = "#b1c4b3"
bg_red = "#8c2323"
active_red = "#e8bcbc"

blue_outline_colour = "#241f30"
green_outline_colour = "#182119"
txt_colour_light = "#e4eff0"
txt_colour_dark = "#043f45"
font = "Small Fonts"

# Handles command line arguments to set the game difficulty level
if len(sys.argv) > 1:
    initial_difficulty = sys.argv[1].lower()
else:
    initial_difficulty = "normal"

# Maps string difficulty levels to float values for speed adjustment
difficulty_map = {
    "easy": -0.002,
    "normal": 0.0,
    "hard": 0.003
}

initial_difficulty = difficulty_map.get(initial_difficulty, 0.0)

# Path to local image assets
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "images", "fish_sprites")

# ================================
# FISH CLASS SET UP
# ================================

class Fish:
    def __init__(self, canvas: tk.Canvas, x: int, y: int, radius: int, fish_types: list):
        """
        Initializes a fish object with movement logic and visual representation.
        fish_types: list of dicts containing 'name', 'rarity' (int), and 'image' (str).
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius

        # Selects fish identity based on rarity weights
        self.fish_data = self.weighted_choice(fish_types)
        self.type_name = self.fish_data.get("name", "unknown")
        self.rarity = self.fish_data.get("rarity", 1)

        # Calculates wave_speed (float) based on rarity; rarer fish move faster
        self.calculate_speed_from_rarity(min_speed=0.002, max_speed=0.01, max_rarity=100)
        self.starting_level = round(self.wave_speed * 1000)

        # Image loading logic
        image_filename = self.fish_data.get("image", None)
        self.image = None
        self.is_image = False

        if image_filename:
            image_path = os.path.join(IMAGE_DIR, image_filename)
            try:
                img_raw = Image.open(image_path)
                img_raw = img_raw.resize((radius * 4, radius * 4))
                self.image = ImageTk.PhotoImage(img_raw)
                self.is_image = True
            except:
                self.is_image = False

        # Renders the fish as an image or a procedural oval if image fails
        if self.is_image:
            self.canvas_item = self.canvas.create_image(self.x, self.y, image=self.image)
        else:
            shade = max(50, 255 - int(self.rarity * 10))
            fill = f"#{shade:02x}{shade:02x}{int(shade / 1.5):02x}"
            self.canvas_item = self.canvas.create_oval(
                self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius,
                fill=fill, outline="black")

        self.wave_x = 0.0
        self.generate_new_wave()

        self.in_bar = False
        self.time_in_bar = 0

# Function to obtain a speed value from rarity
    def calculate_speed_from_rarity(self, min_speed: float, max_speed: float, max_rarity: int):
        rarity = max(1, self.rarity)
        self.wave_speed = min_speed + (max_rarity - rarity) / max_rarity * (max_speed - min_speed)

    @staticmethod
    def weighted_choice(fish_types: list) -> dict:
        """Uses a weighted random algorithm to pick a fish dictionary from the list."""
        weights = [f.get("rarity", 1) for f in fish_types]
        total = sum(weights)
        if total <= 0:
            return random.choice(fish_types)

        r = random.uniform(0, total)
        cumulative = 0.0
        for f, w in zip(fish_types, weights):
            cumulative += w
            if r <= cumulative:
                return f
        return fish_types[-1]

    def generate_new_wave(self):
        """Randomizes sine/cosine coefficients for unpredictable fish movement."""
        self.a = random.randint(150, 500)
        self.b = random.uniform(8, 12)
        self.c = random.randint(750, 1000)
        self.d = random.uniform(12, 18)
        self.e = random.randint(300, 650)
        self.f = random.uniform(18, 22)

    def motion(self, t: float) -> float:
        """Returns a Y-offset using a combination of wave functions."""
        return (
            self.a * math.sin(self.b * t)
            + self.c * math.sin(self.d * t)
            + self.e * math.cos(self.f * t)
        )

    def update_position(self, bar_top: int, bar_bottom: int):
        """Calculates and applies the new fish Y-coordinate on the canvas."""
        self.wave_x += self.wave_speed
        offset = self.motion(self.wave_x) * 0.15
        offset = max(min(offset, 500), -500)


        bar_mid = (bar_top + bar_bottom) // 2
        self.y = bar_mid + offset

        # Collision detection with fishing bar boundaries
        top_limit = bar_top + self.radius
        bottom_limit = bar_bottom - self.radius
        self.y = max(min(self.y, bottom_limit), top_limit)

        if self.is_image:
            self.canvas.coords(self.canvas_item, self.x, self.y)
        else:
            self.canvas.coords(
                self.canvas_item,
                self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius
            )

        self.canvas.tag_raise(self.canvas_item)

    def check_in_bar(self, green_coords: list) -> bool:
        """Checks if the fish overlaps with the green catcher bar."""
        fish_coords = [
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius
        ]

        if green_coords[1] < fish_coords[3] and green_coords[3] > fish_coords[1]:
            self.in_bar = True
            self.time_in_bar += 1
        else:
            self.in_bar = False

        return self.in_bar

    def update_difficulty(self, fishing_progress: float) -> float:
        """Dynamic difficulty adjustment based on how long it took to catch the fish."""
        difficulty = fishing_progress / self.time_in_bar
        if difficulty <= 0.4 and self.wave_speed > 0.001:
            print("game too hard")
            return -0.001
        elif difficulty > 0.4:
            print("game too easy")
            return 0.0015

#==============================
# CONFIGURE AVAILABLE FISH
#==============================
fish_types = [
    {"name": "anchovy", "rarity": 80, "image": "anchovy.png"},
    {"name": "carp", "rarity": 80, "image": "carp.png"},
    {"name": "flounder", "rarity": 60, "image": "flounder.png"},
    {"name": "catfish", "rarity": 60, "image": "catfish.png"},
    {"name": "pufferfish", "rarity": 35, "image": "pufferfish.png"},
    {"name": "salmon", "rarity": 35, "image": "salmon.png"},
    {"name": "eel", "rarity": 15, "image": "eel.png"},
    {"name": "tuna", "rarity": 15, "image": "tuna.png"},
    {"name": "giant squid", "rarity": 5, "image": "giant_squid.png"},
    {"name": "hammerhead shark", "rarity": 5, "image": "hammerhead_shark.png"},
]

# ===============================================
# GAME SETUP
# ===============================================

window = tk.Tk()
window.title("Bit Fisher🎣")
window_width = window.winfo_screenwidth()
window_height = window.winfo_screenheight()
window.geometry("%dx%d" % (window_width, window_height))

fish_count_file = "fish_count.csv"
performance_file = "performance_log.csv"
fish_type_count_file = "fish_type_counts.csv"

# Create performance file if missing
if not os.path.exists(performance_file):
    with open(performance_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["fish_number", "performance"])

# ============================================================
# INITIAL VARIABLE SECTION
# ============================================================
# Circle Progress bar parameters
radius_outer = 130
radius_inner = 75
fishing_progress = 0
progress_arc = None
progress_center_x = window_width - 220
progress_center_y = window_height - 680

# Main fishing area boundaries
fishing_width = 150
fishing_height = 700
fishing_x1 = window_width - fishing_width - 500
fishing_y1 = window_height - fishing_height - 120
fishing_x2 = fishing_x1 + fishing_width
fishing_y2 = fishing_y1 + fishing_height

# Green catcher bar parameters
green_width = fishing_width
green_height = 75
green_x = (fishing_x1 + fishing_x2) // 2
green_y = fishing_y1 + 50

# Movement physics
gravity = 10
lift = -10
velocity = 0
space_pressed = False

fish_caught = 0

canvas = tk.Canvas(window, width=window_width, height=window_height, bg=bg_colour)
canvas.pack()

#==========================
# LOAD AND SAVE FUNCTIONS
#==========================

fish_type_counts = {}

def load_fish_type_counts():
    """Reads the types of fish from a CSV file"""
    global fish_type_counts
    fish_type_counts = {f["name"]: 0 for f in fish_types}

    if os.path.exists(fish_type_count_file):
        with open(fish_type_count_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    name, count = row
                    if name in fish_type_counts:
                        fish_type_counts[name] = int(count)


def save_fish_type_counts():
    """Persists the caught fish total to a CSV file."""
    with open(fish_type_count_file, "w", newline="") as f:
        writer = csv.writer(f)
        for name, count in fish_type_counts.items():
            writer.writerow([name, count])


def load_fish_count():
    """Reads the total lifetime caught fish from a CSV file."""
    global fish_caught
    if os.path.exists(fish_count_file):
        try:
            with open(fish_count_file, "r") as file:
                value = file.read().strip()
                fish_caught = int(value) if value.isdigit() else 0
        except:
            fish_caught = 0
    else:
        fish_caught = 0

load_fish_count()
load_fish_type_counts()

def save_fish_count():
    """Persists the caught fish total to a CSV file."""
    try:
        with open(fish_count_file, "w") as file:
            file.write(str(fish_caught))
    except:
        print("Unable to save fish count.")

def save_performance(fish_number, performance):
    """Persists the performance of player to a CSV file."""
    with open(performance_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([fish_number, performance])

# ==========================================================
# DEFINING FUNCTION SECTION
# ==========================================================

def space_down(event):
    global space_pressed
    if not paused:
        space_pressed = True

def space_up(event):
    global space_pressed
    space_pressed = False

window.bind("<KeyPress-space>", space_down)
window.bind("<KeyRelease-space>", space_up)

# ==========================================================
# DRAW FISH TYPE COLLECTION
# ==========================================================

fish_display_items = []

def draw_fish_collection():
    """Draws the fish collection with sprite, name and in rarity category"""
    global fish_display_items

    for item in fish_display_items:
        canvas.delete(item)
    fish_display_items = []

    start_x = 50
    start_y = 40
    cell_w = 200
    cell_h = 150

    for i, fish_info in enumerate(fish_types):
        row = i // 2
        col = i % 2

        x = start_x + col * cell_w
        y = start_y + row * cell_h

        img_path = os.path.join(IMAGE_DIR, fish_info["image"])
        try:
            img_raw = Image.open(img_path).resize((80, 80))
            img = ImageTk.PhotoImage(img_raw)
        except:
            img = None

        if img:
            sprite = canvas.create_image(x, y, image=img, anchor="nw")
            fish_display_items.append(sprite)
            fish_info["display_img"] = img
        else:
            rect = canvas.create_rectangle(x, y, x+80, y+80, fill="grey")
            fish_display_items.append(rect)

        # Fish name
        name_text = canvas.create_text(
            x + 40, y + 95,
            text=fish_info["name"],
            font=(font, 14),
            fill=txt_colour_dark
        )
        fish_display_items.append(name_text)

        # Count
        count = fish_type_counts.get(fish_info["name"], 0)
        txt = canvas.create_text(
            x + 100, y + 40,
            text=f"x {count}",
            font=(font, 20),
            fill=txt_colour_dark,
            anchor="w"
        )
        fish_display_items.append(txt)

draw_fish_collection()

# ==========================================================
# DEFINING PAUSE MENU FUNCTIONS
# ==========================================================
paused = False

def pause_game(event=None):
    """Halts game loops and creates a Toplevel UI for pausing."""
    global paused
    paused = True

    popup = tk.Toplevel(window)
    popup.title("Pause")
    popup.geometry("500x300")
    popup.grab_set()

    tk.Label(popup, text="Want to end the game?", font=(font, 30), fg=txt_colour_dark).pack(pady=30)

    def quit_game():
        save_fish_count()
        save_fish_type_counts()
        show_performance_graph()
        window.destroy()

    def resume_game():
        global paused
        popup.destroy()
        paused = False

    tk.Button(popup,
              font=(font, 25),
              width=5,
              height=1,
              text="Yes",
              command=quit_game,
              bg=bg_red,
              activebackground=active_red,
              fg=txt_colour_light).pack(side="left", expand=True, padx=20)
    tk.Button(popup,
              font=(font, 25),
              width=5,
              height=1,
              text="No",
              command=resume_game,
              bg=bg_green,
              activebackground=active_green,
              fg=txt_colour_light).pack(side="right", expand=True, padx=20)

window.bind("<Escape>", pause_game)

# Create initial fish
fish = Fish(
    canvas,
    (fishing_x1 + fishing_x2) // 2,
    fishing_y1 + 500,
    40,
    fish_types
)
fish.wave_speed += initial_difficulty
level = round(fish.wave_speed * 1000)

# ================================
# MAIN GAME FUNCTIONS
# ================================

def caught_fish():
    """Handles logic for when the progress bar reaches 100%."""
    global fish_caught, fish, level, fishing_progress
    canvas.delete(fish.canvas_item)

    fish_caught += 1
    save_fish_count()

    # Update fish type count
    fish_type_counts[fish.type_name] += 1
    save_fish_type_counts()
    draw_fish_collection()

    adjusted_difficulty = fish.update_difficulty(fishing_progress)
    performance_value = fishing_progress / max(fish.time_in_bar, 1)
    save_performance(fish_caught, performance_value)

    fish = Fish(
        canvas,
        (fishing_x1 + fishing_x2) // 2,
        fishing_y1 + 500,
        40,
        fish_types
    )
    fish.wave_speed += initial_difficulty
    fish.wave_speed += adjusted_difficulty



def update_progress_bar():
    """Main game loop for managing the circular progress meter."""
    global fishing_progress, level, fish_caught, fish

    if paused:
        window.after(30, update_progress_bar)
        return

    if fish.in_bar:
        fishing_progress += 0.5
        if fishing_progress >= 100:
            caught_fish()
            level = round(fish.wave_speed * 1000)
            print(level)
            fishing_progress = 0

            canvas.itemconfig(
                stats_display,
                text=f"Hold SPACE to raise the green bar\nOr press ESC to pause\nKeep the fish inside!\n\nFish Caught: {fish_caught}\nDifficulty: {level}"
            )

    else:
        fishing_progress -= 0.1
        fishing_progress = max(fishing_progress, 0)

    draw_progress()
    window.after(30, update_progress_bar)

def show_performance_graph():
    """Draw the performance over fish caught graph"""
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button

    fish_numbers = []
    performances = []

    # Load saved performance data
    if os.path.exists(performance_file):
        with open(performance_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fish_numbers.append(int(row["fish_number"]))
                performances.append(float(row["performance"]))

    if not fish_numbers:
        return  # nothing to plot

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(bottom=0.3)  # make room for 2 buttons

    ax.plot(fish_numbers, performances, marker="o", color=txt_colour_dark)
    ax.set_title("Player Performance Over Time")
    ax.set_xlabel("Fish Number")
    ax.set_ylabel("Performance Score")
    ax.grid(True)


    # --- Exit Button ---
    exit_ax = fig.add_axes([0.18, 0.1, 0.3, 0.12])  # x, y, width, height
    exit_button = Button(exit_ax, "Exit Game", color=bg_green, hovercolor=active_green)
    exit_button.label.set_fontsize(18)
    exit_button.label.set_color(txt_colour_light)
    def exit_all(event):
        plt.close('all')
        os._exit(0)  # force close all Tk windows and Python process

    exit_button.on_clicked(exit_all)

    # --- Clear Data Button ---
    clear_ax = fig.add_axes([0.55, 0.1, 0.3, 0.12])
    clear_button = Button(clear_ax, "Clear All Saved Data", color=bg_grey, hovercolor=active_grey)
    clear_button.label.set_fontsize(18)
    clear_button.label.set_color(txt_colour_light)
    def clear_data(event):
        # Clear performance file
        with open(performance_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["fish_number", "performance"])

        # Clear fish count file
        with open(fish_count_file, "w") as f:
            f.write("0")

        # CLear fish type file
        with open(fish_type_count_file, "w") as f:
            f.write(" ")

        # Give visual confirmation
        ax.clear()
        ax.text(0.5, 0.5, "All Data Cleared!", ha="center", va="center", fontsize=20)
        fig.canvas.draw_idle()

    clear_button.on_clicked(clear_data)

    plt.show()


def draw_progress():
    """Updates the visual arc of the circular progress bar."""
    global progress_arc
    if progress_arc:
        try:
            canvas.delete(progress_arc)
        except:
            pass

    if fishing_progress > 0:
        extent = (fishing_progress / 100) * 360
        progress_arc = canvas.create_arc(
            progress_center_x - radius_outer, progress_center_y - radius_outer,
            progress_center_x + radius_outer, progress_center_y + radius_outer,
            start=90, extent=-extent, fill=bg_green, outline=green_outline_colour
        )

    canvas.tag_raise(inner_circle)

def update_greenbar():
    """Physics loop for the catcher bar movement (gravity vs player lift)."""
    global green_y, velocity

    if paused:
        window.after(30, update_greenbar)
        return

    velocity = lift if space_pressed else gravity
    green_y += velocity

# Keep catcher bar within the vertical fishing lane
    top_limit = fishing_y1 + green_height // 2
    bot_limit = fishing_y2 - green_height // 2
    green_y = max(min(green_y, bot_limit), top_limit)

    canvas.coords(green_bar,
                  green_x - green_width // 2, green_y - green_height // 2,
                  green_x + green_width // 2, green_y + green_height // 2
                  )

    window.after(30, update_greenbar)

def check_if_fish_in_bar():
    """Triggers the fish's collision detection and updates the UI timer."""
    if paused:
        window.after(30, check_if_fish_in_bar)
        return

    green_coords = canvas.coords(green_bar)
    fish.check_in_bar(green_coords)

    canvas.itemconfig(timer_text, text=f"Time fish in bar: {fish.time_in_bar}")

    window.after(30, check_if_fish_in_bar)

def update_fish():
    """Loop to update the fish's movement position."""
    if paused:
        window.after(30, update_fish)
        return

    fish.update_position(fishing_y1, fishing_y2)
    window.after(30, update_fish)

# =============================================
# DRAWING THE WIDGETS ONTO THE CANVAS
# =============================================

# Background circles for progress meter
canvas.create_oval(progress_center_x - radius_outer, progress_center_y - radius_outer,
                   progress_center_x + radius_outer, progress_center_y + radius_outer,
                   fill=active_grey, outline=green_outline_colour)
inner_circle = canvas.create_oval(progress_center_x - radius_inner, progress_center_y - radius_inner,
                                  progress_center_x + radius_inner, progress_center_y + radius_inner,
                                  fill=bg_colour, outline=green_outline_colour)

# Main fishing lane rectangle
canvas.create_rectangle(fishing_x1, fishing_y1, fishing_x2, fishing_y2,
                        fill=active_grey, outline=blue_outline_colour)

green_bar = canvas.create_rectangle(
    green_x - green_width // 2, green_y - green_height // 2,
    green_x + green_width // 2, green_y + green_height // 2,
    fill=bg_green, outline=green_outline_colour
)

# ==========================================================
# STATS DISPLAY SECTION
# ==========================================================

stats_display = canvas.create_text(
    window_width - 50,
    window_height - 200,
    text=f"Hold SPACE to raise the green bar\nOr press ESC to pause\nKeep the fish inside!\n\nFish Caught: {fish_caught}\nDifficulty: {level}",
    anchor='se',
    font=(font, 20),
    fill=txt_colour_dark
)

timer_text = canvas.create_text(
    window_width - 700,
    window_height - 150,
    text="Time fish in bar: 0",
    font=(font, 14),
    fill=txt_colour_dark,
    anchor="se"
)

# Start all recursive game loops
draw_progress()
update_progress_bar()
check_if_fish_in_bar()
update_greenbar()
update_fish()

window.mainloop()
