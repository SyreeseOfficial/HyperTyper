# HyperTyper — Findings

Rounds 1 and 2 (both 2026-10-23) added to the 2026-10-08 and 2026-10-13 lists, audited against `hypertyper.py` (893 lines) at commit `6c01baf`. Older open items are merged into the list below (effort `?` where the old list gave none); done items from earlier rounds are kept at the bottom. Items marked "(older item)" restate or extend an entry that is also in this list. "Run today" means I reproduced it.

Effort: **XS** under 5 min · **S** about 15 min · **M** about an hour · **L** half a day · **?** not estimated. Sorted by value, then effort, then area.

**271 items.** 14 high, 204 medium, 53 low.

## Do these first

1. A non-object `settings.json` crashes at startup _[Bug, XS]_
2. Terminal is left in a bad state if the game is killed with SIGTERM/SIGHUP (window closed): `cbreak_mode`… _[Bug, XS]_
3. No cursor hiding: the text cursor blinks at the end of the last drawn line while typing _[Bug, XS]_
4. Settings values are never validated _[Bug, S]_
5. Settings and history writes are not atomic _[Bug, S]_
6. Cheating by paste is possible _[Bug, S]_
7. Record per-keystroke data (key, expected key, timestamp) in memory during a run and write a compact… _[Feature, S]_
8. Rank runs by something harder to game than score _[Gameplay, S]_

## High value

1. [ ] **[XS]** _Bug_ — A non-object `settings.json` crashes at startup. `[1]` in the file makes `SETTINGS.update(data)` raise `TypeError: object is not iterable` (run today), and `load_settings` only catches `JSONDecodeError`/`IOError`. Check `isinstance(data, dict)` and fall back to defaults.
2. [ ] **[XS]** _Bug_ — Terminal is left in a bad state if the game is killed with SIGTERM/SIGHUP (window closed): `cbreak_mode` restores in `finally`, but a signal-kill skips it and the cursor/echo can stay off. Install SIGTERM/SIGHUP handlers that raise `SystemExit`, and register `atexit` to reset attributes.
3. [ ] **[XS]** _Bug_ — No cursor hiding: the text cursor blinks at the end of the last drawn line while typing. Emit `\033[?25l` when entering `screen()` and restore `\033[?25h` in a `finally`/`atexit` (restoring matters for crashes).
4. [ ] **[S]** _Bug_ — Settings values are never validated. `{"volume": "loud", "time_limit": 0}` loads as-is (run today), then `apply_volume` raises `TypeError` and a 0-second timer ends every run instantly. Clamp/coerce each key against `DEFAULT_SETTINGS` types and ranges (volume 0-100, time 5-600, difficulty in `LENGTHS`).
5. [ ] **[S]** _Bug_ — Settings and history writes are not atomic. `save_settings`, `save_high_scores` open with `'w'`, so a crash mid-write truncates the file; write to `file.tmp` and `os.replace`. (Also listed for scores in the older list; settings have the same flaw.)
6. [ ] **[S]** _Bug_ — Cheating by paste is possible. Pasting a word into the terminal arrives as a burst of characters and scores perfectly; detect more than N characters inside one `read_key` poll interval and ignore/flag them (and mark the run `suspect` in history).
7. [ ] **[S]** _Feature_ — Record per-keystroke data (key, expected key, timestamp) in memory during a run and write a compact summary line to `history.jsonl`. It unlocks weak-keys drills, a real accuracy figure and replay, and everything in the stats ideas below depends on it.
8. [ ] **[S]** _Gameplay_ — Rank runs by something harder to game than score. Score is `len(word) * multiplier`, so 8x combo makes long words dominate and a single lucky streak beats consistent play. Add a "rank by WPM x accuracy" view in the Hall of Fame so a high-score alone isn't the only ladder.
9. [ ] **[S]** _Gameplay_ — Add a reaction/lead-in-free "Test" mode: fixed 30 words, no combo, no sudden death, ends when the last word is typed and reports WPM/accuracy. Matches how other typing tools measure and gives a comparable number.
10. [ ] **[?]** _Bugs_ — WPM is inflated by very short runs. `wpm()` clamps elapsed to 1 s (`:263`) and sudden death ends the run at the first typo, so typing two 6-letter words in 1.5 s then missing the third records ~96 WPM. That feeds "Best WPM", the trend sparkline and the **Speed Demon (50 WPM)** achievement (`:95`). Require a minimum run length (e.g. >= 10 s or >= 10 words) before a run counts toward WPM stats and WPM achievements, or mark short runs `"short": true` in `history.jsonl` and skip them.
11. [ ] **[?]** _Bugs_ — Accuracy ignores corrected mistakes. `accuracy = good_chars / raw_chars` (`:700`) only counts characters in submitted words, so typing a wrong letter and hitting Backspace costs nothing. Count every keystroke and every wrong keystroke inside `screen()` (return them with the buffer) and report `accuracy` plus "corrected errors". This is also the prerequisite for the weak-keys drill below.
12. [ ] **[?]** _Bugs_ — Hall of Fame breaks as scores accumulate. Keys are `mode@30s long practice` (`score_key`, `:206`), so 13 modes x 4 timers x 4 lengths x practice can produce hundreds of rows. `build_frame` keeps `out[-rows:]` (`:365`), so a long table loses its **top**, i.e. the title and header. Show one mode per page with Left/Right, or show only the best row per mode with a "filter: 30s / all" toggle.
13. [ ] **[?]** _Skip_ — Top-10 leaderboard per mode with date and WPM (README promises "leaderboard" but only 1 entry per mode exists).
14. [ ] **[?]** _UX / UI_ — Arrow-key / `j` `k` menu navigation with a highlighted row and Enter to select. `read_key` already swallows arrow sequences and returns `''` (`:325`), so they do nothing today. Digits stay as shortcuts, but with 14+ items the numbers need two keystrokes and mode 1 needs Enter because `10 <= 14` (`choose`, `:439`), which is inconsistent with modes 2-9.

## Medium value

