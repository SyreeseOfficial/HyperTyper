# HyperTyper: Findings

Reviewed 2026-10-08. Single file `hypertyper.py` (774 lines) + `data/*.txt`. Tags: **[H]** high value, **[M]** medium, **[L]** low. `[ ]` = open.

## Bugs / correctness
- [ ] **[M]** Timer is not live: `~Ns` is drawn once per word (`:458`), so it freezes while you type. A long word at 1 s left is still accepted or silently thrown away (`:477`). Pick a rule: reject late input with a message, or draw a live timer (see Features).
- [ ] **[M]** Random word repeats back-to-back (`random.choice`, `:453`), and duplicates in the lists weight some words higher. Use a shuffled bag, then dedupe the data files.
- [ ] **[M]** Spanish mode needs exact characters: accent-insensitive compare (`unicodedata` NFD, strip combining) or at least accept un-accented input. (Only 1 non-ASCII line today, so low risk, but any future list will hit this.)
- [ ] **[L]** Initials loop is a `while True` that always breaks on the first pass, with two copy-pasted save blocks (`:554-574`). Collapse to `name = (input or "UNK")[:3]`; save once.

## Performance / efficiency
- [ ] **[M]** `clear_screen()` shells out via `os.system('clear')` every word (`:276`). Print `"\033[2J\033[H"` (colorama already handles Windows); removes a process spawn per word and the flicker.
- [ ] **[M]** `pygame` import is slow and prints its "Hello from the pygame community" banner. Set `os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1"` before import; use `pygame.mixer.init()` only. Lazy-import when sound is on.
- [ ] **[L]** `load_words` re-reads and re-filters the file on every mode entry and each retry-loop is fine, but cache per file in a dict.
- [ ] **[L]** `load_high_scores()` re-reads the JSON file multiple times per game over (`:543`, `:561`, `:570`). Load once, reuse.
- [ ] **[L]** `get_visible_length` recompiles the ANSI regex on each call (`:207`). Compile once at module level.
- [ ] **[L]** Remove the forced `time.sleep(1)` when pygame is missing (`:21`) and `time.sleep(2)` when a word file is missing (`:125`). Print once, never block startup.

## UI / UX
- [ ] **[H]** Live countdown timer that ticks every 100 ms while typing (needs the raw-mode loop above).
- [ ] **[M]** Auto-submit on correct final character (or Space) in non-exact modes, so Enter is not needed per word. Keep Enter for exact-match modes (code/terminal).
- [ ] **[M]** Remove the fixed 0.2 s sleep after every correct word (`:505`). It eats time budget and slows pace. A brief inline "+N" flash on the same screen is enough.
- [ ] **[M]** Main menu title says "CLI TYPING GAME" (`:732`); use the HyperTyper logo/name. Show current time limit and best score on the mode picker.
- [ ] **[M]** Mode list is a 13-line `if/elif` chain duplicated in the menu text (`:601-650`). Drive both from one `MODES = [(name, file, exact)]` list so menu number, label, and launch never drift apart.
- [ ] **[M]** Game Over: show accuracy, best combo, longest word, and compare to personal best ("+12 vs best"). Data is already tracked or trivial to add.
- [ ] **[L]** Menu choices need Enter; allow single keypress selection once raw input exists.
- [ ] **[L]** Re-center on terminal resize and warn when the terminal is smaller than 60x15.
- [ ] **[L]** Settings: allow custom timer value and sound volume (`Sound.set_volume`), not only the 15/30/60/120 cycle (`:685`).
- [ ] **[L]** Colorblind-safe palette option (replace red/green-only signals with symbols too). Matches "Color themes" on the roadmap.
- [ ] **[L]** Pause/quit key in game (Esc) instead of Ctrl-C only.

## New features
- [ ] **[H]** Top-10 leaderboard per mode with date and WPM (README promises "leaderboard" but only 1 entry per mode exists).
- [ ] **[M]** CLI flags with `argparse`: `--mode food --time 60 --no-sound --version`. Lets the AUR package launch straight into a mode.
- [ ] **[M]** User word lists: any `~/.config/hypertyper/words/*.txt` shows up as a mode automatically (name from file name). Pair with the MODES table above.
- [ ] **[M]** "Practice" / forgiving mode: mistakes cost a combo reset instead of ending the run. Current sudden death is harsh for new players, especially in code mode.
- [ ] **[M]** Stats history (`history.jsonl`): date, mode, time, WPM, accuracy, score; add a Stats screen with averages and a trend sparkline.
- [ ] **[M]** Quotes/sentences mode (full lines, punctuation) for real-world typing practice.
- [ ] **[L]** Daily challenge: seed `random` with the date so everyone gets the same words; separate daily record.
- [ ] **[L]** Difficulty filter by word length (short/medium/long) for the word-based modes.
- [ ] **[L]** Local multiplayer / hot-seat (on roadmap). Easiest form: two players alternate runs with the same seed, compare scores.
- [ ] **[L]** Achievements (first God Mode, 50 WPM, 100 words in one run).

