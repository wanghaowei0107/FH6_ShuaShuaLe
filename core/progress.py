import configparser
import os
import threading

PROGRESS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "config", "progress.ini")

_lock = threading.Lock()

def load_progress(section):
    config = configparser.ConfigParser()
    config.read(PROGRESS_FILE)
    if section not in config:
        return 0, 0
    total = config.getint(section, "total", fallback=0)
    done = config.getint(section, "completed", fallback=0)
    return total, done

def save_total(section, total):
    with _lock:
        config = configparser.ConfigParser()
        config.read(PROGRESS_FILE)
        if section not in config:
            config.add_section(section)
        config.set(section, "total", str(total))
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, "w") as f:
            config.write(f)

def save_completed(section, done):
    with _lock:
        config = configparser.ConfigParser()
        config.read(PROGRESS_FILE)
        if section not in config:
            config.add_section(section)
        config.set(section, "completed", str(done))
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, "w") as f:
            config.write(f)