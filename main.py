import os
import enum
import yaml
import random
import time
import unicodedata
import subprocess

################################################################################
#                                    Audio                                     #
################################################################################
def read_word(filename):
    subprocess.call(["mpg123", "-q", f"{filename}"])

################################################################################
#                                     Menu                                     #
################################################################################
class GameMode(enum.Enum):
    REVIEW_VOCABULARY = enum.auto(), "Review Vocabulary"
    REVIEW_VOCABULARY_MISSED = enum.auto(), "Review Vocabulary (Missed)"
    GUESS_THE_WORD = enum.auto(), "Guess The Word"
    GUESS_THE_WORD_MISSED = enum.auto(), "Guess The Word (Missed)"
    GUESS_THE_GRAMMAR = enum.auto(), "Guess The Grammar"

    def __init__(self, _, display_name):
        self._display_name = display_name

    @property
    def display_name(self):
        return self._display_name

################################################################################
#                                   Loading                                    #
################################################################################
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def get_paths():
    paths = {}

    paths["root"] = os.path.dirname(os.path.abspath(__file__))
    paths["vocabulary"] = os.path.join(paths["root"], "vocabulary")
    paths["sets"] = os.path.join(paths["vocabulary"], "sets")
    paths["sounds"] = os.path.join(paths["vocabulary"], "sounds")
    paths["missed"] = os.path.join(paths["vocabulary"], "missed")
    paths["grammar"] = os.path.join(paths["vocabulary"], "grammar")

    os.makedirs(paths["missed"], exist_ok=True)

    return paths

################################################################################
#                            Select Vocabulary Set                             #
################################################################################
def choose_game_mode():
    print("")

    for mode in GameMode:
        print(f"{mode.value[0]}. {mode.display_name}")

    choice = int(input("\n>> Select a game by number: "))

    for mode in GameMode:
        if mode.value[0] == choice:
            return mode

def get_txt_files(path):
    file_paths = []
    file_names = []

    for entry in sorted(os.listdir(path)):
        file_path = os.path.join(path, entry)

        if os.path.isfile(file_path) and file_path.endswith('.txt'):
            absolute_path = os.path.abspath(file_path)
            base_name = os.path.basename(file_path)
            modified_base_name = ' '.join(word.capitalize() for word in base_name.replace('_', ' ').split('.txt')[0].split())
            file_paths.append(absolute_path)
            file_names.append(modified_base_name)
    return file_paths, file_names

def choose_vocab_set(selected_mode, paths):

    if selected_mode == GameMode.GUESS_THE_WORD_MISSED or selected_mode == GameMode.REVIEW_VOCABULARY_MISSED:
        path = paths["missed"]
    elif selected_mode == GameMode.GUESS_THE_WORD_MISSED:
        path = paths["grammar"]
    else:
        path = paths["sets"]

    file_paths, file_names = get_txt_files(path)

    print("")
    for idx, title in enumerate(file_names, start=1):
        print(f"{idx}. {title}")

    while True:
        try:
            choice = int(input("\n>> Select a vocabulary set by number: ")) - 1
            if 0 <= choice < len(file_paths):
                selected_file = file_paths[choice]
                sound_path = os.path.join(paths["sounds"], os.path.basename(selected_file).split('.txt')[0])
                return (selected_file, sound_path)
            else:
                print("!! Invalid selection. Please enter a valid number.")
        except ValueError:
            print(">> Invalid input. Please enter a number.")

################################################################################
#                         Extract Vocabulary From File                         #
################################################################################
def load_vocabulary(path):
    with open(path, 'r') as file:
        return [line.strip().split(';') for line in file]

