import json
import os
import sys

# Get the path to the config.json file - appdata OR working directory
def get_config_path():
    if getattr(sys, "frozen", False):
        base_path = os.path.join(os.environ["APPDATA"], "Soundboard")
        os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, "config.json")
    else:
        return os.path.join(os.path.abspath("."), "config.json")

# Path to the configuration file
CONFIG_FILE = get_config_path()

# Load the configuration from CONFIG_FILE, create empty if missing or invalid
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

# Save the given configuration dictionary to CONFIG_FILE
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# Load the configuration when this module is imported
config = load_config()