15. [ ] **[XS]** _Bug_ — `play_sound("victory")` plays when time runs out even with zero correct words. Play `gameover` for score 0 and `victory` only when the run scored.
16. [ ] **[XS]** _Bug_ — `combo in (3, 5, 7, 10, 12)` duplicates the thresholds in `get_combo_tier`; change a tier and the level-up sound drifts. Compare `get_combo_tier(combo)[0] != get_combo_tier(combo - 1)[0]`.
17. [ ] **[XS]** _Bug_ — `history.jsonl` records `time` but not `difficulty`, so Stats cannot separate short-word from long-word runs. Add `difficulty`, `version`, `practice` (exists) and the `key` used for the high score.
18. [ ] **[XS]** _Bug_ — The old-format migration treats any `int` as a score, including `True`/`False` (JSON bools are ints in Python). Exclude `bool`.
19. [ ] **[XS]** _Bug_ — `get_visible_length` counts combining characters (accents in NFD input, emoji variation selectors) as width 1; use `unicodedata.combining`/`wcwidth` logic so Spanish words typed in NFD and the star `★` align.
20. [ ] **[XS]** _Bug_ — `★` and `·` use ambiguous East Asian width; in CJK-locale terminals they render 2 columns and misalign the Stats list. Use ASCII `*` and `-` when `LANG` is a CJK locale or when `colorblind` is on.
21. [ ] **[XS]** _Data_ — `quotes.txt` has 40 lines, max 56 characters, all ASCII; none use curly quotes, dashes or accented names, so punctuation practice is limited to `, . ' ?`. Add typographic punctuation lines (`—`, `"…"`, `…`) behind a "typographic" tag and include numbers.
22. [ ] **[S]** _Audio_ — Convert WAVs to OGG (`correct.wav` 48 KB, `countdown.wav` 682 KB, `splash.wav` 387 KB: 2 MB total of the repo) and load with pygame; cuts the package size by ~80% and git history growth.
23. [ ] **[S]** _Audio_ — Trim the countdown wav to the actual 3-2-1 length; 682 KB suggests ~4 s and it overlaps the "GO!" frame.
24. [ ] **[S]** _Audio_ — Pre-initialize the mixer with a small buffer (`pygame.mixer.pre_init(44100, -16, 2, 256)`) to reduce latency on the `correct` click, which plays on every word.
25. [ ] **[S]** _Audio_ — Per-sound volume (keystroke click quieter than victory) and a master slider with finer steps than 25%.
26. [ ] **[S]** _Audio_ — Optional per-keystroke click sound with a different pitch for wrong keys.
27. [ ] **[S]** _Audio_ — Distinguish "audio unavailable" from "sound off" in Settings and show the reason (no device, no pygame) on the Sound row (older item mentions the message is lost).
28. [ ] **[S]** _Audio_ — Fall back to `paplay`/`aplay`/`afplay` subprocesses when pygame is missing so sound works without a Python dependency.
29. [ ] **[S]** _Audio_ — Mute automatically when `TERM`/SSH shows a remote session (no local audio).
30. [ ] **[S]** _Audio_ — Play the sounds asynchronously on a channel limit so rapid words don't stack and cut off (`pygame.mixer.set_num_channels`).
31. [ ] **[S]** _Audio_ — Play a soft tick on each correct character at low volume (optional), with a distinct buzz on a wrong one; the current sounds are word-level only.
32. [ ] **[S]** _Audio_ — Respect the system "do not disturb" / mute: skip sound init when `PULSE_SERVER` is absent or when stdout isn't a tty.
33. [ ] **[S]** _Bug_ — `pause_screen` says "Enter = resume" but `wait_key` returns on the first key: pressing Space/Esc/any key also resumes (and a wrongly pressed key during the pause is lost). Only Enter should resume; use `screen(..., done=lambda b: b.lower() == 'q')`.
34. [ ] **[S]** _Bug_ — `load_high_scores` ghost entry: when the file is corrupt it returns `{"Streak": {"score": 0, "name": "---"}}`, which the Hall of Fame lists as a real `Streak` row with no timer suffix. Return `{}`.
35. [ ] **[S]** _Bug_ — `score_key` uses `SETTINGS['time_limit']` live but `streak_mode` computes `key` once before the retry loop; changing nothing mid-run is fine, but `run["time"]` uses `int(time_limit)` and the key uses `int(SETTINGS[...])` so a float setting (`30.5` hand-edited) saves under `@30s` and stores 30. Normalize the setting to int on load.
36. [ ] **[S]** _Bug_ — `elapsed = time_limit if status == "timeout"` ignores the time spent on the last unfinished word, which is fine, but `wpm` for a "wrong" ending uses actual elapsed seconds; compare equal-length timeouts vs sudden deaths in the Hall of Fame separately or normalize.
37. [ ] **[S]** _Bug_ — Raw-mode `read_key` ignores bracketed paste and mouse escape sequences and swallows any sequence after Esc with 20 ms reads; a slow SSH link can split an arrow sequence so the first `\x1b` is read as Esc and pauses the game. Make the Esc timeout 50-100 ms when `SSH_TTY` is set.
38. [ ] **[S]** _Bug_ — Terminals that send `\x1b[200~` bracketed paste leave the remainder `[200~...` in the buffer when Esc is read; disable bracketed paste mode (`\033[?2004l`) on entry and restore on exit.
39. [ ] **[S]** _Bug_ — `screen()` limits typed length to `reserve = len(target) + 10`; a user holding a key can still fill the buffer with 10 extra characters on a wrong word, and each is colored BAD; fine, but the "wrong" message prints the whole buffer. Truncate the displayed typed text to 40 characters.
40. [ ] **[S]** _Bug_ — On resize while typing, the frame is redrawn at 10 Hz but leftover rows from a larger earlier frame stay until the next `\033[J`; verify by shrinking the terminal mid-game. `build_frame` ends with `\033[J` so this should be fine; add a test frame renderer check.
41. [ ] **[S]** _Bug_ — Mixed key case in menus: `choose()` returns `'q'`, `'Q'`, letters as-is and callers ignore them; pressing `r` on a menu does nothing and `R` at game over is lowercased, but menus compare exact strings. Normalize case in `choose`.
42. [ ] **[S]** _CLI_ — `argparse` flags (older item): `--mode`, `--time`, `--practice`, `--no-sound`, `--no-splash`, `--version`, `--stats`, `--list-modes`.
43. [ ] **[S]** _CLI_ — Non-interactive stats: `hypertyper --stats` prints averages and exits, for shell prompts or status bars.
44. [ ] **[S]** _CLI_ — `hypertyper --daily` jumps straight into the daily challenge.
45. [ ] **[S]** _CLI_ — Accept `--words FILE` to play any file once without installing it as a mode.
46. [ ] **[S]** _CLI_ — Exit codes and `--json` output for scripted runs (CI of typing tests is unlikely, but this makes the game testable end to end).
47. [ ] **[S]** _CLI_ — Shell completion for `--mode` (bash/zsh/fish) generated from the mode list.
48. [ ] **[S]** _CLI_ — `--list-modes` prints mode names and file paths including custom lists; `--word-file PATH` plays any file as an ad-hoc mode without installing it.
49. [ ] **[S]** _CLI_ — `--seed N` for reproducible word order (testing and challenges) and `--no-save` to play without touching highscores/history.
50. [ ] **[S]** _CLI_ — `--config-dir PATH` to point at a different profile, for two players sharing one machine.
51. [ ] **[S]** _CLI_ — `hypertyper stats --json` for status bars (waybar) showing today's runs and best WPM.
52. [ ] **[S]** _Config_ — Validate and migrate settings with a `version` key so new defaults are applied explicitly rather than by silently merging.
53. [ ] **[S]** _Config_ — Provide `--config-dir` and `--reset-settings` flags.
54. [ ] **[S]** _Config_ — Support `HYPERTYPER_NO_SOUND=1` and similar env overrides.
55. [ ] **[S]** _Config_ — Remember the last played mode and time limit and preselect them in the menu.
56. [ ] **[S]** _Config_ — Per-mode settings (e.g. exact-case on for code, off for words) stored under `mode_settings`.
57. [ ] **[S]** _Config_ — Store settings in a typed dataclass with a `from_dict` that ignores unknown keys, replacing the global dict mutated across functions.
58. [ ] **[S]** _Data_ — Add per-language word lists (French, German, Portuguese, Italian) and a Dvorak/Colemak-aware "layout" note in the README.
59. [ ] **[S]** _Data_ — Longer quotes (older item) with source attribution displayed after the run, and a "quote of length N" filter.
60. [ ] **[S]** _Data_ — Split `code.txt` by language (older item) and add real multi-line snippets typed with Enter between lines.
61. [ ] **[S]** _Data_ — Common-words frequency lists (top 200 / 1000 / 5000 English words) as selectable difficulty levels, the standard in typing tools.
62. [ ] **[S]** _Data_ — Add `data/README` or header comments describing each file's format and licensing (quotes need attribution; Pokemon names are trademarked).
63. [ ] **[S]** _Data_ — Data validation script: flag duplicates, trailing spaces, non-printable characters and entries longer than the terminal width.
64. [ ] **[S]** _Data_ — Provide a profanity/NSFW flag: Brainrot and UwU lists are fine, but custom lists shared online may not be; add a `family_friendly` setting that filters a small denylist.
65. [ ] **[S]** _Data_ — Mark which modes support case-insensitive match and show it in the mode picker, because "Cities" requires exact capitals typed out.
66. [ ] **[S]** _Data_ — Capitals: expand to world capitals (older item) and add a "flags/countries" list; include accents handled by `fold`.
67. [ ] **[S]** _Data_ — Add programming keywords per language, regex snippets, SQL statements, git commands, vim commands, docker commands.
68. [ ] **[S]** _Data_ — Add a "numbers & dates" mode (phone-like strings, ISO dates, IP addresses) for data-entry practice.
69. [ ] **[S]** _Data_ — Add an "email & URL" mode with symbols common in real typing.
70. [ ] **[S]** _Data_ — Sentence mode generated from word lists with simple grammar (Markov or template) for endless unique text.
71. [ ] **[S]** _Data_ — Fetch fresh quotes from a local file the user can update; document the file format and a script to append.
72. [ ] **[S]** _Data_ — Word difficulty weighting by length and rare letters so "easy/hard" means more than length.
73. [ ] **[S]** _Data_ — Spanish mode teaches misspellings. `data/spanish.txt` has only one non-ASCII line (`albañil`), so words like `ano`, `cancion`, `corazon`, `espanol` and `pequeno` appear without their ñ/accents (run today: 33 entries end in `cion`). The game's `fold()` forgives the typist, but the list itself is wrong; regenerate it from a proper accented source and keep `fold` for leniency.
74. [ ] **[S]** _Data_ — `linkedin.txt` is 690 lines and `brainrot.txt` 401 of mostly slang that dates quickly; add a `data/CREDITS.md` noting origin and a dated header comment per list so stale slang can be pruned.
75. [ ] **[S]** _Data_ — Add a "Common words" mode driven by real frequency lists (top 200/1000 English words) and per-length buckets, so the Streak mode isn't one flat 750-word list with no frequency weighting.
76. [ ] **[S]** _Data_ — Add a programming-symbols mode with bracket-heavy snippets sourced per language (the `code.txt` has 131 short lines ≤21 chars); longer multi-token lines (e.g. `for (int i = 0; i < n; i++)`) test real coding accuracy.
77. [ ] **[S]** _Docs_ — README: add a "Scoring" section for combo tiers and multipliers (today only WPM is documented) and a table of modes with their match type.
78. [ ] **[S]** _Docs_ — README: document keys (Esc pauses, Enter/Space submit, R retry) and the practice-mode rules in one table.
79. [ ] **[S]** _Docs_ — README: document the file formats of `highscores.json` and `history.jsonl` so users can back up/edit them.
80. [ ] **[S]** _Docs_ — README: correct the roadmap (older item) and link to this file.
81. [ ] **[S]** _Docs_ — README: add Windows notes (needs Windows Terminal for ANSI; `msvcrt` input path) and macOS notes.
82. [ ] **[S]** _Docs_ — Record a fresh demo GIF showing the live timer, combo tiers and Stats; the current gif predates the live timer and per-key colouring.
83. [ ] **[S]** _Docs_ — Add a CONTRIBUTING note on adding a mode (add to `MODES`, add a data file, add a test) and on word-list licensing.
84. [ ] **[S]** _Docs_ — README: add keyboard controls, scoring/combos table, mode list with match type (exact vs word), config file formats and an FAQ ("why did my run end?").
85. [ ] **[S]** _Docs_ — Add `CONTRIBUTING.md` for adding modes and word lists (format, size limits, license/attribution, no offensive content).
86. [ ] **[S]** _Gameplay_ — Add a per-word time bonus: finishing a word under its par time (len x 0.15 s) adds a speed multiplier so slow-but-accurate typists don't tie with fast ones.
87. [ ] **[S]** _Gameplay_ — Combo decay instead of hard reset in practice mode: a mistake drops the combo by two tiers rather than to zero.
88. [ ] **[S]** _Gameplay_ — "Zen" mode with no timer: type until you quit, record WPM/accuracy per 25 words, no high score. Good for warm-up.
89. [ ] **[S]** _Gameplay_ — "Marathon" mode: fixed 100 words, race the clock, ranked by total time; fits the speedrun crowd.
90. [ ] **[S]** _Gameplay_ — Time attack: start with 30 s, each correct word adds 1 s (length-weighted), wrong word subtracts 3 s; ends at zero.
91. [ ] **[S]** _Gameplay_ — Ghost run: replay your best run's word timings as a progress bar next to the live one (needs per-word timestamps in history).
92. [ ] **[S]** _Gameplay_ — Boss words: every 20th word is a long phrase worth 5x, shown in a different color.
93. [ ] **[S]** _Gameplay_ — Power-ups (slow-time for 3 s on a 10-word streak, shield that absorbs one mistake). Keep behind a `fun` setting so the default stays pure.
94. [ ] **[S]** _Gameplay_ — Letter-set drills: "home row only", "top row", "no vowels", "numbers", "symbols" generated from a character set rather than a word list.
95. [ ] **[S]** _Gameplay_ — Number-row and symbol mode for programmers (`{}[]()<>=!&|`), generated with weighted bracket pairs, since only `code.txt` has symbols today.
96. [ ] **[S]** _Gameplay_ — Bigram/trigram drills generated from the user's worst pairs (needs keystroke data).
97. [ ] **[S]** _Gameplay_ — Rhythm mode: show a metronome beat and score evenness of intervals between keys.
98. [ ] **[S]** _Gameplay_ — Two-player alternating mode with the same seed (older open item) implemented as "pass the keyboard": score both, show winner; no network needed.
99. [ ] **[S]** _Gameplay_ — Daily challenge (older open item): seed by date, one scored attempt per day, a streak of days played, stored separately.
100. [ ] **[S]** _Gameplay_ — Weekly challenge with a fixed word list and a printed result string to share (`HT-2026W43 62wpm 97%`).
101. [ ] **[S]** _Gameplay_ — Typing speed goals: set a target WPM in settings and show a progress bar toward it on the Stats page.
102. [ ] **[S]** _Gameplay_ — Mistake review screen after a run: list wrong words with what was typed vs expected, and offer "drill these now".
103. [ ] **[S]** _Gameplay_ — Lesson ladder: structured progression (home row, then top row, then words, then sentences) unlocking in order, for beginners.
104. [ ] **[S]** _Gameplay_ — Handicap by mode: scale high scores by mode difficulty (Spanish vs fruit) so cross-mode leaderboards are meaningful.
105. [ ] **[S]** _Gameplay_ — Slow-start fairness: first word appears after "GO!" with the timer paused until the first keypress; today the clock starts at "GO!" and the first word is costly if you look away.
106. [ ] **[S]** _Gameplay_ — Show next word preview (dimmed) so players can read ahead, optional setting like in monkeytype.
107. [ ] **[S]** _Gameplay_ — "Stop on error" vs "allow backspace" vs "forgive typos on correction" options for exact modes; backspace policy changes difficulty a lot.
108. [ ] **[S]** _Gameplay_ — Case sensitivity setting for exact modes (code/terminal) so beginners can type lowercase.
109. [ ] **[S]** _Gameplay_ — Whitespace handling: collapse repeated spaces in quotes/exact mode and trim trailing space so an extra Space doesn't fail a run.
110. [ ] **[S]** _Gameplay_ — Punctuation toggle for Quotes mode: type without punctuation, with punctuation, or numbers.
111. [ ] **[S]** _Gameplay_ — Word difficulty is length-only (`LENGTHS`). Score words by letter frequency/bigram difficulty (`qz`, `ght`) and use it for adaptive selection: easier words after a miss, harder after a streak.
112. [ ] **[S]** _Gameplay_ — Add "accuracy streak" scoring: combo multipliers currently depend on consecutive words; add a per-character perfect-run bonus so slow-but-clean typing isn't dominated by fast sloppy runs.
113. [ ] **[S]** _Gameplay_ — Per-run replay: record keystroke timestamps and let the player watch their last run back at 2x on the game-over screen; reveals hesitation points. (needs the keystroke data from the older item)
114. [ ] **[S]** _Gameplay_ — "Sudden death" fairness: allow one backspace-correction per word before it counts as an error, as an optional rule, since the live coloring already shows mistakes.
115. [ ] **[S]** _Gameplay_ — Add a warm-up mode before the first run of the day: 20 easy words, no scoring, ends with a suggestion for the day's mode based on recent weakness.
116. [ ] **[S]** _Gameplay_ — Typing of numbers: numeric-row drills (phone numbers, dates, IPs) and a numpad mode, which are separate skills from word typing.
117. [ ] **[S]** _Gameplay_ — Touch-typing trainer: show an on-screen keyboard highlighting the next key and the finger color, with lessons that unlock by accuracy.
118. [ ] **[S]** _Gameplay_ — Multiplayer over a shared seed without a server: export a "challenge code" (mode, time, seed) as a short string; friends enter it and compare scores out of band.
119. [ ] **[S]** _Packaging_ — PKGBUILD: drop `python-colorama`, make `python-pygame` an `optdepends` (older item) and add a `check()` that runs the tests.
120. [ ] **[S]** _Packaging_ — Update PKGBUILD/.SRCINFO automatically from a tag via a release script so versions can't drift (1.0.2 now; the code has more features than the tag).
121. [ ] **[S]** _Packaging_ — Provide a `.desktop` entry and icon so it launches from an app menu in a terminal (`Terminal=true`).
122. [ ] **[S]** _Packaging_ — Publish to PyPI as `hypertyper` and add a Homebrew formula/Nix flake for macOS users.
123. [ ] **[S]** _Packaging_ — Add a man page (`hypertyper.1`) installed by the PKGBUILD.
124. [ ] **[S]** _Packaging_ — Use `sys.executable`-independent shebang (`#!/usr/bin/env python3` exists); add `python_requires` check printing a clear message for <3.8 (f-strings with `=`? none; walrus not used) and verify 3.8 compatibility in CI.
125. [ ] **[S]** _Packaging_ — Version constant `__version__` and `--version`; bump script that updates it, PKGBUILD and `.SRCINFO` together.
126. [ ] **[S]** _Packaging_ — `DATA_DIR` falls back to `/usr/share/hypertyper/data` only if the local dir is missing; a `pip install` into site-packages would find neither. Add a third lookup next to the module and `XDG_DATA_DIRS`.
127. [ ] **[S]** _Packaging_ — Compress `hypertyper.gif` (921 KB) to WebP/MP4 for the README, or host it as a release asset to keep clones small.
128. [ ] **[S]** _Packaging_ — Add a `CHANGELOG.md` and GitHub releases with notes per tag.
129. [ ] **[S]** _Quality_ — Split the 893-line single file into modules (`input.py`, `screen.py`, `store.py`, `modes.py`) once multiplayer or new modes land; keep the single-file install by building a zipapp.
130. [ ] **[S]** _Quality_ — Extract `streak_mode` (130 lines, nested loops, 15 locals) into a `Run` object with `next_word()`, `submit()` and `finish()` methods; the control flow with `status` strings is hard to test.
131. [ ] **[S]** _Quality_ — Replace string statuses (`'enter'`, `'auto'`, `'esc'`, `'timeout'`, `'wrong'`) with an `Enum` to avoid typos.
132. [ ] **[S]** _Quality_ — Replace module-level mutable globals (`SETTINGS`, `GOOD`, `BAD`, `SOUNDS`) with a `Game` context object, enabling parallel tests and a second UI.
133. [ ] **[S]** _Quality_ — Type hints and `mypy` run; the data shapes (`run` dict, scores dict) get documented.
134. [ ] **[S]** _Quality_ — Add `ruff` config and fix issues; the file mixes single/double quotes and has bare `except Exception` blocks.
135. [ ] **[S]** _Quality_ — Replace the `print` calls scattered in `init_audio`/`load_words` with a small `notice()` that queues messages for display after the splash (older items note the messages are cleared).
136. [ ] **[S]** _Quality_ — Read word files with `encoding="utf-8"` explicitly (`open(path, 'r')` uses the locale encoding; Spanish accents break under `LANG=C`). Same for settings, scores, history.
137. [ ] **[S]** _Quality_ — Make `DATA_DIR` resolution testable by injecting the path rather than computing at import.
138. [ ] **[S]** _Quality_ — A pty-driven smoke test (Python `pty` + `pexpect`) that starts the game, plays one scripted word, quits, and asserts the terminal is restored (`stty -a` before/after). Terminal-mode regressions are otherwise invisible to the unit tests.
139. [ ] **[S]** _Quality_ — Fuzz `read_key` with random byte sequences (partial UTF-8, `ESC [` fragments, mouse reports) to prove it never raises and never blocks beyond its timeout.
140. [ ] **[S]** _Quality_ — Measure frame-render cost with a benchmark (`build_frame` with 80x24 and 200x60) and add a test that guards against accidental O(n^2) regressions in the line building.
141. [ ] **[S]** _Quality_ — Split the 893-line file into modules (older item) and expose a stable `hypertyper.core` API for tests (`Game`, `Run`), keeping a single-file launcher; the global `SETTINGS` and `GOOD/BAD` make parallel tests impossible.
142. [ ] **[S]** _Quality_ — Run `python -X dev -W error` in tests; `open()` without encoding (locale-dependent) will show as warnings under `-X warn_default_encoding`.
143. [ ] **[S]** _Stats_ — Per-mode and per-timer filters on the Stats screen (older item covers per-mode; add timer and practice filters, default excluding practice).
144. [ ] **[S]** _Stats_ — Show best/average WPM for the last 7 and 30 days with a delta against the previous period.
145. [ ] **[S]** _Stats_ — Per-key accuracy heatmap on a keyboard layout drawn in the terminal (needs keystroke data).
146. [ ] **[S]** _Stats_ — Consistency score: standard deviation of per-word times; report "consistency 87%" like other typing tools.
147. [ ] **[S]** _Stats_ — Streak of consecutive days played, longest and current, shown on the main menu.
148. [ ] **[S]** _Stats_ — Total play time and total characters typed lifetime counters.
149. [ ] **[S]** _Stats_ — Personal best history graph per mode (sparkline of PBs over time).
150. [ ] **[S]** _Stats_ — Export history to CSV (`hypertyper --export csv`) for spreadsheets.
151. [ ] **[S]** _Stats_ — Import/merge history from another machine (dedupe by timestamp+mode).
152. [ ] **[S]** _Stats_ — Cap `history.jsonl` growth: archive entries older than 1 year into `history-2025.jsonl.gz` and keep aggregate counters.
153. [ ] **[S]** _Stats_ — Compute stats once and cache in `stats.json`; `load_history()` is read twice per game over and again on the Stats screen (full-file parse each time).
154. [ ] **[S]** _Stats_ — Histogram of WPM across runs (terminal bars) to see distribution, not just average.
155. [ ] **[S]** _Stats_ — Compare against "typical" WPM bands (average 40, fast 70, expert 100) as a footnote on Stats.
156. [ ] **[S]** _Stats_ — Include accuracy-weighted WPM ("adjusted WPM") on game over and in history.
157. [ ] **[S]** _Stats_ — Show the date of the best run next to Best WPM on the Stats screen.
158. [ ] **[S]** _Stats_ — Show your all-time WPM percentile against a built-in table of typical WPM bands, plus accuracy-adjusted WPM on game over.
159. [ ] **[S]** _Stats_ — Weekly summary printed on first launch of a new week: runs, time practiced, best WPM change and a suggested focus.
160. [ ] **[S]** _Stats_ — Allow tagging runs with keyboard/layout (e.g. "laptop", "mechanical", "Dvorak") in Settings so history can be split by input device.
161. [ ] **[S]** _Stats_ — Export the Hall of Fame as Markdown/CSV for sharing (`hypertyper --export`), including the date of each record.
162. [ ] **[S]** _Tests_ — Test `screen()` with a fake `read_key` feeding scripted keystrokes: auto-submit, backspace, Esc, timeout, length cap.
163. [ ] **[S]** _Tests_ — Test `build_frame` centering and the small-terminal warning with a patched `shutil.get_terminal_size`.
164. [ ] **[S]** _Tests_ — Test `load_high_scores` migration and corrupt-file paths (older item) plus bool-as-int.
165. [ ] **[S]** _Tests_ — Test `score_key` for every setting combination.
166. [ ] **[S]** _Tests_ — Test `streak_mode` end to end with scripted input: perfect run, wrong word ends, practice continues, timeout.
167. [ ] **[S]** _Tests_ — Test `fold`/`same` with NFC vs NFD input and with `ñ`.
168. [ ] **[S]** _Tests_ — Test `get_visible_length` with emoji, CJK and combining characters.
169. [ ] **[S]** _Tests_ — Test `settings_menu` volume cycle and the time-limit prompt bounds (4, 5, 600, 601, "abc").
170. [ ] **[S]** _Tests_ — Test the Windows `msvcrt` branch with a fake module injected into `sys.modules`.
171. [ ] **[S]** _Tests_ — Property-based test: `word_bag` yields each word exactly once per cycle and never repeats adjacent across cycle boundaries (including 2-word lists).
172. [ ] **[S]** _Tests_ — Smoke test with a pseudo-terminal (`pty`) that starts the game, presses a key, and quits; catches terminal-mode regressions.
173. [ ] **[S]** _Tests_ — Coverage report in CI and a badge in the README.
174. [ ] **[S]** _Tests_ — Run tests with `unittest`/`pytest` discovery; the custom `__main__` loop reports only "ok" and stops at the first failure.
175. [ ] **[S]** _UI_ — Alternate screen buffer and cursor hiding (older item) plus restoring them on all exit paths via `atexit`.
176. [ ] **[S]** _UI_ — Arrow-key menu with highlighted row (older item); also `j/k` and Home/End.
177. [ ] **[S]** _UI_ — Theme system: named palettes (dracula, nord, solarized, mono) selectable in settings, with the colorblind palette as one entry instead of a boolean.
178. [ ] **[S]** _UI_ — Monochrome/`NO_COLOR` support: honor the `NO_COLOR` env var and `TERM=dumb`.
179. [ ] **[S]** _UI_ — Draw a box frame around the HUD with box-drawing characters to anchor the layout; fall back to ASCII when `LANG` is not UTF-8.
180. [ ] **[S]** _UI_ — Progress bar for words remaining in finite modes (Cities) and for the timer (older item).
181. [ ] **[S]** _UI_ — Animate the combo tier change (brief flash of the tier name) instead of just changing text.
182. [ ] **[S]** _UI_ — Show a keyboard diagram with the next key highlighted (beginner mode) and finger colors.
183. [ ] **[S]** _UI_ — Persistent footer with key hints (`Esc pause · Enter submit`) on game screens.
184. [ ] **[S]** _UI_ — Center the HUD vertically relative to the word, not the full screen, so tall terminals don't push the prompt out of eye-line.
185. [ ] **[S]** _UI_ — Left-align the word and caret in exact modes for long lines (quotes up to 56+ chars); centered text jumps when the prompt grows.
186. [ ] **[S]** _UI_ — Hall of Fame: group by mode with the timer variants nested, show date, WPM and accuracy columns, and page with arrow keys when it overflows (older item notes overflow).
187. [ ] **[S]** _UI_ — Add a "How to play" screen in the main menu describing combos, practice, scoring and keys.
188. [ ] **[S]** _UI_ — Add an "About" screen with version, config path, data path and credits.
189. [ ] **[S]** _UI_ — Show the version in the splash and main menu (`__version__` constant tied to PKGBUILD).
190. [ ] **[S]** _UI_ — ASCII celebration animation on a new personal best (brief, skippable).
191. [ ] **[S]** _UI_ — Quiet mode (`--no-splash`) that skips the splash and its sound for fast restarts.
192. [ ] **[S]** _UI_ — Support narrow terminals gracefully (below 60 cols) by compacting the HUD to two lines instead of showing a resize warning.
193. [ ] **[S]** _UI_ — Terminal bell option (`\a`) as a fallback feedback when pygame/audio is unavailable.
194. [ ] **[S]** _UI_ — Smooth redraw: the frame writer rewrites the whole screen at 10 Hz even when only the timer changes; track changed lines and rewrite only those to cut terminal I/O over SSH.
195. [ ] **[S]** _UI_ — Support terminal sizes below 60x15 by dropping decoration (splash art, separators) instead of showing a resize warning that blocks nothing but looks broken.
196. [ ] **[S]** _UI_ — Use the Kitty/WezTerm keyboard protocol or `CSI u` when available for exact modifier handling (Ctrl-W/Ctrl-U word deletion, dead keys) instead of byte sniffing.
197. [ ] **[S]** _UI_ — Display the next word's first letters dimmed under the current word ("lookahead") as an option; many typing tools offer it to build reading speed.
198. [ ] **[M]** _Packaging_ — `pyproject.toml` with entry point and package data so `pipx install .` works (older item); include the data directory as package data and resolve `DATA_DIR` via `importlib.resources`.
199. [ ] **[?]** _Bugs_ — Hall of Fame columns misalign: the mode column is `<24` wide (`:575`) but keys like `Terminal Commands@30s practice` are 30 characters, and the `-` rule is 45 wide. Truncate or widen, and show friendly labels (`Terminal Commands · 30s · practice`) instead of the raw key.
200. [ ] **[?]** _Bugs_ — `MIN_ROWS = 15` (`:99`) is too small for the mode picker: 3 header lines + 13 modes + Back + prompt is 19+ lines (more with custom lists). A 15-18 row terminal passes the size check and silently loses the top of the menu. Compute the required rows from the actual `lines` passed to `build_frame`, or paginate long menus.
201. [ ] **[?]** _Bugs_ — Word modes silently drop entries. `load_words` keeps only `len >= 3 and isalpha()` (`:171`), which removes 21 of 276 animals (`Polar Bear`, `Sea Lion`, `Ox`), 6 foods (`Ice Cream`, `Halo-Halo`), 17 lorem words, 26 Spanish words and `mr. mime`. Either allow spaces/hyphens (and fix the space-submits rule, see below) or clean those entries out of the data files so the lists are honest.
202. [ ] **[?]** _Bugs_ — Space submits in word modes (`b.endswith(" ")`, `:647`). That makes any multi-word entry untypeable and means one stray Space mid-word ends the run in sudden death. Only treat Space as submit when the buffer does not match the start of the target (`not target_word.startswith(b)`), or make it a setting.
203. [ ] **[?]** _Bugs_ — Sound failures are invisible and Settings lies. When `pygame` is missing or there is no audio device, `init_audio()` prints "Audio disabled" (`:222`), which the splash screen's `clear_screen()` immediately erases; Settings still shows `Sound: [ON]`. It also retries the import on every settings toggle (`:806`). Remember the failure, show `Sound: [UNAVAILABLE]`, and don't retry.
204. [ ] **[?]** _Bugs_ — `load_words` warning is lost the same way (`:178`): a custom list that is empty or has only blank lines silently plays the fruit `BACKUP_WORDS` under the custom list's name, and scores get recorded against it. Skip empty custom files when building the mode list (or show "empty list" in the menu).
205. [ ] **[?]** _Bugs_ — High scores and settings can be wiped by a crash. `save_high_scores`/`save_settings` open the file with `'w'` (`:517`, `:139`), which truncates first; a kill mid-write loses everything. Worse, a corrupt `highscores.json` makes `load_high_scores` return defaults (`:512`) and the next save overwrites the corrupt file, so a recoverable file is destroyed. Write to `path + ".tmp"` then `os.replace`, and on a parse error move the bad file to `.bak` first.
206. [ ] **[?]** _Data / content_ — The Quotes mode has only 40 lines, none over 56 characters, so they are short proverbs rather than passages. Add a few longer 80-120 character quotes and test how they wrap on an 80-column terminal (the prompt line is `len(target) + 10` wide and can wrap and break the in-place redraw, `:379`).
207. [ ] **[?]** _Gameplay / features_ — Weak-keys drill: record per-character errors and keystroke latency in `history.jsonl` (needs the keystroke accounting above), then add a "Weak Keys" mode that generates words weighted toward your worst letters, plus a "slowest 10 keys" panel in Stats. This is the feature that makes typing trainers actually improve people.
208. [ ] **[?]** _Gameplay / features_ — Personal-best pace line: during a run, show `PB pace: +3 words` comparing `correct_words` at the current elapsed time against the best run for the same key (store the per-run word timestamps once, cheap). It is the single-player version of "ghost racing".
209. [ ] **[?]** _Gameplay / features_ — Per-mode Stats: best WPM, average accuracy and run count per mode, plus "runs today", "total time practiced" and a day streak. The data is already in `history.jsonl`; only the aggregation is missing.
210. [ ] **[?]** _Gameplay / features_ — Custom word lists are always exact-match (`get_modes`, `:202`), so a plain list of lowercase words still needs Enter after each. Let a first line `# words` (or a `name.words.txt` suffix) put the list in word mode with auto-submit and lowercasing.
211. [ ] **[?]** _Packaging / repo_ — `PKGBUILD` still has `depends=('python' 'python-pygame' 'python-colorama')` but the code no longer imports colorama and pygame is optional. Change to `depends=('python')` and `optdepends=('python-pygame: sound effects')`, add `install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"`, bump `pkgver`, tag, update `sha256sums`, and regenerate `.SRCINFO` in the same commit.
212. [ ] **[?]** _Packaging / repo_ — `pyproject.toml` with a `[project.scripts] hypertyper = "hypertyper:main"` entry (move the `__main__` block into `main()`), so `pipx install .` works on non-Arch systems. README's pip route is only "clone and run".
213. [ ] **[?]** _Packaging / repo_ — Add a GitHub Actions workflow that runs `python3 test_hypertyper.py` on 3.8, 3.11 and 3.13, plus a Windows job (the `msvcrt` path has no coverage at all).
214. [ ] **[?]** _Skip_ — CLI flags with `argparse`: `--mode food --time 60 --no-sound --version`. Lets the AUR package launch straight into a mode.
215. [ ] **[?]** _UX / UI_ — Live WPM in the HUD (`game_lines`, `:605`). The data (`good_chars`, `start`) is already in scope; show `WPM: 47` next to score and timer, since this is a typing game that never shows speed while playing.
216. [ ] **[?]** _UX / UI_ — Use the terminal's alternate screen (`\033[?1049h` / `\033[?1049l`) and hide the cursor in menus. Currently every frame is drawn on the main screen, so quitting leaves the last frame in the user's scrollback with the shell prompt under it. Restore in the existing `finally`/exit paths.
217. [ ] **[?]** _UX / UI_ — Resume from pause should give a short "3-2-1" before the clock restarts. Today resume (`:660`) puts the user straight back on a new keystroke clock with the same word and their partial input erased.
218. [ ] **[?]** _UX / UI_ — Visual progress for the timer: a 20-char bar (`█████░░░░░`) beside `TIME: 12.3s` that changes color in the last 5 s. Easier to read at a glance than a number you have to parse mid-word.

