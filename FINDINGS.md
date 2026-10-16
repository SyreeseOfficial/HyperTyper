# HyperTyper: Findings

Reviewed 2026-10-08. Single file `hypertyper.py` (774 lines) + `data/*.txt`. Tags: **[H]** high value, **[M]** medium, **[L]** low. `[ ]` = open, `[x]` = done.

## Skip
- [ ] **[L]** Local multiplayer / hot-seat (on roadmap). Easiest form: two players alternate runs with the same seed, compare scores.
- [ ] **[L]** Daily challenge: seed `random` with the date so everyone gets the same words; separate daily record.
- [ ] **[M]** CLI flags with `argparse`: `--mode food --time 60 --no-sound --version`. Lets the AUR package launch straight into a mode.
- [ ] **[H]** Top-10 leaderboard per mode with date and WPM (README promises "leaderboard" but only 1 entry per mode exists).

## Completed
- [x] **[H]** Type-ahead breaks the game: keys pressed during the countdown or the 0.2 s "OK!" flash stay in stdin and become the next `input()`, so the next word is "wrong" and the run ends instantly (`hypertyper.py:308`, `:505`). Fix: `termios.tcflush(sys.stdin, termios.TCIFLUSH)` right before each prompt (guard for Windows). (already fixed in `af9d406`)
- [x] **[H]** Wrong-word message is never seen: it prints at `:517`, then `break` goes straight to the Game Over screen, which calls `clear_screen()`. Show it inside the Game Over lines ("You typed X, expected Y"). (already fixed in `af9d406`)
- [x] **[H]** High scores ignore the timer length: 15 s and 120 s runs share one record per mode (`:543`). Key by `f"{mode}@{time_limit}s"`, or store a per-time table. (already fixed in `af9d406`)
- [x] **[M]** Ctrl-D (EOF) is only caught on the word prompt (`:473`). On the initials prompt, menus after game over, splash, or pause it dumps a traceback, and `__main__` only catches `KeyboardInterrupt` (`:772`). Catch `EOFError` at top level too. (already fixed in `af9d406`)
- [x] **[M]** First run prints "Migrated high scores to new format..." for no reason: `__main__` writes the old format `{"Streak": 0}` (`:761`) and the loader migrates it. Write `{}` or the new format. (already fixed in `af9d406`)
- [x] **[M]** Timer is not live: `~Ns` is drawn once per word (`:458`), so it freezes while you type. A long word at 1 s left is still accepted or silently thrown away (`:477`). Pick a rule: reject late input with a message, or draw a live timer (see Features).
- [x] **[M]** Random word repeats back-to-back (`random.choice`, `:453`), and duplicates in the lists weight some words higher. Use a shuffled bag, then dedupe the data files.
- [x] **[M]** Spanish mode needs exact characters: accent-insensitive compare (`unicodedata` NFD, strip combining) or at least accept un-accented input. (Only 1 non-ASCII line today, so low risk, but any future list will hit this.)
- [x] **[L]** Emoji in "🚨 NEW HIGH SCORE" is 2 columns wide but counted as 1, so that line sits 1 col off-center (`get_visible_length`, `:205`). Use `wcwidth` or drop the emoji. (already fixed in `af9d406`)
- [x] **[L]** Initials loop is a `while True` that always breaks on the first pass, with two copy-pasted save blocks (`:554-574`). Collapse to `name = (input or "UNK")[:3]`; save once.
- [x] **[L]** WPM uses full elapsed time including the pause after a wrong word and counts only correct chars, so it is not comparable with other tools (`:521-527`). Document the formula or show raw + net WPM. (already fixed in `af9d406`)
- [x] **[L]** `PKGBUILD` says `pkgver=1.0.1` but tag `v1.0.2` exists. Bump PKGBUILD and `.SRCINFO` together, and replace `sha256sums=('SKIP')` with a real sum before AUR push. (already fixed in `af9d406`)
- [x] **[L]** PKGBUILD maintainer is a placeholder `syreese@example.com`. Fix before publishing. (already fixed in `af9d406`)
- [x] **[M]** `clear_screen()` shells out via `os.system('clear')` every word (`:276`). Print `"\033[2J\033[H"` (colorama already handles Windows); removes a process spawn per word and the flicker.
- [x] **[M]** `pygame` import is slow and prints its "Hello from the pygame community" banner. Set `os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1"` before import; use `pygame.mixer.init()` only. Lazy-import when sound is on.
- [x] **[L]** `load_words` re-reads and re-filters the file on every mode entry and each retry-loop is fine, but cache per file in a dict.
- [x] **[L]** `load_high_scores()` re-reads the JSON file multiple times per game over (`:543`, `:561`, `:570`). Load once, reuse.
- [x] **[L]** `get_visible_length` recompiles the ANSI regex on each call (`:207`). Compile once at module level.
- [x] **[L]** Remove the forced `time.sleep(1)` when pygame is missing (`:21`) and `time.sleep(2)` when a word file is missing (`:125`). Print once, never block startup.
- [x] **[H]** Live countdown timer that ticks every 100 ms while typing (needs the raw-mode loop above).
- [x] **[M]** Auto-submit on correct final character (or Space) in non-exact modes, so Enter is not needed per word. Keep Enter for exact-match modes (code/terminal).
- [x] **[M]** Remove the fixed 0.2 s sleep after every correct word (`:505`). It eats time budget and slows pace. A brief inline "+N" flash on the same screen is enough.
- [x] **[M]** Main menu title says "CLI TYPING GAME" (`:732`); use the HyperTyper logo/name. Show current time limit and best score on the mode picker.
- [x] **[M]** Mode list is a 13-line `if/elif` chain duplicated in the menu text (`:601-650`). Drive both from one `MODES = [(name, file, exact)]` list so menu number, label, and launch never drift apart.
- [x] **[M]** Game Over: show accuracy, best combo, longest word, and compare to personal best ("+12 vs best"). Data is already tracked or trivial to add.
- [x] **[L]** Menu choices need Enter; allow single keypress selection once raw input exists.
- [x] **[L]** Re-center on terminal resize and warn when the terminal is smaller than 60x15.
- [x] **[L]** Settings: allow custom timer value and sound volume (`Sound.set_volume`), not only the 15/30/60/120 cycle (`:685`).
- [x] **[L]** Colorblind-safe palette option (replace red/green-only signals with symbols too). Matches "Color themes" on the roadmap.
- [x] **[L]** Pause/quit key in game (Esc) instead of Ctrl-C only.
- [x] **[M]** User word lists: any `~/.config/hypertyper/words/*.txt` shows up as a mode automatically (name from file name). Pair with the MODES table above.
- [x] **[M]** "Practice" / forgiving mode: mistakes cost a combo reset instead of ending the run. Current sudden death is harsh for new players, especially in code mode.
- [x] **[M]** Stats history (`history.jsonl`): date, mode, time, WPM, accuracy, score; add a Stats screen with averages and a trend sparkline.
- [x] **[M]** Quotes/sentences mode (full lines, punctuation) for real-world typing practice.
- [x] **[L]** Difficulty filter by word length (short/medium/long) for the word-based modes.
- [x] **[L]** Achievements (first God Mode, 50 WPM, 100 words in one run).
- [x] **[M]** Delete `organize_sound_files()` (`:131-152`) and its call (`:767`). One-time dev migration that runs a relative `sounds` check every launch; sounds already live in `data/sounds`.
- [x] **[M]** Dedupe word lists: linkedin 327, spanish 394, words 314, lorem 151, terminal 48, animals 34 duplicate lines. `sort -u` them (keep file order if it matters, use `awk '!s[$0]++'`).
- [x] **[L]** Dead code: `pause()` (`:315`), `WORD_FILE` (`:52`), unused `Back` import (`:9`), commented-out sleep (`:189`), stale "Optional" migration comment (`:49`), long monologue comment in `pause()`.
- [x] **[L]** `data/settings.json` is a leftover; settings live in `~/.config/hypertyper/`. Remove from the repo if tracked (`git ls-files data/settings.json`).
- [x] **[L]** Docstrings still say "data/settings.json" (`:65`, `:87`). Update to `SETTINGS_FILE`.
- [x] **[L]** README: `pygame` is listed as required in `requirements.txt` but the game works without it; mark optional. Add LICENSE file (PKGBUILD says MIT, repo has none). Document the config path and that high scores are in `~/.config/hypertyper/`.
- [x] **[L]** No tests. One `test_hypertyper.py` for `get_combo_tier`, `load_words` filtering, and WPM math is enough.
- [x] **[L]** Consider dropping `colorama` on Linux/macOS (raw ANSI works) to cut a dependency; keep only if Windows support matters. Done: colors are plain ANSI codes now. `PKGBUILD`/`.SRCINFO` still list `python-colorama` and require `python-pygame`; make pygame an `optdepends` and drop colorama when you cut the next release (the v1.0.2 tarball still needs them).

