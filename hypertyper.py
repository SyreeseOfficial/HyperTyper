#!/usr/bin/env python3
import contextlib
import functools
import glob
import json
import os
import random
import re
import select
import shutil
import sys
import time
import unicodedata

try:
    import termios, tty
    msvcrt = None
except ImportError:  # Windows
    import msvcrt
    termios = None

# --- ANSI colors (plain escape codes; no colorama needed) ---
if os.name == "nt":
    os.system("")  # turns on ANSI escape processing in the Windows console

class Fore:
    RED, GREEN, YELLOW, CYAN, MAGENTA, WHITE = (f"\033[{n}m" for n in (31, 32, 33, 36, 35, 37))
    BLUE, ORANGE = "\033[94m", "\033[38;5;208m"

class Style:
    BRIGHT, UNDERLINE, RESET_ALL = "\033[1m", "\033[4m", "\033[0m"

# Right/wrong signals. apply_theme() swaps them for a colorblind-safe pair (blue vs underlined orange).
GOOD, BAD = Fore.GREEN, Fore.RED

# --- Configuration & Data ---
SOUNDS = {}
SOUND_FILES = {
    "splash": "splash.wav",
    "countdown": "countdown.wav",
    "correct": "correct.wav",
    "levelup": "levelup.wav",
    "gameover": "gameover.wav",
    "victory": "victory.wav",
}

APP_NAME = "hypertyper"

# 1. Data Directory (Read-only assets: words, sounds)
# Check local first (dev mode), then system install path
local_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if os.path.exists(local_data):
    DATA_DIR = local_data
else:
    # Standard Linux install path
    DATA_DIR = os.path.join("/usr/share", APP_NAME, "data")

# 2. Config Directory (Writable: settings, highscores, history, your own word lists)
# Use XDG_CONFIG_HOME or default to ~/.config
xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
CONFIG_DIR = os.path.join(xdg_config, APP_NAME)

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

HIGHSCORE_FILE = os.path.join(CONFIG_DIR, "highscores.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.jsonl")
WORDS_DIR = os.path.join(CONFIG_DIR, "words")  # any *.txt in here becomes a mode

BACKUP_WORDS = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "lemon", "lime", "mango"]

# (menu name, word file, exact_match). The name is also the high-score key.
MODES = [
    ("Streak", "words.txt", False),
    ("Cities", "capitals.txt", True),
    ("Food", "foods.txt", False),
    ("Animals", "animals.txt", False),
    ("Lorem", "lorem.txt", False),
    ("Code Snippets", "code.txt", True),
    ("Terminal Commands", "terminal.txt", True),
    ("Brainrot", "brainrot.txt", True),
    ("UwU", "uwu.txt", True),
    ("LinkedIn Jargon", "linkedin.txt", True),
    ("Spanish", "spanish.txt", False),
    ("Pokemon", "pokemon.txt", False),
    ("Quotes", "quotes.txt", True),
]

# Word-length filter for the word-based (non exact-match) modes: (min, max) letters.
LENGTHS = {"all": (0, 99), "short": (0, 5), "medium": (6, 8), "long": (9, 99)}

ACHIEVEMENTS = [  # (name, description, test on a finished run's history record)
    ("God Mode", "Reach a 12-word combo", lambda r: r.get("best_combo", 0) >= 12),
    ("Speed Demon", "Hit 50 WPM", lambda r: r.get("wpm", 0) >= 50),
    ("Centurion", "Type 100 words in one run", lambda r: r.get("words", 0) >= 100),
]

MIN_COLS, MIN_ROWS = 60, 15

DEFAULT_SETTINGS = {
    "sound": True,
    "volume": 100,
    "time_limit": 30,
    "show_timer": True,
    "practice": False,
    "difficulty": "all",
    "colorblind": False,
}
SETTINGS = DEFAULT_SETTINGS.copy()

# --- Helper Functions ---

def load_settings():
    """Loads settings from SETTINGS_FILE, creating it with defaults if missing."""
    global SETTINGS

    if not os.path.exists(SETTINGS_FILE):
        SETTINGS = DEFAULT_SETTINGS.copy()
        save_settings(SETTINGS)
        return

    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            SETTINGS = DEFAULT_SETTINGS.copy()
            SETTINGS.update(data)
    except (json.JSONDecodeError, IOError):
        SETTINGS = DEFAULT_SETTINGS.copy()
        save_settings(SETTINGS)

