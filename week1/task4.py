# Word Counter from Text File

def count_words_in_file(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
            words = content.split()
            word_count = len(words)
            return word_count
    
    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return -1
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return -1


if __name__ == "__main__":
    filename = input("Enter the filename to read: ")
    
    word_count = count_words_in_file(filename)
    
    if word_count != -1:
        print(f"\nFile: {filename}")
        print(f"Total number of words: {word_count}")
    else:
        print("Could not count words due to an error.")
