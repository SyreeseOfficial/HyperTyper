# HyperTyper

![HyperTyper Demo](hypertyper.gif)

A high-octane CLI typing game built with Python. Test your speed, build your streaks, and dominate the leaderboard!

## Features

- **Multiple Game Modes:** Streak, Cities, Food, Code Snippets, Quotes, and more!
- **Live Gameplay:** Ticking timer, per-letter right/wrong coloring, auto-submit in word modes, Esc to pause.
- **Combo System:** Build up your combo to earn multipliers and reach "God Mode".
- **Sound Effects:** Audio feedback for milestones (optional, requires `pygame`).
- **High Scores:** Local best score per mode, timer length and word length.
- **Stats & Achievements:** Every run is logged; see averages, a WPM trend and unlocked achievements.
- **Customizable:** Sound volume, custom timer length, word length, practice mode (mistakes only reset your combo), colorblind palette.
- **Your Own Word Lists:** Drop any `.txt` file (one entry per line) into `~/.config/hypertyper/words/` and it shows up as a mode.

## Installation

### Prerequisites

- Python 3.8+
- `pygame` (optional, for sound)

### Option 1: Arch Linux (AUR) - Recommended

If you are on Arch Linux, you can install HyperTyper directly from the AUR:

```bash
yay -S hypertyper
```

### Option 2: Using pip (Other Systems)

1.  Clone the repository:
    ```bash
    git clone https://github.com/SyreeseOfficial/HyperTyper.git
    cd HyperTyper
    ```
2.  (Optional) Install `pygame` for sound:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the game, run:

```bash
python3 hypertyper.py
```

Navigate the menus using the number keys (Esc goes back) and type the words as they appear on the screen!
Word modes submit on the last correct letter or Space; code, quote and custom modes need Enter.

## Files

Settings, high scores, run history and custom word lists live in `~/.config/hypertyper/`
(`$XDG_CONFIG_HOME/hypertyper/`): `settings.json`, `highscores.json`, `history.jsonl`, `words/`.

## Scoring

WPM = correct characters / 5 / minutes elapsed (net). "raw" counts every character you submitted, right or wrong.

## Tests

```bash
python3 test_hypertyper.py
```

## License

MIT, see [LICENSE](LICENSE).

## Roadmap

- [ ] More game modes
- [ ] More settings
- [ ] More color themes
- [ ] Local multiplayer