def save_settings(new_settings):
    """Saves the settings dict to SETTINGS_FILE."""
    global SETTINGS
    SETTINGS = new_settings

    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(SETTINGS, f, indent=4)
    except IOError:
        print(f"\n{Fore.RED}Warning: Could not save settings.{Style.RESET_ALL}")

def apply_theme():
    """Picks the right/wrong colors for the current palette setting."""
    global GOOD, BAD
    if SETTINGS["colorblind"]:
        GOOD, BAD = Fore.BLUE, Fore.ORANGE + Style.UNDERLINE
    else:
        GOOD, BAD = Fore.GREEN, Fore.RED

@functools.lru_cache(maxsize=None)
def load_words(path, exact_match=False):
    """Loads unique lines from `path` (file order kept). Falls back to BACKUP_WORDS if needed.
    If exact_match is True, preserves case and allows punctuation/spaces.
    Cached per (path, exact_match); callers must not mutate the result.
    """
    words = []
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                for line in f:
                    if exact_match:
                        # Just strip newlines, keep content as is
                        w = line.strip()
                        if w:
                            words.append(w)
                    else:
                        # Standard mode logic
                        w = line.strip().lower()
                        if len(w) >= 3 and w.isalpha():
                            words.append(w)
        except IOError:
            pass # Keep list empty to trigger backup

    words = list(dict.fromkeys(words))  # a repeated line would otherwise come up more often
    if not words:
        print(f"Warning: {path} not found or empty, using backup list.")
        return BACKUP_WORDS

    return words

def pick_words(words, exact_match):
    """Applies the difficulty (word length) setting to word-based modes."""
    lo, hi = LENGTHS.get(SETTINGS["difficulty"], LENGTHS["all"])
    picked = [] if exact_match else [w for w in words if lo <= len(w) <= hi]
    return picked if len(picked) >= 10 else words  # too few left: ignore the filter

def word_bag(words):
    """Yields every word once per shuffle, never the same word twice in a row."""
    last = None
    while True:
        bag = random.sample(words, len(words))
        if len(bag) > 1 and bag[0] == last:
            bag[0], bag[-1] = bag[-1], bag[0]
        yield from bag
        last = bag[-1]

def get_modes():
    """Built-in MODES plus one exact-match mode per ~/.config/hypertyper/words/*.txt."""
    builtin = [(name, os.path.join(DATA_DIR, f), exact) for name, f, exact in MODES]
    custom = [(os.path.splitext(os.path.basename(p))[0], p, True)
              for p in sorted(glob.glob(os.path.join(WORDS_DIR, "*.txt")))]
    return builtin + custom

def score_key(name, exact_match):
    """High-score key: records are per mode, timer length, difficulty (word modes only) and practice."""
    diff = SETTINGS["difficulty"]
    return (f"{name}@{int(SETTINGS['time_limit'])}s"
            + ("" if exact_match or diff == "all" else f" {diff}")
            + (" practice" if SETTINGS["practice"] else ""))

def init_audio():
    """Loads sounds. pygame is imported only here, and only when sound is on. Safe to call repeatedly."""
    if SOUNDS or not SETTINGS["sound"]:
        return
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import pygame
        pygame.mixer.init()
    except Exception as e:  # not installed, or no audio device
        print(f"{Fore.YELLOW}Audio disabled: {e}{Style.RESET_ALL}")
        return

    base_path = os.path.join(DATA_DIR, "sounds")
    for name, filename in SOUND_FILES.items():
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            try:
                SOUNDS[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"{Fore.RED}Failed to load {filename}: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Warning: Sound file '{filename}' not found.{Style.RESET_ALL}")
    apply_volume()

def apply_volume():
    for s in SOUNDS.values():
        s.set_volume(SETTINGS["volume"] / 100)

def play_sound(name):
    """Plays a sound by name if available."""
    if SETTINGS["sound"] and name in SOUNDS:
        try:
            SOUNDS[name].play()
        except Exception:
            pass

ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def get_visible_length(s):
    """Returns the length of the string in terminal columns, without ANSI color codes."""
    # East Asian Wide/Fullwidth chars (incl. emoji) take 2 terminal columns
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in ANSI_RE.sub('', s))

