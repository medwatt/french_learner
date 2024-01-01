import os
from gtts import gTTS
import concurrent.futures

def text_to_speech(word, filename, lang):
    """Convert text to speech and save as an MP3 file."""
    tts = gTTS(word, lang=lang)
    tts.save(filename)

def get_new_words(filepath, output_folder, existing_files):
    new_words = []
    already_present = set()

    def update_lists (word, filename, lang):
        if filename in existing_files:
            already_present.add(filename)
        else:
            new_words.append((word, os.path.join(output_folder, filename), lang))

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            french_word, english_word = line.split(';')
            french_word = french_word.strip()
            english_word = english_word.strip()
            french_filename = french_word.replace("'", "").replace(" ", "_") + "_fr.mp3"
            english_filename = english_word.replace("'", "").replace(" ", "_") + "_en.mp3"

            update_lists(french_word, french_filename, "fr")
            update_lists(english_word, english_filename, "en")

    return new_words, already_present

def download_words(filepath, output_folder, existing_files):
    new_words, already_present = get_new_words(filepath, output_folder, existing_files)
    to_be_deleted = existing_files - already_present

    # Use multithreading to create sound files
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda p: text_to_speech(*p), new_words)

    # Delete all stale files
    for filename in to_be_deleted:
        os.remove(os.path.join(output_folder, filename))

def get_existing_sound_files(folder_path):
    """Get a list of existing sound files in a folder."""
    return set(os.listdir(folder_path))

def setup_folders(root_path, sound_path, selected_file_path):
    output_folder = os.path.join(sound_path, selected_file_path[0])
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def get_required_filepath(root_path):
    idx = 1
    paths = {}
    for file in sorted(os.listdir(root_path)):
        if file.endswith('.txt'):
            filepath = os.path.join(root_path, file)
            base_filename = os.path.splitext(file)[0]
            paths[idx] = (base_filename, filepath)
            idx += 1

    for k, v in paths.items():
        print(f"{k}. {v[0]}")

    while True:
        try:
            choice = int(input(">> Select a vocabulary set by number: "))
            if 0 <= choice < len(paths):
                return paths[choice]
            else:
                print("!! Invalid selection. Please enter a valid number.")
        except ValueError:
            print(">> Invalid input. Please enter a number.")

def main():
    root_path = '/home/medwatt/coding/python/french_learner/vocabulary/sets'
    sound_path = '/home/medwatt/coding/python/french_learner/vocabulary/sounds'
    selected_file_path = get_required_filepath(root_path)
    sound_path = setup_folders(root_path, sound_path, selected_file_path)
    existing_sound_files = get_existing_sound_files(sound_path)

    download_words(selected_file_path[1], sound_path, existing_sound_files)
    # word_pairs = get_word_pairs(selected_file_path[1])

    # print(word_pairs)
    # print(sound_path)

if __name__ == "__main__":
    main()
