import pystray
from PIL import Image
import sys
import os

# Holds the system tray icon instance
tray_icon = None

# Create a simple icon image for the system tray
def create_icon():
    # Get .ico
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    icon_path = os.path.join(base_path, "assets", "soundboard.ico")

    return Image.open(icon_path)

# Initialize and display the system tray icon with show and quit actions
def setup_tray(quit_app, show_window):
    global tray_icon
    if tray_icon is None:
        tray_icon = pystray.Icon(
            "Soundboard",
            create_icon(),
            "Soundboard",
            menu=pystray.Menu(
                pystray.MenuItem("Show", show_window),
                pystray.MenuItem("Quit", quit_app)
            )
        )
        tray_icon.run_detached()