def fold(s):
    """Drops accents (n for ñ) so any keyboard can type any word."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))

def same(typed, target):
    return fold(typed) == fold(target)

def wpm(chars, seconds):
    """Standard WPM: 5 chars = 1 word, over the elapsed time (at least 1 s)."""
    return (chars / 5.0) / (max(seconds, 1.0) / 60.0)

def get_combo_tier(combo):
    """
    Returns (tier_name, multiplier, color_code) based on combo count.
    Tiers:
      0-2:   None
      3-4:   Flow State (1.5x) - Cyan
      5-6:   Overclocked (2x) - Green
      7-9:   Surge (3x) - Yellow
      10-11: Unstoppable (5x) - Red
      12+:   God Mode (8x) - Magenta
    """
    if combo >= 12:
        return "GOD MODE", 8.0, Fore.MAGENTA + Style.BRIGHT
    elif combo >= 10:
        return "UNSTOPPABLE", 5.0, Fore.RED + Style.BRIGHT
    elif combo >= 7:
        return "SURGE", 3.0, Fore.YELLOW + Style.BRIGHT
    elif combo >= 5:
        return "OVERCLOCKED", 2.0, Fore.GREEN + Style.BRIGHT
    elif combo >= 3:
        return "FLOW STATE", 1.5, Fore.CYAN + Style.BRIGHT
    else:
        return "", 1.0, ""

# --- Input & screen drawing ---

def flush_input():
    """Discards keys typed ahead (e.g. during the countdown) so they don't become the next answer."""
    if not sys.stdin.isatty():
        return
    if termios:
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    else:
        while msvcrt.kbhit():
            msvcrt.getwch()

def read_key(timeout=None):
    """One keypress without waiting for Enter. Esc is '\\x1b'; '' = ignored key (arrows etc.); None = timed out."""
    if msvcrt:
        end = None if timeout is None else time.time() + timeout
        while not msvcrt.kbhit():
            if end is not None and time.time() >= end:
                return None
            time.sleep(0.01)
        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):  # arrow/function key: swallow its second code
            msvcrt.getwch()
            return ""
        return ch
    fd = sys.stdin.fileno()
    if not select.select([fd], [], [], timeout)[0]:
        return None
    b = os.read(fd, 1)
    if not b:
        raise EOFError
    if b == b"\x1b":
        if not select.select([fd], [], [], 0.02)[0]:
            return "\x1b"  # nothing followed: a bare Esc press
        while select.select([fd], [], [], 0.02)[0]:  # escape sequence (arrows etc.): swallow it
            os.read(fd, 8)
        return ""
    extra = 0 if b[0] < 0xC0 else 1 if b[0] < 0xE0 else 2 if b[0] < 0xF0 else 3  # UTF-8 continuation bytes
    return (b + os.read(fd, extra) if extra else b).decode("utf-8", "ignore")

