import os
import yaml
import random
import datetime
import unicodedata
import subprocess

def create_directory_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    # os.makedirs(new_directory, exist_ok=True)

def set_paths(vocab_set_filename):
    paths = {}

    paths["root"] = os.path.dirname(os.path.abspath(__file__))
    paths["vocabulary"] = os.path.join(paths["root"], "vocabulary")
    paths["sound"] = os.path.join(paths["root"], "vocabulary", "sounds")

    paths["missed_words"] = os.path.join(paths["root"], "missed_words")
    os.makedirs(paths["missed_words"], exist_ok=True)
    # create_directory_if_not_exists(paths["missed_words"])

    paths["vocab_set"] = os.path.join(paths["root"], "vocabulary", vocab_set_filename)
    paths["vocab_set_name"] = os.path.splitext(vocab_set_filename)[0]

    return paths

def read_word(filename):
    subprocess.call(["mpg123", "-q", f"{filename}"])

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def select_vocabulary_set(sets):
    for i, set_ in enumerate(sets):
        print(f"{i+1}. {set_['title']}")
    choice = int(input("Select a vocabulary set by number: ")) - 1
    return sets[choice]['filename']

def load_vocabulary(path):
    with open(path, 'r') as file:
        return [line.strip().split(';') for line in file]

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

def display_game_over_stats(correct_count, missed_count, wrong_words):
    print(f"\nGame Over. Correct: {correct_count}, Missed: {missed_count}")
    print("Words missed:")
    for word_pair, stat in wrong_words.items():
        print(f"{word_pair[0]} -> {word_pair[1]} : {stat[1]}#")

def save_missed_words(wrong_words, original_path):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = paths["missed_words"]
    filename = paths["vocab_set_name"]
    new_path = os.path.join(basename, f"{filename}_{timestamp}.txt")

    with open(new_path, 'w') as file:
        for question, answer in wrong_words.items():
            file.write(f"{question};{answer}\n")

    print(f"Missed words saved to {new_path}")

def review_set(vocabulary, config, vocab_path):
    print(vocabulary)
    for word_pair in vocabulary:
        print("----------------->")
        french, english = word_pair
        path_fr = os.path.join(vocab_path[:-4], french.replace("'", "").replace(" ", "_"))
        path_en = os.path.join(vocab_path[:-4], english.replace("'", "").replace(" ", "_"))
        print(f"{path_fr}_fr.mp3")
        read_word(f"{path_fr}_fr.mp3")
        print(f"{path_en}_en.mp3")
        read_word(f"{path_en}_en.mp3")

def play_game(vocabulary, config, paths):
    seen_words = set()
    wrong_words = {}
    correct_count = missed_count = 0
    last_word = None
    repeat_wrong_probability = config['repeat_wrong_probability']

    try:
        while True:

            if random.random() < repeat_wrong_probability and len(wrong_words) > 1:
                word_pair = tuple(random.choice([word for word, stat in wrong_words.items() if stat[0] > 0 and word != last_word]))
            elif (random.random() < config['repeat_seen_probability'] and len(seen_words) > 3) or len(seen_words) == len(vocabulary):
                print("repeating")
                word_pair = tuple(random.choice([word for word in seen_words if word != last_word]))
            else:
                word_pair = tuple(random.choice([word for word in vocabulary if tuple(word) not in seen_words and word != last_word]))
                seen_words.add(word_pair)

            question, answer = (word_pair[1], word_pair[0]) if config['guess_french_word'] else (word_pair[0], word_pair[1])

            user_input = input(f"\nTranslate '{question}': ").strip()
            last_word = word_pair
            if user_input == "-1":
                break

            if config['guess_french_word']:
                normalized_answer = answer
                if config['ignore_accents']:
                    normalized_answer = remove_article(answer)
                if config['ignore_article']:
                    normalized_answer = normalize_word(normalized_answer, config['ignore_accents'])

            if user_input.lower() == answer or user_input.lower() == normalized_answer.lower():
                if user_input.lower() != answer and (config['ignore_accents'] or config['ignore_article']):
                    print("Correct!: ", answer)
                else:
                    print("Correct!")
                correct_count += 1
                if word_pair in wrong_words:
                    wrong_words[word_pair][0] -= 1
            else:
                print(f"Wrong! The correct translation is '{answer}'.")
                missed_count += 1
                if word_pair in wrong_words:
                    wrong_words[word_pair][0] += 1
                    wrong_words[word_pair][1] += 1
                else:
                    wrong_words[word_pair] = [int(config['correct_guesses_to_remove']), 1]

            if len(seen_words) == len(vocabulary):
                repeat_wrong_probability = 0.5

            if config["say_word"]:
                path = os.path.join(paths["sound"], paths["vocab_set_name"], answer.replace(" ", "_").replace("'", ""))
                read_word(f"{path}_fr.mp3")

    except KeyboardInterrupt:
        pass

    display_game_over_stats(correct_count, missed_count, wrong_words)

    if input("\nDo you want to save the missed words to a file? (y/n): ").lower() == 'y':
        save_missed_words(wrong_words, paths["missed_words"])

if __name__ == "__main__":
    print("Welcome to the French Vocabulary Game. Type '-1' at any time to quit.")
    config = load_config()
    vocab_set_filename = select_vocabulary_set(config['vocabulary_sets'])
    paths = set_paths(vocab_set_filename)
    vocabulary = load_vocabulary(paths["vocab_set"])
    play_game(vocabulary, config, paths)
    # review_set(vocabulary, config, vocab_path)
