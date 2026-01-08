
import os
import random
import sys
import time
import json
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

# --- Configuration & Data ---

HIGHSCORE_FILE = "highscores.json"
WORD_FILE = "words.txt"
BACKUP_WORDS = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "lemon", "lime", "mango"]

# --- Helper Functions ---

def load_words(filename):
    """Loads words from data/filename, filtering invalid ones. Falls back to BACKUP_WORDS if needed."""
    words = []
    # Look for filename inside the 'data' folder
    file_path = os.path.join("data", filename)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    w = line.strip().lower()
                    if len(w) >= 3 and w.isalpha():
                        words.append(w)
        except IOError:
            pass # Keep list empty to trigger backup

    if not words:
        print(f"Warning: {file_path} not found or empty, using backup list.")
        time.sleep(2) # Give user a chance to see the warning
        return BACKUP_WORDS
    
    return words



def clear_screen():
    """Clears the terminal screen."""
    # os.name is 'nt' for Windows, 'posix' for Linux/Mac
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def countdown():
    """Runs a 3-2-1-GO countdown."""
    for i in [3, 2, 1]:
        clear_screen()
        print(f"\n\n\n\t\t{Fore.CYAN}{Style.BRIGHT}{i}")
        time.sleep(1)
    
    clear_screen()
    print(f"\n\n\n\t\t{Fore.GREEN}{Style.BRIGHT}GO!")
    time.sleep(0.5)

def pause():
    """Waits for user input to continue."""
    input("\nPress Enter to continue...")

def load_high_scores():
    """Loads high scores from JSON, returning a dict."""
    if not os.path.exists(HIGHSCORE_FILE):
        return {"Streak": 0}
    
    try:
        with open(HIGHSCORE_FILE, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"Streak": 0}
            return data
    except (json.JSONDecodeError, IOError):
        return {"Streak": 0}

def save_high_scores(scores):
    """Saves the high score dict to JSON."""
    try:
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=4)
    except IOError:
        print("\nWarning: Could not save high scores.")

def update_high_score(mode_name, score):
    """Updates the high score for a given mode if the new score is higher."""
    scores = load_high_scores()
    current_best = scores.get(mode_name, 0)
    
    if score > current_best:
        scores[mode_name] = score
        save_high_scores(scores)
        print(f"\n{Fore.GREEN}{Style.BRIGHT}NEW HIGH SCORE for {mode_name}: {score}!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}High Score for {mode_name}: {current_best}{Style.RESET_ALL}")

def show_high_scores():
    """Displays all high scores."""
    clear_screen()
    print(f"{Fore.CYAN}{Style.BRIGHT}--- HIGH SCORES ---{Style.RESET_ALL}")
    scores = load_high_scores()
    
    if not scores:
        print("No scores recording yet.")
    else:
        for mode, score in scores.items():
            print(f"{mode}: {Fore.YELLOW}{score}{Style.RESET_ALL}")
    
    print("-" * 20)
    print()
    pause()

# --- Game Modes ---

