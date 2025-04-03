import string
from collections import Counter
import textwrap
import math
import random

ENGLISH_FREQ_ORDER = "etaoinshrdlucmfwygpbvkxqjz"
COMMON_WORDS = ["the", "and", "you", "that", "was", "for", "are", "with", "his", "they", "this", "have"]


# --------------------------
# Quadgram Scorer
# --------------------------
class QuadgramScorer:
    def __init__(self, quadgram_file):
        self.quadgrams = {}
        self.total = 0
        self.load_quadgrams(quadgram_file)
        self.floor = math.log10(0.01 / self.total)

    def load_quadgrams(self, path):
        with open(path, 'r') as f:
            for line in f:
                key, count = line.strip().split()
                self.quadgrams[key] = int(count)
                self.total += int(count)

        # Precompute log probabilities
        self.quadgrams = {k: math.log10(v / self.total) for k, v in self.quadgrams.items()}

    def score(self, text):
        text = ''.join([c for c in text.upper() if c in string.ascii_uppercase])
        score = 0
        for i in range(len(text) - 3):
            quad = text[i:i + 4]
            score += self.quadgrams.get(quad, self.floor)
        return score


# --------------------------
# File & Text Utilities
# --------------------------
def load_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().lower()


def get_letter_frequencies(text):
    only_letters = [c for c in text if c in string.ascii_lowercase]
    return Counter(only_letters)


def create_initial_mapping(cipher_freq, target_freq):
    mapping = {}
    sorted_cipher = [pair[0] for pair in cipher_freq.most_common()]
    for cipher_char, english_char in zip(sorted_cipher, target_freq):
        mapping[cipher_char] = english_char
    return mapping


def apply_mapping(text, mapping):
    result = []
    for char in text:
        if char in mapping:
            result.append(mapping[char])
        elif char in string.ascii_uppercase:
            result.append(mapping.get(char.lower(), '?').upper())
        else:
            result.append(char)
    return ''.join(result)


def print_mapping(mapping):
    print("\nCurrent Mapping:")
    for c in string.ascii_lowercase:
        print(f"{c} -> {mapping.get(c, '.')} ", end='  ')
    print("\n")


def xor_bytes(b1, b2):
    """Return the XOR of two byte sequences (shorter one determines length)."""
    return bytes(a ^ b for a, b in zip(b1, b2))


def find_matching_segments(xor_data, min_length=4):
    """Find all continuous zero-byte sequences of at least min_length."""
    matches = []
    current_start = None

    for i, byte in enumerate(xor_data):
        if byte == 0:
            if current_start is None:
                current_start = i
        else:
            if current_start is not None:
                length = i - current_start
                if length >= min_length:
                    matches.append((current_start, length))
                current_start = None

    if current_start is not None:
        length = len(xor_data) - current_start
        if length >= min_length:
            matches.append((current_start, length))

    return matches


def translate_text(text, mapping):
    """Translate a string using a monoalphabetic mapping (preserving case)."""
    result = ""
    for char in text:
        upper_char = char.upper()
        if upper_char in mapping:
            if char.isupper():
                result += mapping[upper_char]
            else:
                result += mapping[upper_char].lower()
        else:
            result += char
    return result


# --------------------------
# Auto Refinement Using Quadgram Scoring
# --------------------------
def auto_refine_mapping(text, initial_mapping, scorer, max_iterations=2000):
    best_mapping = initial_mapping.copy()
    best_decryption = apply_mapping(text, best_mapping)
    best_score = scorer.score(best_decryption)

    for _ in range(max_iterations):
        trial_mapping = best_mapping.copy()

        # Swap two letters in the mapped values
        a, b = random.sample(string.ascii_lowercase, 2)
        for k, v in trial_mapping.items():
            if v == a:
                trial_mapping[k] = b
            elif v == b:
                trial_mapping[k] = a

        trial_decryption = apply_mapping(text, trial_mapping)
        trial_score = scorer.score(trial_decryption)

        if trial_score > best_score:
            best_score = trial_score
            best_mapping = trial_mapping
            print(f"[+] Improved score: {best_score:.2f}")

    return best_mapping


# --------------------------
# Password Extraction Logic
# --------------------------
def find_and_decrypt_password_candidates(source1_path, source2_path, source3_path, mapping, scorer, min_length=4):
    """Find and decrypt reused OTP password segments in Source-2 and return the most plausible one."""
    with open(source1_path, 'rb') as f1, open(source2_path, 'rb') as f2, open(source3_path, 'rb') as f3:
        source1 = f1.read()
        source2 = f2.read()
        source3 = f3.read()

    xor_result = xor_bytes(source1, source3)
    matches = find_matching_segments(xor_result, min_length)

    if not matches:
        print("[!] No password-like segments found.")
        return

    print(f"\n[+] Found {len(matches)} matching segments (length ≥ {min_length})")

    best_score = float('-inf')
    best_segment = None

    for idx, (pos, length) in enumerate(matches, 1):
        if pos + length > len(source2):
            print(f"[!] Skipping segment {idx}: exceeds Source-2 length")
            continue

        encrypted_chunk = source2[pos:pos + length]
        try:
            encrypted_str = encrypted_chunk.decode('ascii', errors='replace')
        except UnicodeDecodeError:
            continue

        decrypted_str = translate_text(encrypted_str, mapping)
        score = scorer.score(decrypted_str) / max(1, len(decrypted_str))  # normalize by length

        print(f"[{idx}] Offset {pos}, Length {length} → Score: {score:.4f} → {decrypted_str}")

        if score > best_score:
            best_score = score
            best_segment = (pos, length, decrypted_str)

    if best_segment:
        pos, length, best_decryption = best_segment
        print("\n[✅] Best candidate:")
        print(f"Offset: {pos}, Length: {length}, Score: {best_score:.2f}")
        print(f"Decrypted Password: {best_decryption}")
    else:
        print("[!] No valid decrypted segments found.")


# --------------------------
# Main Entry Point
# --------------------------
def main():
    encrypted_text = load_file('Source-2-encrypted.txt')

    print("\n[1] Analyzing frequency...")
    frequencies = get_letter_frequencies(encrypted_text)

    print("\n[2] Creating initial mapping...")
    mapping = create_initial_mapping(frequencies, ENGLISH_FREQ_ORDER)

    print("\n[3] Loading quadgram model...")
    scorer = QuadgramScorer('english_quadgrams.txt')

    print("\n[4] Refining mapping using quadgram scoring...")
    mapping = auto_refine_mapping(encrypted_text, mapping, scorer)

    print("\n[5] Applying final mapping...\n")
    decrypted = apply_mapping(encrypted_text, mapping)
    for chunk in textwrap.wrap(decrypted[:2000], width=100):
        print(chunk)

    save = input("\nSave this draft to file? (y/n): ").strip().lower()
    if save == 'y':
        with open("decrypted_draft.txt", "w", encoding="utf-8") as f:
            f.write(decrypted)
        print("Saved to 'decrypted_draft.txt'")

    run_password_finder = input("Check for reused OTP password? (y/n): ").strip().lower()
    if run_password_finder == 'y':
        find_and_decrypt_password_candidates(
            "Source-1-encrypted.txt",
            "decrypted_draft.txt",
            "Source-3-encrypted.txt",
            mapping,
            scorer,
            min_length=8
        )


if __name__ == "__main__":
    main()