## Low value / nice to have

219. [ ] **[XS]** _Cleanup_ — `.gitignore` ignores `highscores.json` (a leftover from when it lived in the repo); add `history.jsonl` and `settings.json` too, in case anyone runs from the repo dir with `XDG_CONFIG_HOME` pointing there.
220. [ ] **[XS]** _Cleanup_ — `BACKUP_WORDS` is a fruit list; make it a generic set of 10 common words (and warn visibly) since it silently replaces a broken custom list (older item).
221. [ ] **[XS]** _Cleanup_ — `splash_screen` ASCII is built from two 5-line blocks; store the logo as a data file or a constant to keep functions short.
222. [ ] **[XS]** _Cleanup_ — `ANSI_RE` is declared between functions; move it to the top constants block.
223. [ ] **[XS]** _Cleanup_ — `Fore`/`Style` classes duplicate colorama's API; a `dict` of names or f-string constants would read better, but keep the names to minimize churn.
224. [ ] **[XS]** _Cleanup_ — `LENGTHS` ranges overlap at boundaries (short 0-5, medium 6-8); fine, add a comment that the minimum word length is 3 from `load_words`.
225. [ ] **[XS]** _Cleanup_ — Remove `msvcrt = None` pattern by splitting platform input into `_posix_input.py`/`_win_input.py` when the file is split.
226. [ ] **[XS]** _Cleanup_ — `import functools` for a single `lru_cache`; use `functools.cache` (3.9+) once 3.8 is dropped.
227. [ ] **[XS]** _Cleanup_ — `time.strftime("%Y-%m-%d %H:%M")` loses seconds and timezone; store ISO-8601 with offset for sorting/merging.
228. [ ] **[XS]** _Cleanup_ — `ACHIEVEMENTS` stores tuples with lambdas; a `namedtuple` would let you refer to `a.name` instead of `a[0]`.
229. [ ] **[XS]** _Cleanup_ — `import select`, `termios`, `tty`, `msvcrt` conditional imports at the top make the file read platform-first; move to `_platform.py` when splitting.
230. [ ] **[XS]** _Cleanup_ — `apply_theme()` and `GOOD, BAD` module globals could be replaced by a `Palette` object passed to `game_lines`, removing the `global` statements.
231. [ ] **[XS]** _Cleanup_ — Add a `__version__` and print it on the splash and in `--version`; PKGBUILD still says 1.0.2 while the code has a live timer, combos, stats and achievements.
232. [ ] **[S]** _Feature_ — Online leaderboard (opt-in) via a tiny signed-score endpoint; adds trust and abuse problems, so keep local-only unless wanted.
233. [ ] **[S]** _Feature_ — Share image/ASCII card of a run for social posts (`--share`), rendered to a text block the user can copy.
234. [ ] **[S]** _Feature_ — Discord/Slack webhook integration for friends' leaderboards (opt-in).
235. [ ] **[S]** _Feature_ — Practice reminders via a systemd user timer or notification ("you haven't practiced today").
236. [ ] **[S]** _Feature_ — Integrate with `notify-send` on personal bests.
237. [ ] **[S]** _Feature_ — Curses/textual rewrite for mouse support and resize events (SIGWINCH) instead of 10 Hz polling; only worth it if the UI grows.
238. [ ] **[S]** _Feature_ — Mobile-friendly Termux notes (keyboard quirks, `select` on Android).
239. [ ] **[S]** _Feature_ — Localized UI strings (`gettext`) starting with Spanish, matching the Spanish word mode.
240. [ ] **[S]** _Feature_ — Accessibility mode: no animations, no color-only signals, optional speech output of the word via `espeak` for low-vision users.
241. [ ] **[S]** _Feature_ — Keyboard layout awareness: detect Dvorak/Colemak (via `setxkbmap -query` or `localectl`) and show layout in history so records are comparable.
242. [ ] **[S]** _Feature_ — Plugin mechanism: modes defined in `~/.config/hypertyper/modes/*.py` returning an iterator of targets (e.g. random numbers, git log lines).
243. [ ] **[S]** _Feature_ — Typing test import: paste an arbitrary text file path and play it as a passage with progress through the file saved between sessions.
244. [ ] **[S]** _Feature_ — Book mode: type through a public-domain text sequentially (Project Gutenberg), resume where you left off, show chapter progress.
245. [ ] **[S]** _Feature_ — Code-from-repo mode: sample random lines from a git repo (`hypertyper --repo .`) for practicing on code you actually write.
246. [ ] **[S]** _Feature_ — Add a "daily 3" challenge: three fixed word sets per day with a streak counter, shown on the menu.
247. [ ] **[S]** _Feature_ — Share card: generate a compact ASCII summary of a run (mode, time, WPM, accuracy, combo) to paste into chat.
248. [ ] **[S]** _Feature_ — Lesson plans: curated sequences (home row → top row → bottom row → numbers → symbols) with pass thresholds, tracked in a small `progress.json`.
249. [ ] **[S]** _Feature_ — Quote mode with real attributions: show the author after each quote, and use public-domain sources (Project Gutenberg passages) for longer passage typing.
250. [ ] **[M]** _Feature_ — Web/WASM port or a minimal HTTP UI so it runs in a browser; out of scope unless sharing widely.
251. [ ] **[?]** _Bugs_ — `load_high_scores` builds a sanitized `new_data` but returns the raw `data` when nothing needed migrating (`:510`). A hand-edited entry like `"Streak": "abc"` then crashes `best.get(...)` at game over. Return `new_data` always.
252. [ ] **[?]** _Bugs_ — Countdown runs in cooked mode: `countdown()` (`:464`) never enters `cbreak_mode`, so keys pressed during "3-2-1" are echoed onto the centered screen before `flush_input()` discards them. Wrap the countdown in `cbreak_mode()`, and let any key skip it (see UX).
253. [ ] **[?]** _Bugs_ — Directory creation runs at import time (`os.makedirs(CONFIG_DIR)`, `:64`). With a read-only or missing `$HOME`, `import hypertyper` raises before any friendly handling, and tests must set `XDG_CONFIG_HOME` before importing. Create the directory lazily in `save_*`, inside the existing `IOError` handling.
254. [ ] **[?]** _Bugs_ — Custom list named like a built-in mode (`Streak.txt`) produces the same `score_key` as the built-in and shares its high score (`get_modes`, `:200`). Prefix custom modes (`custom: name`) or dedupe names.
255. [ ] **[?]** _Bugs_ — Stats mix incomparable runs. The trend, averages and "Best WPM" (`:587`) combine 15 s and 120 s runs, all modes, and practice runs, while achievements already exclude practice. Filter by practice flag by default and add a mode / timer filter.
256. [ ] **[?]** _Bugs_ — "Reset All High Scores" (`:831`) leaves `history.jsonl` untouched, so Stats and achievements still show the old runs and the Settings label doesn't say so. Offer a second confirmation for "also clear history", or rename the item.
257. [ ] **[?]** _Data / content_ — `data/code.txt` mixes languages and tiny snippets (`x = [1, 2, 3]`). Split into per-language files (`python`, `js`, `bash`, `c`) so Code Snippets mode can be filtered, and add multi-token lines with brackets and operators, which are the hard part of typing code.
258. [ ] **[?]** _Data / content_ — Mode difficulty differs wildly (Pokemon names, brainrot slang, linkedin phrases) but menu items look the same. Add a short one-line description or tag (`easy`, `symbols`, `phrases`) next to each mode in the picker.
259. [ ] **[?]** _Data / content_ — Cities has only 50 entries (US state capitals). In a 120 s run at 40+ WPM the bag runs out and repeats; extend it (world capitals) or let a mode declare a "finite" list that ends the run when exhausted.
260. [ ] **[?]** _Gameplay / features_ — Mid-run difficulty ramp option ("Endless"): the word length filter steps up every 10 correct words and the timer adds +1 s per word instead of a fixed clock. Gives a second, more forgiving play style without touching the existing scoring.
261. [ ] **[?]** _Gameplay / features_ — More achievements: 95% accuracy over 30 s, 10 runs in a day, 7-day streak, first run in every mode, a clean 30 words in a row. Three achievements is too few to feel like progress. Persist unlocked ones in `settings.json`/`achievements.json` so pruning the history file doesn't re-lock them.
262. [ ] **[?]** _Gameplay / features_ — Sudden death ends on the first wrong word even when the player only fat-fingered Enter early. Add a one-time "strike" allowance per run (setting: 0 / 1 / 3 strikes) between full sudden death and Practice mode.
263. [ ] **[?]** _Gameplay / features_ — Share line: a "copy result" key on the game-over screen that prints a one-line summary (`HyperTyper Streak 30s: 62 WPM 97% acc, score 340`) to stdout/clipboard (`wl-copy`/`xclip`/`pbcopy` if present).
264. [ ] **[?]** _Packaging / repo_ — Tests cover the pure helpers only. Add cases for `score_key` (time, difficulty, practice suffixes), `pick_words` (the `< 10` fallback), the `load_high_scores` migration path, and the corrupt-file recovery above; an end-to-end smoke test can drive `streak_mode` through piped stdin since `screen()` already has a non-tty branch.
265. [ ] **[?]** _Packaging / repo_ — README roadmap still lists "More game modes / More settings / More color themes". Replace with concrete items from this file so the list tells a reader what is actually planned, and refresh `hypertyper.gif` (it predates the live timer, auto-submit and new HUD).
266. [ ] **[?]** _Skip_ — Local multiplayer / hot-seat (on roadmap). Easiest form: two players alternate runs with the same seed, compare scores.
267. [ ] **[?]** _Skip_ — Daily challenge: seed `random` with the date so everyone gets the same words; separate daily record.
268. [ ] **[?]** _UX / UI_ — Allow any key to skip the 3-2-1 countdown on retry (`countdown`, `:464`), or a setting for countdown length (0 / 1 / 3). Three seconds plus the 0.5 s "GO!" on every retry slows the R-to-retry loop.
269. [ ] **[?]** _UX / UI_ — Show the target word's progress cursor: dim the remaining letters of the target under the typed text so you can see where you are in long entries (Quotes, Code). Currently the target is shown above and the colored copy below, so the eye has to compare two lines.
270. [ ] **[?]** _UX / UI_ — Menus have no `q` shortcut and any non-digit key is returned as a choice that is then ignored (`choose`, `:439`). Map `q` to Quit/Back, and ignore unrelated keys instead of redrawing.
271. [ ] **[?]** _UX / UI_ — Ctrl-W / Ctrl-U in the typing buffer to delete a word / the line (`screen`, `:419`). Only Backspace works now; for long Quotes entries a mistake at the start costs a lot of keystrokes.