---

## Round 2 (reviewed 2026-10-13, against `hypertyper.py` at 891 lines)

Still open from the first list: hot-seat multiplayer, daily seeded challenge, `argparse` flags, top-10 leaderboard per mode. Everything below is new.

### Bugs (verified in code or data)
- [ ] **[H]** WPM is inflated by very short runs. `wpm()` clamps elapsed to 1 s (`:263`) and sudden death ends the run at the first typo, so typing two 6-letter words in 1.5 s then missing the third records ~96 WPM. That feeds "Best WPM", the trend sparkline and the **Speed Demon (50 WPM)** achievement (`:95`). Require a minimum run length (e.g. >= 10 s or >= 10 words) before a run counts toward WPM stats and WPM achievements, or mark short runs `"short": true` in `history.jsonl` and skip them.
- [ ] **[H]** Accuracy ignores corrected mistakes. `accuracy = good_chars / raw_chars` (`:700`) only counts characters in submitted words, so typing a wrong letter and hitting Backspace costs nothing. Count every keystroke and every wrong keystroke inside `screen()` (return them with the buffer) and report `accuracy` plus "corrected errors". This is also the prerequisite for the weak-keys drill below.
- [ ] **[H]** Hall of Fame breaks as scores accumulate. Keys are `mode@30s long practice` (`score_key`, `:206`), so 13 modes x 4 timers x 4 lengths x practice can produce hundreds of rows. `build_frame` keeps `out[-rows:]` (`:365`), so a long table loses its **top**, i.e. the title and header. Show one mode per page with Left/Right, or show only the best row per mode with a "filter: 30s / all" toggle.
- [ ] **[M]** Hall of Fame columns misalign: the mode column is `<24` wide (`:575`) but keys like `Terminal Commands@30s practice` are 30 characters, and the `-` rule is 45 wide. Truncate or widen, and show friendly labels (`Terminal Commands · 30s · practice`) instead of the raw key.
- [ ] **[M]** `MIN_ROWS = 15` (`:99`) is too small for the mode picker: 3 header lines + 13 modes + Back + prompt is 19+ lines (more with custom lists). A 15-18 row terminal passes the size check and silently loses the top of the menu. Compute the required rows from the actual `lines` passed to `build_frame`, or paginate long menus.
- [ ] **[M]** Word modes silently drop entries. `load_words` keeps only `len >= 3 and isalpha()` (`:171`), which removes 21 of 276 animals (`Polar Bear`, `Sea Lion`, `Ox`), 6 foods (`Ice Cream`, `Halo-Halo`), 17 lorem words, 26 Spanish words and `mr. mime`. Either allow spaces/hyphens (and fix the space-submits rule, see below) or clean those entries out of the data files so the lists are honest.
- [ ] **[M]** Space submits in word modes (`b.endswith(" ")`, `:647`). That makes any multi-word entry untypeable and means one stray Space mid-word ends the run in sudden death. Only treat Space as submit when the buffer does not match the start of the target (`not target_word.startswith(b)`), or make it a setting.
- [ ] **[M]** Sound failures are invisible and Settings lies. When `pygame` is missing or there is no audio device, `init_audio()` prints "Audio disabled" (`:222`), which the splash screen's `clear_screen()` immediately erases; Settings still shows `Sound: [ON]`. It also retries the import on every settings toggle (`:806`). Remember the failure, show `Sound: [UNAVAILABLE]`, and don't retry.
- [ ] **[M]** `load_words` warning is lost the same way (`:178`): a custom list that is empty or has only blank lines silently plays the fruit `BACKUP_WORDS` under the custom list's name, and scores get recorded against it. Skip empty custom files when building the mode list (or show "empty list" in the menu).
- [ ] **[M]** High scores and settings can be wiped by a crash. `save_high_scores`/`save_settings` open the file with `'w'` (`:517`, `:139`), which truncates first; a kill mid-write loses everything. Worse, a corrupt `highscores.json` makes `load_high_scores` return defaults (`:512`) and the next save overwrites the corrupt file, so a recoverable file is destroyed. Write to `path + ".tmp"` then `os.replace`, and on a parse error move the bad file to `.bak` first.
- [ ] **[L]** `load_high_scores` builds a sanitized `new_data` but returns the raw `data` when nothing needed migrating (`:510`). A hand-edited entry like `"Streak": "abc"` then crashes `best.get(...)` at game over. Return `new_data` always.
- [ ] **[L]** Countdown runs in cooked mode: `countdown()` (`:464`) never enters `cbreak_mode`, so keys pressed during "3-2-1" are echoed onto the centered screen before `flush_input()` discards them. Wrap the countdown in `cbreak_mode()`, and let any key skip it (see UX).
- [ ] **[L]** Directory creation runs at import time (`os.makedirs(CONFIG_DIR)`, `:64`). With a read-only or missing `$HOME`, `import hypertyper` raises before any friendly handling, and tests must set `XDG_CONFIG_HOME` before importing. Create the directory lazily in `save_*`, inside the existing `IOError` handling.
- [ ] **[L]** Custom list named like a built-in mode (`Streak.txt`) produces the same `score_key` as the built-in and shares its high score (`get_modes`, `:200`). Prefix custom modes (`custom: name`) or dedupe names.
- [ ] **[L]** Stats mix incomparable runs. The trend, averages and "Best WPM" (`:587`) combine 15 s and 120 s runs, all modes, and practice runs, while achievements already exclude practice. Filter by practice flag by default and add a mode / timer filter.
- [ ] **[L]** "Reset All High Scores" (`:831`) leaves `history.jsonl` untouched, so Stats and achievements still show the old runs and the Settings label doesn't say so. Offer a second confirmation for "also clear history", or rename the item.