@contextlib.contextmanager
def cbreak_mode():
    """Unbuffered, no-echo stdin for the duration of the block (Ctrl-C still works). No-op on Windows."""
    if termios is None:
        yield
        return
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def clear_screen():
    """Clears the terminal screen."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def center(s, cols):
    return " " * max(0, (cols - get_visible_length(s)) // 2) + s

def build_frame(lines, prompt=None, typed="", reserve=0):
    """One full screen as a string: `lines` centered in the terminal, plus an optional prompt line below.
    `reserve` is the width the typed text may grow to; it is left free so the prompt doesn't shift."""
    cols, rows = shutil.get_terminal_size()
    out = [center(l, cols) for l in lines]
    if prompt is not None:
        pad = " " * max(0, (cols - get_visible_length(prompt) - reserve) // 2)
        out += ["", pad + prompt + typed]
    out = [""] * max(0, (rows - len(out)) // 2) + out
    if cols < MIN_COLS or rows < MIN_ROWS:
        out.insert(0, f"{Fore.RED}Terminal is {cols}x{rows}: resize to at least {MIN_COLS}x{MIN_ROWS}{Style.RESET_ALL}")
    # Home the cursor and overwrite in place (no clear => no flicker); \033[K / \033[J wipe leftovers.
    return "\033[H" + "\n".join(l + Style.RESET_ALL + "\033[K" for l in out[-rows:]) + "\033[J"

def screen(lines, prompt="", target=None, done=None, deadline=None):
    """
    Draws `lines` centered with a prompt below and reads the answer key by key.
    Redraws ~10x/s only when something changed (typing, live timer, terminal resize).

    lines     list of lines, or callable(seconds_left) -> list (for a live timer)
    target    if given, typed chars are colored GOOD/BAD against it and stale keys are not flushed
    done      callable(buf) -> True to finish early (single-key menus, auto-submit)
    deadline  time.time() value at which to give up
    Returns (text, status); status is 'enter', 'auto' (done fired), 'esc' or 'timeout'.
    """
    lines_fn = lines if callable(lines) else (lambda remaining: lines)
    reserve = len(target) + 10 if target else 12  # also the max chars accepted; keeps the line from wrapping

    if not sys.stdin.isatty():  # piped input: no raw keys, no live timer
        clear_screen()
        sys.stdout.write(build_frame(lines_fn(None), prompt, "", reserve))
        sys.stdout.flush()
        return input(""), "enter"

    if target is None:
        flush_input()
    clear_screen()
    buf, last = "", None
    with cbreak_mode():
        while True:
            remaining = None if deadline is None else deadline - time.time()
            if remaining is not None and remaining <= 0:
                return buf, "timeout"

            if target is None:
                typed = buf
            else:
                typed = "".join(
                    (GOOD if fold(c) == fold(target[i:i + 1]) else BAD) + c for i, c in enumerate(buf))
            frame = build_frame(lines_fn(remaining), prompt, typed, reserve)
            if frame != last:
                sys.stdout.write(frame)
                sys.stdout.flush()
                last = frame

            ch = read_key(0.1)
            if ch is None:
                continue
            if ch in ("\r", "\n"):
                return buf, "enter"
            if ch == "\x1b":
                return buf, "esc"
            if ch == "\x03":  # Ctrl-C (only arrives raw on Windows)
                raise KeyboardInterrupt
            if ch == "\x04":
                raise EOFError
            if ch in ("\x7f", "\x08"):
                buf = buf[:-1]
            elif ch and ch.isprintable() and len(buf) < reserve:
                buf += ch
                if done and done(buf):
                    return buf, "auto"

def draw_centered(lines):
    """Clears the screen and draws `lines` centered (no input)."""
    clear_screen()
    sys.stdout.write(build_frame(lines))
    sys.stdout.flush()

def wait_key(lines, prompt=f"{Fore.YELLOW}Press any key to continue...{Style.RESET_ALL}"):
    """Shows `lines` until a key is pressed. Returns the key ('' for Enter/Esc)."""
    return screen(lines, prompt, done=lambda b: True)[0]

def choose(lines, prompt, n):
    """Menu pick from 1..n: a digit selects at once unless it could start a longer number (then Enter).
    Esc picks the last item (Back / Quit)."""
    text, status = screen(lines, prompt, done=lambda b: not b.isdecimal() or int(b) * 10 > n)
    return str(n) if status == "esc" else text

def splash_screen():
    """Displays a cool ASCII art logo on startup."""
    top = [
        r"  _   _  __   __  ____   _____   ____  ",
        r" | | | | \ \ / / |  _ \ | ____| |  _ \ ",
        r" | |_| |  \ V /  | |_) ||  _|   | |_) |",
        r" |  _  |   | |   |  __/ | |___  |  _ < ",
        " |_| |_|   |_|   |_|    |_____| |_| \\_\\",
    ]
    bottom = [
        r"   _____  __   __  ____   _____   ____  ",
        r"  |_   _| \ \ / / |  _ \ | ____| |  _ \ ",
        r"    | |    \ V /  | |_) ||  _|   | |_) |",
        r"    | |     | |   |  __/ | |___  |  _ < ",
        "   |_|     |_|   |_|    |_____| |_| \\_\\",
    ]
    logo = ([Fore.MAGENTA + Style.BRIGHT + l for l in top] + [""]
            + [Fore.CYAN + Style.BRIGHT + l for l in bottom])

    play_sound("splash")
    wait_key(logo, f"{Fore.YELLOW}Press any key to start...{Style.RESET_ALL}")

def countdown():
    """Runs a 3-2-1-GO countdown."""
    play_sound("countdown")
    for i in [3, 2, 1]:
        draw_centered([f"{Fore.CYAN}{Style.BRIGHT}{i}"])
        time.sleep(1)

    draw_centered([f"{Fore.GREEN}{Style.BRIGHT}GO!"])
    time.sleep(0.5)
    flush_input()  # drop keys typed during the countdown

# --- Persistence: high scores, history ---

def load_high_scores():
    """Loads high scores, migrating old format {'Mode': 100} to {'Mode': {'score': 100, 'name': 'CPU'}}."""
    defaults = {"Streak": {"score": 0, "name": "---"}}

    if not os.path.exists(HIGHSCORE_FILE):
        return defaults

    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return defaults

            # Check for migration needs
            migrated = False
            new_data = {}

            for k, v in data.items():
                if isinstance(v, int):
                    # Old format detected
                    new_data[k] = {"score": v, "name": "CPU"}
                    migrated = True
                elif isinstance(v, dict) and "score" in v:
                    # New format (basic check)
                    new_data[k] = v
                else:
                    new_data[k] = {"score": 0, "name": "---"}

            if migrated:
                print(f"{Fore.YELLOW}Migrated high scores to new format...{Style.RESET_ALL}")
                save_high_scores(new_data)
                return new_data

            return data
    except (json.JSONDecodeError, IOError):
        return defaults

def save_high_scores(scores):
    """Saves the high score dict to JSON."""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=4)
    except IOError:
        print("\nWarning: Could not save high scores.")

def load_history():
    """Returns the list of finished runs from history.jsonl (bad lines skipped)."""
    runs = []
    try:
        with open(HISTORY_FILE) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    runs.append(r)
    except OSError:
        pass
    return runs

def append_history(run):
    try:
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(run) + "\n")
    except OSError:
        pass

