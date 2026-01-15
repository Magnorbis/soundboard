import keyboard
from functools import partial

# Stores active hotkey handles so they can be removed later
hotkey_handles = {}

# Register all configured keyboard shortcuts and link them to sound playback
def register_hotkeys(config, play_sound):
    for key, info in config.items():
        shortcut = info.get("shortcut")
        if shortcut:
            try:
                handle = keyboard.add_hotkey(shortcut, partial(play_sound, key))
                hotkey_handles[key] = handle
            except ValueError:
                print(f"Invalid shortcut: {shortcut}")

# Remove a previously registered hotkey for a specific sound slot
def remove_hotkey(key):
    if key in hotkey_handles:
        try:
            keyboard.remove_hotkey(hotkey_handles[key])
        except KeyError:
            pass
        del hotkey_handles[key]
