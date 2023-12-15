import os
from gtts import gTTS
import concurrent.futures

def text_to_speech(word, filename, lang):
    """Convert text to speech and save as an MP3 file."""
    tts = gTTS(word, lang=lang)
    tts.save(filename)

def get_word_pairs(file_path):
    """Extract French and English words from a .txt file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [(line.split(';')[0].strip(), line.split(';')[1].strip()) for line in f]

def get_existing_sound_files(folder_path):
    """Get a list of existing sound files in a folder."""
    return set(os.listdir(folder_path))

def process_file(file_path, output_folder, existing_files):
    """Process a single .txt file."""
    word_pairs = get_word_pairs(file_path)
    tasks = []

    for french_word, english_word in word_pairs:
        french_file_name = french_word.replace("'", "").replace(" ", "_") + "_fr.mp3"
        english_file_name = english_word.replace("'", "").replace(" ", "_") + "_en.mp3"

        if french_file_name not in existing_files:
            tasks.append((french_word, os.path.join(output_folder, french_file_name), 'fr'))

        if english_file_name not in existing_files:
            tasks.append((english_word, os.path.join(output_folder, english_file_name), 'en'))

    # Use multithreading to create sound files
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda p: text_to_speech(*p), tasks)

    # Delete sound files without corresponding words
    normalized_files = {f.replace("_fr.mp3", "").replace("_en.mp3", "").replace("'", "").replace(" ", "_") for f, e in word_pairs}
    for file in existing_files:
        normalized_file = file.replace("_fr.mp3", "").replace("_en.mp3", "")
        if normalized_file not in normalized_files:
            os.remove(os.path.join(output_folder, file))

def process_files(folder_path):
    """Process all .txt files in the given folder."""
    for file in os.listdir(folder_path):
        if file.endswith('.txt'):
            file_path = os.path.join(folder_path, file)
            base_filename = os.path.splitext(file)[0]
            output_folder = os.path.join(folder_path, "sounds", base_filename)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            existing_files = get_existing_sound_files(output_folder)
            process_file(file_path, output_folder, existing_files)

def main():
    folder_path = '/home/medwatt/coding/python/french_learner/vocabulary/'
    process_files(folder_path)

if __name__ == "__main__":
    main()