def earned(run, achievement):
    """Practice runs don't unlock achievements."""
    return not run.get("practice") and achievement[2](run)

def sparkline(values):
    lo, hi = min(values), max(values)
    return "".join("▁▂▃▄▅▆▇█"[int((v - lo) / ((hi - lo) or 1) * 7)] for v in values)

def show_high_scores():
    """Displays high scores in a formatted Hall of Fame table."""
    scores = load_high_scores()

    lines = [
        f"{Fore.CYAN}{Style.BRIGHT}=== HALL OF FAME ==={Style.RESET_ALL}",
        ""
    ]

    # Table Header
    # MODE (24) | SCORE (8) | HELD BY
    header = f"{Fore.WHITE}{Style.BRIGHT}{'MODE':<24} {'SCORE':<8} {'HELD BY'}{Style.RESET_ALL}"
    lines.append(header)
    lines.append("-" * 45)

    if not scores:
        lines.append("No scores recorded yet.")
    else:
        for mode in sorted(scores.keys()):
            entry = scores[mode]
            s_val = entry.get('score', 0)
            s_name = entry.get('name', '---')
            lines.append(f"{Fore.CYAN}{mode:<24}{Style.RESET_ALL} {Fore.YELLOW}{s_val:<8}{Style.RESET_ALL} {Fore.MAGENTA}{s_name}{Style.RESET_ALL}")

    lines.append("")
    lines.append("-" * 45)

    wait_key(lines)

def show_stats():
    """Averages and a WPM trend over all finished runs, plus the achievement list."""
    runs = load_history()
    lines = [f"{Fore.CYAN}{Style.BRIGHT}=== STATS ==={Style.RESET_ALL}", ""]
    if runs:
        wpms = [r.get("wpm", 0) for r in runs]
        accs = [r.get("accuracy", 0) for r in runs]
        lines += [
            f"Runs: {len(runs)}",
            f"Avg WPM: {Fore.CYAN}{sum(wpms) / len(runs):.1f}{Style.RESET_ALL}   Best WPM: {Fore.CYAN}{max(wpms):.1f}{Style.RESET_ALL}",
            f"Avg accuracy: {sum(accs) / len(runs):.0f}%",
            f"WPM trend (last {min(30, len(runs))}): {Fore.GREEN}{sparkline(wpms[-30:])}{Style.RESET_ALL}",
        ]
    else:
        lines.append("No runs recorded yet.")
    lines += ["", f"{Fore.WHITE}{Style.BRIGHT}ACHIEVEMENTS{Style.RESET_ALL}"]
    for a in ACHIEVEMENTS:
        got = any(earned(r, a) for r in runs)
        lines.append(f"{Fore.YELLOW + '★' if got else Fore.WHITE + '·'}{Style.RESET_ALL} {a[0]} - {a[1]}")
    wait_key(lines)

