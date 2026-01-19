import keyboard
import ttkbootstrap as ttk
from tkinter import filedialog, simpledialog, messagebox
from functools import partial
import hotkeys
import os

# Mapping of shifted symbols to their base key equivalents
shifted_to_base = {
    "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
    "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
    "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
    ":": ";", '"': "'", "<": ",", ">": ".", "?": "/"
}

# Normalize left/right modifier keys to a single name
modifiers_map = {"Shift_L": "Shift", "Shift_R": "Shift",
                 "Control_L": "Ctrl", "Control_R": "Ctrl",
                 "Alt_L": "Alt", "Alt_R": "Alt"}

# Play a sound through Voicemeeter using the given slot key
def play_sound(vm, config, key):
    info = config.get(key)
    if not info:
        return

    # Validate audio file path
    file_path = info.get("file")
    if not file_path or not os.path.exists(file_path):
        messagebox.showwarning("Missing File", f"No valid file for '{info['name']}'")
        return

    # Ensure Voicemeeter connection is available
    if not vm:
        messagebox.showerror("Voicemeeter Error", "Not connected to Voicemeeter")
        return

    try:
        # Stop any existing playback and load new file
        vm.set("Recorder.stop", 1)
        vm.set("Recorder.load", file_path)

        # Convert 0.0-1.0 slider value to Voicemeeter gain range
        volume = float(info.get("volume", 1.0))
        vm.set("Recorder.gain", -60.0 + volume * 72)

        # Start playback
        vm.set("Recorder.play", 1)
    except Exception as e:
        messagebox.showerror("Playback error", str(e))

# Stop playing the current sound
def stop_sound(vm):
    if not vm:
        return
    try:
        vm.set("Recorder.stop", 1)
    except Exception as e:
        messagebox.showerror("Voicemeeter Error", str(e))

# Open a popup window to record and assign a keyboard shortcut
def set_shortcut(key, label, root, cards, config, save_config, play_callback, stop_callback):
    if label is None:
        label = cards[key]["shortcut_label"]

    # Modal popup window to capture key presses
    popup = ttk.Toplevel(root)
    popup.title("Set Shortcut")
    popup.geometry("300x100")
    popup.grab_set()
    ttk.Label(popup, text="Press the key(s) for this button").pack(expand=True, fill="both", padx=10, pady=10)

    pressed_mods = set()
    main_key = None

    # Track modifier and main key presses
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

    # Finalize shortcut when keys are released
    def on_release(event):
        nonlocal main_key

        # Escape clears the shortcut
        if event.keysym == "Escape":
            hotkeys.remove_hotkey(key)
            config[key]["shortcut"] = ""
            label.config(text="Not set")
        else:
            combo_parts = sorted(pressed_mods)

            # Normalize shifted characters to base keys
            if main_key:
                key_name = main_key
                if "Shift" in pressed_mods and main_key in shifted_to_base:
                    key_name = shifted_to_base[main_key]
                if key_name.isalpha():
                    key_name = key_name.upper()
                combo_parts.append(key_name)

            combo = "+".join(combo_parts)

            # Remove any existing shortcut for this slot
            hotkeys.remove_hotkey(key)

            try:
                # Use stop_callback if key is the stop button
                callback = stop_callback if key == "stop" else partial(play_callback, key)

                # Register the new global hotkey
                handle = keyboard.add_hotkey(combo, callback)
                hotkeys.hotkey_handles[key] = handle
                config[key]["shortcut"] = combo
                cards[key]["shortcut_label"].config(text=combo)
            except ValueError:
                messagebox.showerror("Shortcut Error", f"Invalid shortcut: {combo}")
                main_key = None
                pressed_mods.clear()
                return

        # Reset state and close popup
        main_key = None
        pressed_mods.clear()
        save_config(config)
        popup.destroy()

    popup.bind("<KeyPress>", on_press)
    popup.bind("<KeyRelease>", on_release)
    popup.focus_set()

# Open a file dialog to select an audio file for a slot
def choose_file(key, config, save_config):
    file = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.ogg")])
    if file:
        config[key]["file"] = file
        save_config(config)

# Rename a sound slot and update its label
def rename(key, label, config, save_config):
    new = simpledialog.askstring("Rename", "Button name:", initialvalue=config[key]["name"])
    if new:
        config[key]["name"] = new
        label.config(text=new)
        save_config(config)