### UX / UI
- [ ] **[H]** Arrow-key / `j` `k` menu navigation with a highlighted row and Enter to select. `read_key` already swallows arrow sequences and returns `''` (`:325`), so they do nothing today. Digits stay as shortcuts, but with 14+ items the numbers need two keystrokes and mode 1 needs Enter because `10 <= 14` (`choose`, `:439`), which is inconsistent with modes 2-9.
- [ ] **[M]** Live WPM in the HUD (`game_lines`, `:605`). The data (`good_chars`, `start`) is already in scope; show `WPM: 47` next to score and timer, since this is a typing game that never shows speed while playing.
- [ ] **[M]** Use the terminal's alternate screen (`\033[?1049h` / `\033[?1049l`) and hide the cursor in menus. Currently every frame is drawn on the main screen, so quitting leaves the last frame in the user's scrollback with the shell prompt under it. Restore in the existing `finally`/exit paths.
- [ ] **[M]** Resume from pause should give a short "3-2-1" before the clock restarts. Today resume (`:660`) puts the user straight back on a new keystroke clock with the same word and their partial input erased.
- [ ] **[M]** Visual progress for the timer: a 20-char bar (`█████░░░░░`) beside `TIME: 12.3s` that changes color in the last 5 s. Easier to read at a glance than a number you have to parse mid-word.
- [ ] **[L]** Allow any key to skip the 3-2-1 countdown on retry (`countdown`, `:464`), or a setting for countdown length (0 / 1 / 3). Three seconds plus the 0.5 s "GO!" on every retry slows the R-to-retry loop.
- [ ] **[L]** Show the target word's progress cursor: dim the remaining letters of the target under the typed text so you can see where you are in long entries (Quotes, Code). Currently the target is shown above and the colored copy below, so the eye has to compare two lines.
- [ ] **[L]** Menus have no `q` shortcut and any non-digit key is returned as a choice that is then ignored (`choose`, `:439`). Map `q` to Quit/Back, and ignore unrelated keys instead of redrawing.
- [ ] **[L]** Ctrl-W / Ctrl-U in the typing buffer to delete a word / the line (`screen`, `:419`). Only Backspace works now; for long Quotes entries a mistake at the start costs a lot of keystrokes.