# --- Game Modes ---

def game_lines(mode_name, score, combo, remaining, msg, word):
    """The in-game HUD: title, score/timer/combo bar, last-word feedback and the word to type."""
    tier_name, multiplier, color_code = get_combo_tier(combo)
    combo_text = f" {color_code}{tier_name} ({multiplier:g}x){Style.RESET_ALL}" if tier_name else ""
    timer = f"{remaining:.1f}s" if SETTINGS["show_timer"] else "--"
    return [
        f"{Fore.CYAN}--- {mode_name.upper()} MODE ---{Style.RESET_ALL}",
        f"SCORE: {Fore.YELLOW}{score}{Style.RESET_ALL}  |  TIME: {Fore.YELLOW}{timer}{Style.RESET_ALL}  |  COMBO: {GOOD}{combo}{Style.RESET_ALL}{combo_text}",
        "-" * 60,
        msg,
        f"Word:  {Style.BRIGHT}{Fore.WHITE}{word}{Style.RESET_ALL}",
        "",
    ]

def pause_screen():
    """Returns True to resume the game, False to quit to the menu."""
    lines = [f"{Fore.CYAN}{Style.BRIGHT}=== PAUSED ==={Style.RESET_ALL}", "The timer is stopped."]
    return wait_key(lines, "Enter = resume, Q = quit to menu: ").lower() != "q"

def streak_mode(mode_name, path, exact_match=False):
    """Runs a timed streak game (with retry). Esc pauses; a wrong word ends the run unless Practice is on."""
    words = pick_words(load_words(path, exact_match), exact_match)
    time_limit = float(SETTINGS["time_limit"])
    practice = SETTINGS["practice"]
    key = score_key(mode_name, exact_match)

    while True:
        countdown()

        score = good_chars = raw_chars = correct_words = combo = best_combo = 0
        longest = ""
        msg = ""  # feedback for the previous word, shown in the HUD
        wrong_msg = None
        bag = word_bag(words)
        start = time.time()
        deadline = start + time_limit
        status = "timeout"

        while True:
            target_word = next(bag)
            _, multiplier, _ = get_combo_tier(combo)
            # In word modes the last correct char (or Space) submits; exact modes need Enter.
            auto = None if exact_match else (lambda b: same(b, target_word) or b.endswith(" "))

            while True:  # same word again after a pause or an empty Enter
                try:
                    typed, status = screen(
                        lambda r: game_lines(mode_name, score, combo, r, msg, target_word),
                        "Type it: ", target=target_word, done=auto, deadline=deadline)
                except (EOFError, KeyboardInterrupt):
                    return
                if status == "esc":
                    t0 = time.time()
                    if not pause_screen():
                        return
                    paused = time.time() - t0
                    start += paused
                    deadline += paused
                elif status == "timeout" or typed.strip():
                    break

            if status == "timeout":  # the word in progress is dropped; the live timer made that visible
                play_sound("victory")
                break

            typed = typed.strip()
            raw_chars += len(typed)

            if same(typed, target_word):
                combo += 1
                best_combo = max(best_combo, combo)
                points = int(len(target_word) * multiplier)
                score += points
                good_chars += len(target_word)
                correct_words += 1
                if len(target_word) > len(longest):
                    longest = target_word

                play_sound("correct")
                if combo in (3, 5, 7, 10, 12):  # combo tier thresholds
                    play_sound("levelup")
                msg = f"{GOOD}✓ {target_word} +{points}{Style.RESET_ALL}"
            else:
                combo = 0
                msg = f"{BAD}✗ You typed '{typed}', expected '{target_word}'{Style.RESET_ALL}"
                if not practice:
                    play_sound("gameover")
                    wrong_msg = msg
                    status = "wrong"
                    break

        # --- GAME OVER SCREEN ---
        elapsed = time_limit if status == "timeout" else time.time() - start
        net_wpm = wpm(good_chars, elapsed)  # correct words only; raw counts every submitted char
        raw_wpm = wpm(raw_chars, elapsed)
        accuracy = 100.0 * good_chars / raw_chars if raw_chars else 100.0

        time.sleep(0.5)  # keys from the word you were mid-typing are flushed by the next screen

        run = {
            "date": time.strftime("%Y-%m-%d %H:%M"), "mode": mode_name, "time": int(time_limit),
            "wpm": round(net_wpm, 1), "accuracy": round(accuracy, 1), "score": score,
            "words": correct_words, "best_combo": best_combo, "practice": practice,
        }
        history = load_history()
        unlocked = [a for a in ACHIEVEMENTS if earned(run, a) and not any(earned(r, a) for r in history)]
        append_history(run)

        scores = load_high_scores()
        best = scores.get(key, {"score": 0, "name": "---"})
        is_new_record = score > best.get("score", 0)

        lines = ["", f"{Fore.RED}{Style.BRIGHT}GAME OVER{Style.RESET_ALL}"]
        if wrong_msg:
            lines.append(wrong_msg)
        if is_new_record:
            play_sound("levelup")
            lines.append(f"{Fore.GREEN}🚨 NEW HIGH SCORE! 🚨{Style.RESET_ALL}")
        lines += [
            f"Final Score: {Fore.YELLOW}{score}{Style.RESET_ALL} ({score - best.get('score', 0):+d} vs best)",
            "-" * 30,
            f"Total Words Typed: {correct_words}",
            f"WPM: {Fore.CYAN}{net_wpm:.1f}{Style.RESET_ALL} (raw {raw_wpm:.1f})",
            f"Accuracy: {accuracy:.0f}%",
            f"Best Combo: {best_combo}",
            f"Longest Word: {longest or '-'}",
            "-" * 30,
        ]
        lines += [f"{Fore.YELLOW}★ Achievement unlocked: {a[0]} - {a[1]}{Style.RESET_ALL}" for a in unlocked]

        if is_new_record:
            name = screen(lines, "Enter initials (3 chars): ")[0].strip().upper()[:3] or "UNK"
            scores[key] = {"score": score, "name": name}
            save_high_scores(scores)
            lines.append(f"{Fore.GREEN}Score Saved! {name} - {score}{Style.RESET_ALL}")
        else:
            lines.append(f"{Fore.CYAN}High Score: {best.get('score', 0)} ({best.get('name', '---')}){Style.RESET_ALL}")

        lines += ["", f"[{Fore.CYAN}Press ENTER for Menu{Style.RESET_ALL}] or [{Fore.CYAN}Press 'R' to Retry{Style.RESET_ALL}]"]
        if wait_key(lines, "").lower() != "r":
            break

