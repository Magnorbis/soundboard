import ttkbootstrap as ttk
from tkinter import filedialog, simpledialog, messagebox
import json
import os
import threading
import keyboard
from functools import partial
import pystray
from PIL import Image, ImageDraw
from voicemeeter import vm_connect
import pygame

CONFIG_FILE = "config.json"
ROWS = 3
COLS = 4
TOTAL = ROWS * COLS
hotkey_handles = {}


# -------------------- CONFIG --------------------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write("{}")

    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        with open(CONFIG_FILE, "w") as f:
            f.write("{}")
        return {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

config = load_config()


# -------------------- VOICEMEETER CONNECTION --------------------
vm = None

try:
    vm_context = vm_connect("banana")
    vm = vm_context.__enter__()
    print("Connected to Voicemeeter")
except Exception as e:
    print(f"Not connected to Voicemeeter: {e}")
    vm = None

def is_vm_ready():
    return vm is not None

# -------------------- SOUNDS  --------------------
pygame.mixer.init(frequency=44100, channels=2)
os.environ["SDL_AUDIODRIVER"] = "directsound"

def play_sound(key):
    info = config.get(key)
    if not info:
        return

    file_path = info.get("file")
    if not file_path or not os.path.exists(file_path):
        messagebox.showwarning("Missing File", f"No valid file for '{info['name']}'")
        return

    if not vm or not is_vm_ready():
        messagebox.showerror("Voicemeeter Error", "Not connected to Voicemeeter")
        return

    try:

        vm.set("Recorder.stop", 1)
        vm.set("Recorder.load", file_path)

        volume = float(info.get("volume", 1.0))
        vm.set("Recorder.gain", volume * 12.0 - 12.0)

        vm.set("Recorder.play", 1)

    except Exception as e:
        messagebox.showerror("Playback error", str(e))

# -------------------- GUI --------------------
root = ttk.Window(themename="darkly")
root.title("Soundboard")
root.geometry("1200x800")
root.configure(bg="#444444")

for r in range(ROWS):
    root.grid_rowconfigure(r, weight=1)

for c in range(COLS):
    root.grid_columnconfigure(c, weight=1)

cards = {}

shifted_to_base = {
    "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
    "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
    "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
    ":": ";", '"': "'", "<": ",", ">": ".", "?": "/"
}

modifiers_map = {"Shift_L": "Shift", "Shift_R": "Shift",
                 "Control_L": "Ctrl", "Control_R": "Ctrl",
                 "Alt_L": "Alt", "Alt_R": "Alt"}


# -------------------- UTILS --------------------
def choose_file(key):
    file = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.ogg")])
    if file:
        config[key]["file"] = file
        save_config()

def rename(key, label):
    new = simpledialog.askstring("Rename", "Button name:", initialvalue=config[key]["name"])
    if new:
        config[key]["name"] = new
        label.config(text=new)
        save_config()

def update_volume(key, var, label):
    val = round(var.get(), 2)
    config[key]["volume"] = val
    label.config(text=f"{val:.2f}")


# -------------------- SHORTCUT --------------------
def set_shortcut(key, label):
    popup = ttk.Toplevel(root)
    popup.title("Set Shortcut")
    popup.geometry("300x100")
    popup.grab_set()
    ttk.Label(popup, text="Press the key(s) for this button").pack(expand=True, fill="both", padx=10, pady=10)

    pressed_mods = set()
    main_key = None

    def on_press(event):
        if event.keysym in modifiers_map:
            pressed_mods.add(modifiers_map[event.keysym])
        else:
            nonlocal main_key
            if event.char and event.char.isprintable():
                main_key = event.char
            elif event.keysym == "Multi_key":
                main_key = "^"
            else:
                main_key = event.keysym

    def on_release(event):
        nonlocal main_key
        if event.keysym == "Escape":
            if key in hotkey_handles:
                try:
                    keyboard.remove_hotkey(hotkey_handles[key])
                except KeyError:
                    pass
                del hotkey_handles[key]

            config[key]["shortcut"] = ""
            label.config(text="Not set")
        else:
            combo_parts = sorted(pressed_mods)
            if main_key:
                key_name = main_key
                if "Shift" in pressed_mods and main_key in shifted_to_base:
                    key_name = shifted_to_base[main_key]
                if key_name.isalpha():
                    key_name = key_name.upper()
                combo_parts.append(key_name)

            combo = "+".join(combo_parts)

            if key in hotkey_handles:
                try:
                    keyboard.remove_hotkey(hotkey_handles[key])
                except KeyError:
                    pass

            try:
                handle = keyboard.add_hotkey(combo, partial(play_sound, key))
                hotkey_handles[key] = handle
                config[key]["shortcut"] = combo
                cards[key]["shortcut_label"].config(text=combo)
            except ValueError:
                messagebox.showerror("Shortcut Error", f"Invalid shortcut: {combo}")
                main_key = None
                pressed_mods.clear()
                return

        main_key = None
        pressed_mods.clear()
        save_config()
        popup.destroy()

    popup.bind("<KeyPress>", on_press)
    popup.bind("<KeyRelease>", on_release)
    popup.focus_set()


# -------------------- BUILD GRID --------------------
for i in range(TOTAL):
    key = f"slot_{i}"
    if key not in config:
        config[key] = {
            "name": f"Sound {i+1}",
            "file": "",
            "volume": 1.0,
            "shortcut": ""
        }

    r = i // COLS
    c = i % COLS

    style = ttk.Style()
    style.configure('TButton', font=("Segoe UI", 12))

    card = ttk.Frame(root, padding=(8,8), bootstyle="bg")
    card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)
    card.grid_rowconfigure(0, weight=1)
    card.grid_columnconfigure(0, weight=1)

    name_label = ttk.Label(card, text=config[key]["name"], font=("Segoe UI", 14, "bold"))
    name_label.pack(pady=(0, 6))

    play_btn = ttk.Button(card, text="Play", bootstyle="success", command=lambda k=key: play_sound(k))
    play_btn.pack(fill="x")

    rename_row = ttk.Frame(card)
    rename_row.pack(fill="x", pady=(4, 0))
    rename_btn = ttk.Button(rename_row, text="Rename", bootstyle="info", command=lambda k=key, l=name_label: rename(k, l))
    rename_btn.pack(side="left", expand=True, fill="x")

    file_row = ttk.Frame(card)
    file_row.pack(fill="x", pady=(4, 0))
    file_btn = ttk.Button(file_row, text="File", bootstyle="secondary", command=lambda k=key: choose_file(k))
    file_btn.pack(side="left", expand=True, fill="x")

    shortcut_row = ttk.Frame(card)
    shortcut_row.pack(fill="x", pady=(4, 0))
    shortcut_btn = ttk.Button(shortcut_row, text="Set Shortcut", bootstyle="warning", command=lambda k=key: set_shortcut(k, cards[k]["shortcut_label"]))
    shortcut_btn.pack(side="left", expand=True, fill="x")
    shortcut_label = ttk.Label(shortcut_row, text=config[key].get("shortcut") or "Not set", anchor="center", width=12, font=("Segoe UI", 12, "bold"))
    shortcut_label.pack(side="left", padx=4)

    vol_row = ttk.Frame(card)
    vol_row.pack(fill="x", pady=(4, 0))

    vol = ttk.DoubleVar(value=config[key]["volume"])
    vol_slider = ttk.Scale(vol_row, from_=0.0, to=1.0, variable=vol, command=lambda val, k=key, v=vol: update_volume(k, v, cards[k]["vol_label"]))
    vol_slider.pack(side="left", fill="x", expand=True, padx=4)

    vol_value = ttk.Label(vol_row, text=f"{vol.get():.2f}", width=4)
    vol_value.pack(padx=(6, 0))

    cards[key] = {"vol_label": vol_value, "shortcut_label": shortcut_label}