################################################################################
#                               Handle Spelling                                #
################################################################################
def levenshtein_distance(word1, word2):
    if len(word1) < len(word2):
        return levenshtein_distance(word2, word1)

    if len(word2) == 0:
        return len(word1)

    previous_row = range(len(word2) + 1)
    for i, c1 in enumerate(word1):
        current_row = [i + 1]
        for j, c2 in enumerate(word2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def word_similarity(word1, word2):
    distance = levenshtein_distance(word1.lower(), word2.lower())
    length = max(len(word1), len(word2))
    similarity = 1 - distance / length
    return similarity

def normalize_word(word, ignore_accents):
    if ignore_accents:
        return ''.join(c for c in unicodedata.normalize('NFD', word) if unicodedata.category(c) != 'Mn')
    return word

def remove_article(word):
    articles = ["le ", "la ", "l'", "les ", "un ", "une "]
    for article in articles:
        if word.startswith(article):
            return word[len(article):]
    return word

################################################################################
#                       SubMenu 1. Review Vocabulary Set                       #
################################################################################
def review_vocab_set(txt_path, sound_path):
    try:
        repeat_word = int(input(">> How many times do you want to repeat every word [default: 1]: ") or 1)
        if repeat_word > 1:
            print("Press Ctrl+C to pause")
    except ValueError:
        repeat_word = 1

    def read_word_aloud(word, lang):
        path = os.path.join(sound_path, word.replace(" ", "_").replace("'", ""))
        read_word(f"{path}_{lang}.mp3")

    def pause_if_needed():
        try:
            print("...")
            time.sleep(1.5)
            print("<<<")
        except KeyboardInterrupt:
            input("Paused. Press Enter to continue...")


    vocabulary = load_vocabulary(txt_path)
    random.shuffle(vocabulary)

    print("")
    for i, word_pair in enumerate(vocabulary):
        french, english = word_pair
        print(f"{i+1}/{len(vocabulary)}. {english} -> {french}")

        for _ in range(repeat_word):
            read_word_aloud(english, "en")
            time.sleep(0.5)
            read_word_aloud(french, "fr")
            pause_if_needed()

    print("Review session completed.")

################################################################################
#                   SubMenu 2. Guess Word (English, French)                    #
################################################################################
def check_answer(answer, user_input, config):

    for word in [ans.strip() for ans in answer.split(',')]:

        if user_input.lower() == word:
            return True

        if config['guess_french_word']:
            normalized_answer = word
            if config['ignore_accents']:
                normalized_answer = remove_article(word)
            if config['ignore_article']:
                normalized_answer = normalize_word(normalized_answer, config['ignore_accents'])

        if user_input.lower() == normalized_answer.lower():
            return True

        if config["liberal_spelling"] and word_similarity(normalized_answer.lower(), user_input.lower()) > 0.7:
            return True

    return False

def guess_the_word(txt_path, sound_path, message, config, paths):
    seen_words = set()
    wrong_words_history = {}
    wrong_words = []
    correct_count = missed_count = 0
    last_word = None
    repeat_wrong_probability = config['repeat_wrong_probability']
    finish_missed_words = False
    question_status = ""

    vocabulary = load_vocabulary(txt_path)

    try:
        while True:

            if (random.random() < repeat_wrong_probability and len(wrong_words) > 1) or finish_missed_words:
                word_pair = tuple(random.choice([word for word in wrong_words if word != last_word]))
                question_status = "missed"

            elif random.random() < config['repeat_seen_probability'] and len(seen_words) > 3:
                word_pair = tuple(random.choice([word for word in seen_words if word != last_word]))
                question_status = "repeating"

            else:
                word_pair = tuple(random.choice([word for word in vocabulary if tuple(word) not in seen_words and word != last_word]))
                seen_words.add(word_pair)
                question_status = f"{len(seen_words)}/{len(vocabulary)}"

            question, answer = (word_pair[1], word_pair[0]) if config['guess_french_word'] else (word_pair[0], word_pair[1])

            user_input = input(f"\n({question_status}): {message} '{question}': ").strip()
            last_word = word_pair
            if user_input == "-1":
                break

            if check_answer(answer, user_input, config):
                if user_input.lower() != answer and (config['ignore_accents'] or config['ignore_article']):
                    print("Correct!: ", answer)
                else:
                    print("Correct!")
                correct_count += 1
                if word_pair in wrong_words_history:
                    wrong_words_history[word_pair][0] -= 1
                    if wrong_words_history[word_pair][0] < 1:
                        wrong_words.remove(word_pair)
            else:
                print(f"Wrong! The correct answer is '{answer}'.")
                missed_count += 1
                if word_pair in wrong_words_history:
                    wrong_words_history[word_pair][0] += 1
                    wrong_words_history[word_pair][1] += 1
                else:
                    wrong_words_history[word_pair] = [int(config['correct_guesses_to_remove']), 1]
                    wrong_words.append(word_pair)

            if config["say_word"]:
                path = os.path.join(sound_path, answer.replace(" ", "_").replace("'", ""))
                read_word(f"{path}_fr.mp3")

            if len(seen_words) == len(vocabulary):
                if len(wrong_words) > 1:
                    finish_missed_words = True
                else:
                    break

    except KeyboardInterrupt:
        pass

    display_game_over_stats(correct_count, missed_count, wrong_words_history)

    if input("\nDo you want to save the missed words to a file? (y/n): ").lower() == 'y':
        save_missed_words(wrong_words_history, txt_path, paths)

################################################################################
#                                    Stats                                     #
################################################################################
def display_game_over_stats(correct_count, missed_count, wrong_words):
    percent = correct_count / (correct_count + missed_count) * 100

    print("")
    print("####################################################################")
    print("#                            GAME OVER                             #")
    print("####################################################################")
    print(f"Correct: {correct_count}, Missed: {missed_count}, Percentage: {percent}")
    print("--------------------------------------------------------------------")
    for word_pair, stat in wrong_words.items():
        print(f"{word_pair[0]} -> {word_pair[1]} : {stat[1]}#")

def save_missed_words(wrong_words, txt_path, paths):
    missed_words_path = paths["missed"]
    file_name = os.path.basename(txt_path).split('.txt')[0]
    path = os.path.join(missed_words_path, f"{file_name}.txt")

    with open(path, 'w') as file:
        for (question, answer), _ in wrong_words.items():
            file.write(f"{question};{answer}\n")

    print(f"Missed words saved to {path}")

################################################################################
#                                     Main                                     #
################################################################################
def main():

    print("Welcome to the French Vocabulary Game. Type '-1' at any time to quit.")

    config = load_config()
    paths = get_paths()

    selected_game_mode = choose_game_mode()
    selected_set_txt, selected_set_sounds = choose_vocab_set(selected_game_mode, paths)

    if selected_game_mode == GameMode.REVIEW_VOCABULARY or selected_game_mode == GameMode.REVIEW_VOCABULARY_MISSED:
        review_vocab_set(selected_set_txt, selected_set_sounds)

    elif selected_game_mode == GameMode.GUESS_THE_GRAMMAR:
        say_word_backup = config["say_word"]
        config["say_word"] = False
        message = "What is the correct tense of"
        guess_the_word(selected_set_txt, selected_set_sounds, message, config, paths)
        config["say_word"] = say_word_backup

    else:
        message = "Translate"
        guess_the_word(selected_set_txt, selected_set_sounds, message, config, paths)


if __name__ == "__main__":
    main()