def play_menu():
    """Submenu for selecting a game mode, showing your best score for the current timer settings."""
    while True:
        modes = get_modes()
        scores = load_high_scores()
        n = len(modes) + 1  # last item is Back
        tags = [f"{SETTINGS['time_limit']}s"]
        if SETTINGS["difficulty"] != "all":
            tags.append(SETTINGS["difficulty"])
        if SETTINGS["practice"]:
            tags.append("practice")
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}--- SELECT MODE ---{Style.RESET_ALL}",
            f"{Fore.YELLOW}Timer: {' | '.join(tags)}{Style.RESET_ALL}",
            f"{Fore.WHITE}{Style.BRIGHT}    {'MODE':<20} {'BEST':>5}{Style.RESET_ALL}",
        ]
        for i, (name, _, exact) in enumerate(modes, 1):
            best = scores.get(score_key(name, exact), {}).get("score", 0)
            lines.append(f"{Fore.CYAN}{i:>2}. {name[:20]:<20}{Style.RESET_ALL} {Fore.YELLOW}{best:>5}{Style.RESET_ALL}")
        lines.append(f"{Fore.CYAN}{n:>2}. {'Back to Main Menu':<20}{Style.RESET_ALL}      ")

        try:
            choice = choose(lines, f"Select an option (1-{n}): ", n).strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == str(n):
            break
        if choice.isdecimal() and 1 <= int(choice) < n:
            streak_mode(*modes[int(choice) - 1])