save_config()


# -------------------- GLOBAL HOTKEYS --------------------
def register_hotkeys():
    for key, info in config.items():
        shortcut = info.get("shortcut")
        if shortcut:
            try:
                keyboard.add_hotkey(shortcut, partial(play_sound, key))
            except ValueError:
                print(f"Invalid shortcut: {shortcut}")

def hotkey_thread():
    register_hotkeys()
    keyboard.wait()

threading.Thread(target=hotkey_thread, daemon=True).start()


# -------------------- SYSTEM TRAY --------------------
tray_icon = None

def create_icon():
    img = Image.new("RGB", (64, 64), color=(0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([16,16,48,48], fill=(255,0,0))
    return img

def show_window(icon=None, item=None):
    root.deiconify()
    root.lift()
    root.focus_force()

def quit_app(icon=None, item=None):
    if icon:
        icon.stop()

    global vm
    if vm:
        try:
            vm.__exit__(None, None, None)
        except Exception:
            pass
        vm = None

    root.after(100, root.destroy)

def setup_tray():
    global tray_icon
    if tray_icon is None:
        tray_icon = pystray.Icon("Soundboard", create_icon(), "Soundboard", menu=pystray.Menu(
            pystray.MenuItem("Show", show_window),
            pystray.MenuItem("Quit", quit_app)
        ))
        tray_icon.run_detached()

def on_close():
    root.withdraw()
    setup_tray()

root.protocol("WM_DELETE_WINDOW", on_close)


# -------------------- RUN --------------------
root.mainloop()