### Gameplay / features
- [ ] **[M]** Weak-keys drill: record per-character errors and keystroke latency in `history.jsonl` (needs the keystroke accounting above), then add a "Weak Keys" mode that generates words weighted toward your worst letters, plus a "slowest 10 keys" panel in Stats. This is the feature that makes typing trainers actually improve people.
- [ ] **[M]** Personal-best pace line: during a run, show `PB pace: +3 words` comparing `correct_words` at the current elapsed time against the best run for the same key (store the per-run word timestamps once, cheap). It is the single-player version of "ghost racing".
- [ ] **[M]** Per-mode Stats: best WPM, average accuracy and run count per mode, plus "runs today", "total time practiced" and a day streak. The data is already in `history.jsonl`; only the aggregation is missing.
- [ ] **[M]** Custom word lists are always exact-match (`get_modes`, `:202`), so a plain list of lowercase words still needs Enter after each. Let a first line `# words` (or a `name.words.txt` suffix) put the list in word mode with auto-submit and lowercasing.
- [ ] **[L]** Mid-run difficulty ramp option ("Endless"): the word length filter steps up every 10 correct words and the timer adds +1 s per word instead of a fixed clock. Gives a second, more forgiving play style without touching the existing scoring.
- [ ] **[L]** More achievements: 95% accuracy over 30 s, 10 runs in a day, 7-day streak, first run in every mode, a clean 30 words in a row. Three achievements is too few to feel like progress. Persist unlocked ones in `settings.json`/`achievements.json` so pruning the history file doesn't re-lock them.
- [ ] **[L]** Sudden death ends on the first wrong word even when the player only fat-fingered Enter early. Add a one-time "strike" allowance per run (setting: 0 / 1 / 3 strikes) between full sudden death and Practice mode.
- [ ] **[L]** Share line: a "copy result" key on the game-over screen that prints a one-line summary (`HyperTyper Streak 30s: 62 WPM 97% acc, score 340`) to stdout/clipboard (`wl-copy`/`xclip`/`pbcopy` if present).