## Remove / clean up
- [ ] **[M]** Delete `organize_sound_files()` (`:131-152`) and its call (`:767`). One-time dev migration that runs a relative `sounds` check every launch; sounds already live in `data/sounds`.
- [ ] **[M]** Dedupe word lists: linkedin 327, spanish 394, words 314, lorem 151, terminal 48, animals 34 duplicate lines. `sort -u` them (keep file order if it matters, use `awk '!s[$0]++'`).
- [ ] **[L]** Dead code: `pause()` (`:315`), `WORD_FILE` (`:52`), unused `Back` import (`:9`), commented-out sleep (`:189`), stale "Optional" migration comment (`:49`), long monologue comment in `pause()`.
- [ ] **[L]** `data/settings.json` is a leftover; settings live in `~/.config/hypertyper/`. Remove from the repo if tracked (`git ls-files data/settings.json`).
- [ ] **[L]** Docstrings still say "data/settings.json" (`:65`, `:87`). Update to `SETTINGS_FILE`.
- [ ] **[L]** README: `pygame` is listed as required in `requirements.txt` but the game works without it; mark optional. Add LICENSE file (PKGBUILD says MIT, repo has none). Document the config path and that high scores are in `~/.config/hypertyper/`.
- [ ] **[L]** No tests. One `test_hypertyper.py` for `get_combo_tier`, `load_words` filtering, and WPM math is enough.
- [ ] **[L]** Consider dropping `colorama` on Linux/macOS (raw ANSI works) to cut a dependency; keep only if Windows support matters.

## Completed
- [x] **[H]** Type-ahead breaks the game: keys pressed during the countdown or the 0.2 s "OK!" flash stay in stdin and become the next `input()`, so the next word is "wrong" and the run ends instantly (`hypertyper.py:308`, `:505`). Fix: `termios.tcflush(sys.stdin, termios.TCIFLUSH)` right before each prompt (guard for Windows).
- [x] **[H]** Wrong-word message is never seen: it prints at `:517`, then `break` goes straight to the Game Over screen, which calls `clear_screen()`. Show it inside the Game Over lines ("You typed X, expected Y").
- [x] **[H]** High scores ignore the timer length: 15 s and 120 s runs share one record per mode (`:543`). Key by `f"{mode}@{time_limit}s"`, or store a per-time table.
- [x] **[M]** Ctrl-D (EOF) is only caught on the word prompt (`:473`). On the initials prompt, menus after game over, splash, or pause it dumps a traceback, and `__main__` only catches `KeyboardInterrupt` (`:772`). Catch `EOFError` at top level too.
- [x] **[M]** First run prints "Migrated high scores to new format..." for no reason: `__main__` writes the old format `{"Streak": 0}` (`:761`) and the loader migrates it. Write `{}` or the new format.
- [x] **[L]** Emoji in "🚨 NEW HIGH SCORE" is 2 columns wide but counted as 1, so that line sits 1 col off-center (`get_visible_length`, `:205`). Use `wcwidth` or drop the emoji.
- [x] **[L]** WPM uses full elapsed time including the pause after a wrong word and counts only correct chars, so it is not comparable with other tools (`:521-527`). Document the formula or show raw + net WPM.
- [x] **[L]** `PKGBUILD` says `pkgver=1.0.1` but tag `v1.0.2` exists. Bump PKGBUILD and `.SRCINFO` together, and replace `sha256sums=('SKIP')` with a real sum before AUR push.
- [x] **[L]** PKGBUILD maintainer is a placeholder `syreese@example.com`. Fix before publishing.
- [x] **[H]** Per-keystroke feedback: right now you type blind and press Enter. Switch to raw-mode input (`termios`/`tty`, `msvcrt` on Windows) and color each typed char green/red as you go. This is the single biggest feel upgrade.