# Update the volume for a sound slot and persist it
def update_volume(key, var, label, config, save_config, slider_value=None):
    val = round(var.get(), 2)
    config[key]["volume"] = val
    if label:
        label.config(text=f"{val:.2f}")
    save_config(config)

# Build the main grid-based UI with sound cards and controls
def build_ui(root, config, save_config, play_sound, stop_sound, rows=3, cols=4):
    total = rows * cols
    cards = {}

    # Global button styling
    style = ttk.Style()
    style.configure('TButton', font=("Segoe UI", 12))

    for i in range(total):
        key = f"slot_{i}"

        if key not in config:
            config[key] = {"name": f"Sound {i + 1}", "file": "", "volume": 1.0, "shortcut": ""}

        r, c = i // cols, i % cols

        # Card container for a single sound slot
        card = ttk.Frame(root, padding=(8, 8), bootstyle="bg")
        card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # Slot name
        name_label = ttk.Label(card, text=config[key]["name"], font=("Segoe UI", 14, "bold"))
        name_label.pack(pady=(0, 6))

        # Play button
        play_btn = ttk.Button(card, text="Play", bootstyle="success", command=partial(play_sound, key))
        play_btn.pack(fill="x")

        # Rename button
        rename_row = ttk.Frame(card)
        rename_row.pack(fill="x", pady=(4, 0))
        rename_btn = ttk.Button(rename_row, text="Rename", bootstyle="info",
                                command=partial(rename, key, name_label, config, save_config))
        rename_btn.pack(side="left", expand=True, fill="x")

        # File picker
        file_row = ttk.Frame(card)
        file_row.pack(fill="x", pady=(4, 0))
        file_btn = ttk.Button(file_row, text="File", bootstyle="secondary",
                              command=partial(choose_file, key, config, save_config))
        file_btn.pack(side="left", expand=True, fill="x")

        # Shortcut assignment
        shortcut_row = ttk.Frame(card)
        shortcut_row.pack(fill="x", pady=(4, 0))
        shortcut_btn = ttk.Button(shortcut_row, text="Set Shortcut", bootstyle="warning",
                                  command=partial(set_shortcut, key, cards.get(key, {}).get("shortcut_label", None),
                                                  root, cards, config, save_config, play_sound, stop_sound))
        shortcut_btn.pack(side="left", expand=True, fill="x")
        shortcut_label = ttk.Label(shortcut_row, text=config[key].get("shortcut") or "Not set",
                                   anchor="center", width=12, font=("Segoe UI", 12, "bold"))
        shortcut_label.pack(side="left", padx=4)

        # Volume slider
        vol_row = ttk.Frame(card)
        vol_row.pack(fill="x", pady=(4, 0))

        vol = ttk.DoubleVar(value=config[key]["volume"])

        vol_slider = ttk.Scale(vol_row, from_=0.0, to=1.0, variable=vol)
        vol_slider.pack(side="left", fill="x", expand=True, padx=4)

        vol_value = ttk.Label(vol_row, text=f"{vol.get():.2f}", width=4)
        vol_value.pack(side="left")

        vol_slider.configure(command=lambda val, k=key, v=vol, l=vol_value: update_volume(k, v, l, config, save_config))

        cards[key] = {"vol_label": vol_value, "shortcut_label": shortcut_label}


    # Stop button with shortcut to stop any sound currently playing
    if "stop" not in config:
        config["stop"] = {"name": "Stop", "shortcut": ""}

    controls = ttk.Frame(root)
    controls.grid(row=rows, column=0, columnspan=cols, sticky="ew", padx=6, pady=(0, 8))

    stop_btn = ttk.Button(controls, text="Stop", bootstyle="danger", command=stop_sound)
    stop_btn.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

    shortcut_label = ttk.Label(controls, text=config["stop"].get("shortcut") or "Not set", anchor="center",
                               width=12, font=("Segoe UI", 12, "bold"))
    shortcut_label.grid(row=0, column=2, sticky="nsew")

    shortcut_btn = ttk.Button(controls, text="Set Shortcut", bootstyle="warning",
                              command=partial(set_shortcut, "stop", shortcut_label, root, cards, config, save_config,
                                              play_sound, stop_sound))
    shortcut_btn.grid(row=0, column=1, sticky="nsew", padx=(0, 4))

    controls.grid_columnconfigure(0, weight=4)
    controls.grid_columnconfigure(1, weight=1)
    controls.grid_columnconfigure(2, weight=1)

    cards["stop"] = {"shortcut_label": shortcut_label}

    return cards