## Done (earlier rounds, kept for reference)

- [x] **[H]** Type-ahead breaks the game: keys pressed during the countdown or the 0.2 s "OK!" flash stay in stdin and become the next `input()`, so the next word is "wrong" and the run ends instantly (`hypertyper.py:308`, `:505`). Fix: `termios.tcflush(sys.stdin, termios.TCIFLUSH)` right before each prompt (guard for Windows). (already fixed in `af9d406`)
- [x] **[H]** Wrong-word message is never seen: it prints at `:517`, then `break` goes straight to the Game Over screen, which calls `clear_screen()`. Show it inside the Game Over lines ("You typed X, expected Y"). (already fixed in `af9d406`)
- [x] **[H]** High scores ignore the timer length: 15 s and 120 s runs share one record per mode (`:543`). Key by `f"{mode}@{time_limit}s"`, or store a per-time table. (already fixed in `af9d406`)
- [x] **[H]** Live countdown timer that ticks every 100 ms while typing (needs the raw-mode loop above).
- [x] **[M]** Ctrl-D (EOF) is only caught on the word prompt (`:473`). On the initials prompt, menus after game over, splash, or pause it dumps a traceback, and `__main__` only catches `KeyboardInterrupt` (`:772`). Catch `EOFError` at top level too. (already fixed in `af9d406`)
- [x] **[M]** First run prints "Migrated high scores to new format..." for no reason: `__main__` writes the old format `{"Streak": 0}` (`:761`) and the loader migrates it. Write `{}` or the new format. (already fixed in `af9d406`)
- [x] **[M]** Timer is not live: `~Ns` is drawn once per word (`:458`), so it freezes while you type. A long word at 1 s left is still accepted or silently thrown away (`:477`). Pick a rule: reject late input with a message, or draw a live timer (see Features).
- [x] **[M]** Random word repeats back-to-back (`random.choice`, `:453`), and duplicates in the lists weight some words higher. Use a shuffled bag, then dedupe the data files.
- [x] **[M]** Spanish mode needs exact characters: accent-insensitive compare (`unicodedata` NFD, strip combining) or at least accept un-accented input. (Only 1 non-ASCII line today, so low risk, but any future list will hit this.)
- [x] **[M]** `clear_screen()` shells out via `os.system('clear')` every word (`:276`). Print `"\033[2J\033[H"` (colorama already handles Windows); removes a process spawn per word and the flicker.
- [x] **[M]** `pygame` import is slow and prints its "Hello from the pygame community" banner. Set `os.environ["PYGAME_HIDE_SUPPORT_PROMPT"]="1"` before import; use `pygame.mixer.init()` only. Lazy-import when sound is on.
- [x] **[M]** Auto-submit on correct final character (or Space) in non-exact modes, so Enter is not needed per word. Keep Enter for exact-match modes (code/terminal).
- [x] **[M]** Remove the fixed 0.2 s sleep after every correct word (`:505`). It eats time budget and slows pace. A brief inline "+N" flash on the same screen is enough.
- [x] **[M]** Main menu title says "CLI TYPING GAME" (`:732`); use the HyperTyper logo/name. Show current time limit and best score on the mode picker.
- [x] **[M]** Mode list is a 13-line `if/elif` chain duplicated in the menu text (`:601-650`). Drive both from one `MODES = [(name, file, exact)]` list so menu number, label, and launch never drift apart.
- [x] **[M]** Game Over: show accuracy, best combo, longest word, and compare to personal best ("+12 vs best"). Data is already tracked or trivial to add.
- [x] **[M]** User word lists: any `~/.config/hypertyper/words/*.txt` shows up as a mode automatically (name from file name). Pair with the MODES table above.
- [x] **[M]** "Practice" / forgiving mode: mistakes cost a combo reset instead of ending the run. Current sudden death is harsh for new players, especially in code mode.
- [x] **[M]** Stats history (`history.jsonl`): date, mode, time, WPM, accuracy, score; add a Stats screen with averages and a trend sparkline.
- [x] **[M]** Quotes/sentences mode (full lines, punctuation) for real-world typing practice.
- [x] **[M]** Delete `organize_sound_files()` (`:131-152`) and its call (`:767`). One-time dev migration that runs a relative `sounds` check every launch; sounds already live in `data/sounds`.
- [x] **[M]** Dedupe word lists: linkedin 327, spanish 394, words 314, lorem 151, terminal 48, animals 34 duplicate lines. `sort -u` them (keep file order if it matters, use `awk '!s[$0]++'`).
- [x] **[L]** Emoji in "🚨 NEW HIGH SCORE" is 2 columns wide but counted as 1, so that line sits 1 col off-center (`get_visible_length`, `:205`). Use `wcwidth` or drop the emoji. (already fixed in `af9d406`)
- [x] **[L]** Initials loop is a `while True` that always breaks on the first pass, with two copy-pasted save blocks (`:554-574`). Collapse to `name = (input or "UNK")[:3]`; save once.
- [x] **[L]** WPM uses full elapsed time including the pause after a wrong word and counts only correct chars, so it is not comparable with other tools (`:521-527`). Document the formula or show raw + net WPM. (already fixed in `af9d406`)
- [x] **[L]** `PKGBUILD` says `pkgver=1.0.1` but tag `v1.0.2` exists. Bump PKGBUILD and `.SRCINFO` together, and replace `sha256sums=('SKIP')` with a real sum before AUR push. (already fixed in `af9d406`)
- [x] **[L]** PKGBUILD maintainer is a placeholder `syreese@example.com`. Fix before publishing. (already fixed in `af9d406`)
- [x] **[L]** `load_words` re-reads and re-filters the file on every mode entry and each retry-loop is fine, but cache per file in a dict.
- [x] **[L]** `load_high_scores()` re-reads the JSON file multiple times per game over (`:543`, `:561`, `:570`). Load once, reuse.
- [x] **[L]** `get_visible_length` recompiles the ANSI regex on each call (`:207`). Compile once at module level.
- [x] **[L]** Remove the forced `time.sleep(1)` when pygame is missing (`:21`) and `time.sleep(2)` when a word file is missing (`:125`). Print once, never block startup.
- [x] **[L]** Menu choices need Enter; allow single keypress selection once raw input exists.
- [x] **[L]** Re-center on terminal resize and warn when the terminal is smaller than 60x15.
- [x] **[L]** Settings: allow custom timer value and sound volume (`Sound.set_volume`), not only the 15/30/60/120 cycle (`:685`).
- [x] **[L]** Colorblind-safe palette option (replace red/green-only signals with symbols too). Matches "Color themes" on the roadmap.
- [x] **[L]** Pause/quit key in game (Esc) instead of Ctrl-C only.
- [x] **[L]** Difficulty filter by word length (short/medium/long) for the word-based modes.
- [x] **[L]** Achievements (first God Mode, 50 WPM, 100 words in one run).
- [x] **[L]** Dead code: `pause()` (`:315`), `WORD_FILE` (`:52`), unused `Back` import (`:9`), commented-out sleep (`:189`), stale "Optional" migration comment (`:49`), long monologue comment in `pause()`.
- [x] **[L]** `data/settings.json` is a leftover; settings live in `~/.config/hypertyper/`. Remove from the repo if tracked (`git ls-files data/settings.json`).
- [x] **[L]** Docstrings still say "data/settings.json" (`:65`, `:87`). Update to `SETTINGS_FILE`.
- [x] **[L]** README: `pygame` is listed as required in `requirements.txt` but the game works without it; mark optional. Add LICENSE file (PKGBUILD says MIT, repo has none). Document the config path and that high scores are in `~/.config/hypertyper/`.
- [x] **[L]** No tests. One `test_hypertyper.py` for `get_combo_tier`, `load_words` filtering, and WPM math is enough.
- [x] **[L]** Consider dropping `colorama` on Linux/macOS (raw ANSI works) to cut a dependency; keep only if Windows support matters. Done: colors are plain ANSI codes now. `PKGBUILD`/`.SRCINFO` still list `python-colorama` and require `python-pygame`; make pygame an `optdepends` and drop colorama when you cut the next release (the v1.0.2 tarball still needs them).
