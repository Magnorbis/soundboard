import threading
from functools import partial
import ttkbootstrap as ttk
from config import config, save_config
from ui import build_ui, play_sound
from voicemeeter import vm_connect
import hotkeys
import tray
import sys
import os

# -------------------- CONFIG --------------------
ROWS = 3
COLS = 4
TOTAL = ROWS * COLS

# -------------------- VOICEMEETER --------------------
# Attempt to connect to Voicemeeter banana
vm = None
try:
    vm_context = vm_connect("banana")
    vm = vm_context.__enter__()
    print("Connected to Voicemeeter")
except Exception as e:
    print(f"Not connected to Voicemeeter: {e}")
    vm = None

# Wrap play_sound so vm and config are automatically passed
play_sound_with_vm = partial(play_sound, vm, config)

# -------------------- MAIN WINDOW --------------------
# Create the main Tkinter window
root = ttk.Window(themename="darkly")
root.title("Soundboard")
root.geometry("1200x800")
root.configure(bg="#444444")

# Get .ico
if getattr(sys, "frozen", False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

icon_path = os.path.join(base_path, "assets", "soundboard.ico")
root.iconbitmap(icon_path)

# Configure grid rows and columns to expand evenly
for r in range(ROWS):
    root.grid_rowconfigure(r, weight=1)
for c in range(COLS):
    root.grid_columnconfigure(c, weight=1)

# Build the UI grid of sound buttons
cards = build_ui(root, config, save_config, play_sound_with_vm, ROWS, COLS)
save_config(config)

# -------------------- HOTKEY THREAD --------------------
# Register global hotkeys and keep the listener running
def hotkey_thread():
    hotkeys.register_hotkeys(config, play_sound_with_vm)
    import keyboard
    keyboard.wait()

# Start the hotkey listener in a separate daemon thread
threading.Thread(target=hotkey_thread, daemon=True).start()

# -------------------- SYSTEM TRAY --------------------
# Restore and focus the main window from the system tray
def show_window():
    root.deiconify()
    root.lift()
    root.focus_force()

# Quit the application and disconnect from Voicemeeter.
def quit_app(icon=None):
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

# Hide the window instead of closing and show system tray icon.
def on_close():
    root.withdraw()
    tray.setup_tray(quit_app, show_window)

# Override the default close behavior
root.protocol("WM_DELETE_WINDOW", on_close)

# -------------------- RUN --------------------
# Start the Tkinter main event loop
root.mainloop()