def streak_mode(mode_name, word_filename):
    """Runs the Streak Mode game loop with a 30s global timer and game feel."""
    
    # Load words for this mode
    current_words = load_words(word_filename)
    
    while True:
        # Countdown
        countdown()
        
        score = 0
        total_chars_typed = 0
        correct_words = 0
        start_time = time.time()
        time_limit = 30.0
        
        while True:
            # 1. Check time BEFORE showing word
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                break # Go to Game Over logic

            remaining = max(0, int(time_limit - elapsed))
            
            clear_screen()
            print(f"{Fore.CYAN}--- {mode_name.upper()} MODE ---{Style.RESET_ALL}")
            print(f"CURRENT SCORE: {Fore.YELLOW}{score}{Style.RESET_ALL}   |   TIME LEFT: {Fore.YELLOW}~{remaining}s{Style.RESET_ALL}")
            print("-" * 40)
            print()
            
            target_word = random.choice(current_words)
            print(f"Word:  {Style.BRIGHT}{Fore.WHITE}{target_word}{Style.RESET_ALL}")
            print()
            
            try:
                user_input = input("Type it: ").strip()
            except (EOFError, KeyboardInterrupt):
                return

            # 2. Check time AFTER input
            elapsed = time.time() - start_time
            if elapsed >= time_limit:
                break # Go to Game Over logic

            # 3. Sudden Death Check
            if user_input == target_word:
                word_len = len(target_word)
                score += word_len
                total_chars_typed += word_len
                correct_words += 1
                # Green flash logic: Just print a quick success line before clearing
                print(f"{Fore.GREEN}        {target_word} OK!{Style.RESET_ALL}")
                time.sleep(0.2)
            else:
                print()
                print(f"{Fore.RED}Wrong! You typed '{user_input}', expected '{target_word}'.{Style.RESET_ALL}")
                break # Go to Game Over logic

        # --- GAME OVER SCREEN ---
        final_elapsed = time.time() - start_time
        
        if final_elapsed < 1.0: 
            final_elapsed = 1.0 # Avoid div by zero
        
        minutes = final_elapsed / 60.0
        wpm = (total_chars_typed / 5.0) / minutes if minutes > 0 else 0
        
        print(f"\n{Fore.RED}{Style.BRIGHT}GAME OVER{Style.RESET_ALL}")
        print(f"Final Score: {Fore.YELLOW}{score}{Style.RESET_ALL}")
        
        # Show Stats
        print("-" * 30)
        print(f"Total Words Typed: {correct_words}")
        print(f"WPM: {Fore.CYAN}{wpm:.1f}{Style.RESET_ALL}")
        print("-" * 30)
        
        update_high_score(mode_name, score) # Pass dynamic mode name
        print()
        
        print(f"[{Fore.CYAN}Press ENTER for Menu{Style.RESET_ALL}] or [{Fore.CYAN}Press 'R' to Retry{Style.RESET_ALL}]")
        cmd = input().strip().lower()
        if cmd == 'r':
            continue # Restart loop
        else:
            break # Return to menu

def play_menu():
    """Submenu for selecting a game mode."""
    while True:
        clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}--- SELECT CATEGORY ---{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1. Standard Streak{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. Capital Cities{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3. Foods{Style.RESET_ALL}")
        print(f"{Fore.CYAN}4. Animals{Style.RESET_ALL}")
        print(f"{Fore.CYAN}5. Lorem Ipsum{Style.RESET_ALL}")
        print(f"{Fore.CYAN}6. Back to Main Menu{Style.RESET_ALL}")
        print()
        
        try:
            choice = input("Select an option (1-6): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            streak_mode("Streak", "words.txt")
        elif choice == '2':
            streak_mode("Capitals", "capitals.txt")
        elif choice == '3':
            streak_mode("Foods", "foods.txt")
        elif choice == '4':
            streak_mode("Animals", "animals.txt")
        elif choice == '5':
            streak_mode("Lorem", "lorem.txt")
        elif choice == '6':
            break
        else:
            pass

def show_placeholder(feature_name):
    """Displays a 'Coming Soon' message."""
    clear_screen()
    print(f"--- {feature_name} ---")
    print("\nComing Soon!\n")
    pause()

# --- Main Menu ---

def main_menu():
    """Runs the main menu loop."""
    while True:
        clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}=== CLI TYPING GAME ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}1. Play Game{Style.RESET_ALL}")
        print(f"{Fore.CYAN}2. High Scores{Style.RESET_ALL}")
        print(f"{Fore.CYAN}3. Settings{Style.RESET_ALL}")
        print(f"{Fore.CYAN}4. Quit{Style.RESET_ALL}")
        print()
        
        try:
            choice = input("Select an option (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == '1':
            play_menu()
        elif choice == '2':
            show_high_scores()
        elif choice == '3':
            show_placeholder("Settings")
        elif choice == '4':
            print("\nThanks for playing! Goodbye.")
            break
        else:
            # Invalid input, just loop again (or could print error)
            pass

if __name__ == "__main__":
    # Ensure highscore file exists
    if not os.path.exists(HIGHSCORE_FILE):
        save_high_scores({"Streak": 0})
    


    # Clear screen immediately on launch
    clear_screen()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nGame Interrupted. Bye!")
        sys.exit(0)