### Data / content
- [ ] **[M]** The Quotes mode has only 40 lines, none over 56 characters, so they are short proverbs rather than passages. Add a few longer 80-120 character quotes and test how they wrap on an 80-column terminal (the prompt line is `len(target) + 10` wide and can wrap and break the in-place redraw, `:379`).
- [ ] **[L]** `data/code.txt` mixes languages and tiny snippets (`x = [1, 2, 3]`). Split into per-language files (`python`, `js`, `bash`, `c`) so Code Snippets mode can be filtered, and add multi-token lines with brackets and operators, which are the hard part of typing code.
- [ ] **[L]** Mode difficulty differs wildly (Pokemon names, brainrot slang, linkedin phrases) but menu items look the same. Add a short one-line description or tag (`easy`, `symbols`, `phrases`) next to each mode in the picker.
- [ ] **[L]** Cities has only 50 entries (US state capitals). In a 120 s run at 40+ WPM the bag runs out and repeats; extend it (world capitals) or let a mode declare a "finite" list that ends the run when exhausted.

### Packaging / repo
- [ ] **[M]** `PKGBUILD` still has `depends=('python' 'python-pygame' 'python-colorama')` but the code no longer imports colorama and pygame is optional. Change to `depends=('python')` and `optdepends=('python-pygame: sound effects')`, add `install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"`, bump `pkgver`, tag, update `sha256sums`, and regenerate `.SRCINFO` in the same commit.
- [ ] **[M]** `pyproject.toml` with a `[project.scripts] hypertyper = "hypertyper:main"` entry (move the `__main__` block into `main()`), so `pipx install .` works on non-Arch systems. README's pip route is only "clone and run".
- [ ] **[M]** Add a GitHub Actions workflow that runs `python3 test_hypertyper.py` on 3.8, 3.11 and 3.13, plus a Windows job (the `msvcrt` path has no coverage at all).
- [ ] **[L]** Tests cover the pure helpers only. Add cases for `score_key` (time, difficulty, practice suffixes), `pick_words` (the `< 10` fallback), the `load_high_scores` migration path, and the corrupt-file recovery above; an end-to-end smoke test can drive `streak_mode` through piped stdin since `screen()` already has a non-tty branch.
- [ ] **[L]** README roadmap still lists "More game modes / More settings / More color themes". Replace with concrete items from this file so the list tells a reader what is actually planned, and refresh `hypertyper.gif` (it predates the live timer, auto-submit and new HUD).