def settings_menu():
    """Menu for changing game settings."""
    toggles = {'1': ("sound", True), '4': ("show_timer", True), '5': ("practice", False), '7': ("colorblind", False)}

    def flag(on, yes="ON", no="OFF"):
        return f"[{Fore.GREEN if on else Fore.RED}{yes if on else no}{Style.RESET_ALL}]"

    while True:
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}=== SETTINGS ==={Style.RESET_ALL}",
            f"1. Sound: {flag(SETTINGS['sound'])}",
            f"2. Volume: [{Fore.YELLOW}{SETTINGS['volume']}%{Style.RESET_ALL}]",
            f"3. Timer Length: [{Fore.YELLOW}{SETTINGS['time_limit']}s{Style.RESET_ALL}]",
            f"4. Timer Display: {flag(SETTINGS['show_timer'], 'SHOW', 'HIDE')}",
            f"5. Practice Mode (mistakes only reset combo): {flag(SETTINGS['practice'])}",
            f"6. Word Length: [{Fore.YELLOW}{SETTINGS['difficulty'].upper()}{Style.RESET_ALL}]",
            f"7. Colorblind Palette: {flag(SETTINGS['colorblind'])}",
            f"8. {Fore.RED}Reset All High Scores{Style.RESET_ALL}",
            "9. Back to Main Menu",
        ]

        try:
            choice = choose(lines, "Select an option (1-9): ", 9).strip()

            if choice in toggles:
                key, default = toggles[choice]
                SETTINGS[key] = not SETTINGS.get(key, default)
                apply_theme()  # both are no-ops unless colorblind / sound just changed
                init_audio()
                save_settings(SETTINGS)

            elif choice == '2':
                SETTINGS["volume"] = (SETTINGS["volume"] - 25) % 125  # 100 -> 75 -> 50 -> 25 -> 0 -> 100
                apply_volume()
                save_settings(SETTINGS)
                play_sound("correct")

            elif choice == '3':
                raw, _ = screen([f"Current: {SETTINGS['time_limit']}s"], "Seconds (5-600, Enter = next preset): ")
                raw = raw.strip()
                if raw.isdecimal() and 5 <= int(raw) <= 600:
                    SETTINGS["time_limit"] = int(raw)
                elif not raw:
                    options = [15, 30, 60, 120]
                    SETTINGS["time_limit"] = next((o for o in options if o > SETTINGS["time_limit"]), options[0])
                save_settings(SETTINGS)

            elif choice == '6':
                levels = list(LENGTHS)
                i = levels.index(SETTINGS["difficulty"]) if SETTINGS["difficulty"] in levels else -1
                SETTINGS["difficulty"] = levels[(i + 1) % len(levels)]
                save_settings(SETTINGS)

            elif choice == '8':
                warning_lines = [
                    f"{Fore.RED}{Style.BRIGHT}ARE YOU SURE? THIS CANNOT BE UNDONE.{Style.RESET_ALL}",
                    "Type 'Y' or 'y' to confirm, anything else to cancel."
                ]
                confirm, _ = screen(warning_lines, "Confirm Reset: ")
                if confirm.strip().lower() == 'y':
                    save_high_scores({})
                    wait_key([f"{Fore.GREEN}Scores Reset!{Style.RESET_ALL}"])

            elif choice == '9':
                break
        except (EOFError, KeyboardInterrupt):
            break

# --- Main Menu ---

def main_menu():
    """Runs the main menu loop."""
    while True:
        lines = [
            f"{Fore.CYAN}{Style.BRIGHT}=== HYPERTYPER ==={Style.RESET_ALL}",
            f"{Fore.CYAN}1. Play Game{Style.RESET_ALL}",
            f"{Fore.CYAN}2. High Scores{Style.RESET_ALL}",
            f"{Fore.CYAN}3. Stats{Style.RESET_ALL}",
            f"{Fore.CYAN}4. Settings{Style.RESET_ALL}",
            f"{Fore.CYAN}5. Quit{Style.RESET_ALL}"
        ]

        try:
            choice = choose(lines, "Select an option (1-5): ", 5).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == '1':
            play_menu()
        elif choice == '2':
            show_high_scores()
        elif choice == '3':
            show_stats()
        elif choice == '4':
            settings_menu()
        elif choice == '5':
            print("\nThanks for playing! Goodbye.")
            break

if __name__ == "__main__":
    # Ensure highscore file exists
    if not os.path.exists(HIGHSCORE_FILE):
        save_high_scores({})

    load_settings()
    apply_theme()
    init_audio()
    try:
        splash_screen()
        main_menu()
    except (KeyboardInterrupt, EOFError):  # Ctrl-C / Ctrl-D at any prompt
        print("\n\nGame Interrupted. Bye!")
        sys.exit(0)
