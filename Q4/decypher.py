import string
from collections import Counter
import textwrap
import math
import random
import time
import re

ENGLISH_FREQ_ORDER = "etaoinshrdlucmfwygpbvkxqjz"
COMMON_WORDS = ["the", "and", "you", "that", "was", "for", "are", "with", "his", "they", "this", "have", 
                "not", "but", "what", "all", "when", "there", "can", "more", "your", "from", "will"]


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
        # Only convert to uppercase once
        text = ''.join([c for c in text.upper() if c in string.ascii_uppercase])
        score = 0
        
        # Avoid repeatedly slicing the string in the loop
        text_len = len(text)
        for i in range(text_len - 3):
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


def count_common_words(text):
    """Count occurrences of common English words in text"""
    text = text.lower()
    word_count = 0
    for word in COMMON_WORDS:
        # Use word boundary to match whole words only
        pattern = r'\b' + re.escape(word) + r'\b'
        word_count += len(re.findall(pattern, text))
    return word_count


# --------------------------
# Auto Refinement Using Quadgram Scoring with Simulated Annealing
# --------------------------
def auto_refine_mapping(text, initial_mapping, scorer, max_iterations=2000, sample_size=8000, early_stop=150, 
                        initial_temp=10.0, cooling_rate=0.99):
    """
    Refine the mapping using simulated annealing with quadgram scoring
    
    Args:
        text: The encrypted text
        initial_mapping: Starting letter mapping
        scorer: The quadgram scorer object
        max_iterations: Maximum number of iterations
        sample_size: Number of characters to use for scoring
        early_stop: Stop after this many iterations without improvement
        initial_temp: Starting temperature for simulated annealing
        cooling_rate: Rate at which temperature decreases
    """
    print(f"[*] Starting refinement with {max_iterations} max iterations, {sample_size} sample size")
    print(f"[*] Using simulated annealing (temp: {initial_temp}, cooling: {cooling_rate})")
    
    # Use several different samples from the text for better coverage
    samples = []
    text_len = len(text)
    if text_len > sample_size * 3:
        # Take samples from beginning, middle and end
        samples.append(text[:sample_size])
        samples.append(text[text_len//2 - sample_size//2:text_len//2 + sample_size//2])
        samples.append(text[text_len-sample_size:])
    else:
        # Use whole text if short enough
        samples.append(text[:sample_size] if text_len > sample_size else text)
    
    best_mapping = initial_mapping.copy()
    
    # Score each sample and sum them up
    best_score = 0
    for sample in samples:
        decryption = apply_mapping(sample, best_mapping)
        best_score += scorer.score(decryption)
        # Add bonus for common words detected
        best_score += count_common_words(decryption) * 5
    
    # Keep track of progress
    iterations_without_improvement = 0
    start_time = time.time()
    temperature = initial_temp
    improvement_count = 0
    temp_resets = 0
    max_temp_resets = 3

    for iteration in range(max_iterations):
        trial_mapping = best_mapping.copy()

        # Swap two random letters
        a, b = random.sample(string.ascii_lowercase, 2)
        for k, v in trial_mapping.items():
            if v == a:
                trial_mapping[k] = b
            elif v == b:
                trial_mapping[k] = a

        # Score all samples and sum up
        trial_score = 0
        for sample in samples:
            decryption = apply_mapping(sample, trial_mapping)
            trial_score += scorer.score(decryption)
            # Add bonus for common words detected
            trial_score += count_common_words(decryption) * 5

        # Delta between new and old scores
        score_delta = trial_score - best_score

        # Accept if better score, or with probability based on temperature
        if score_delta > 0 or random.random() < math.exp(score_delta / temperature):
            best_score = trial_score
            best_mapping = trial_mapping
            
            # Track improvements
            if score_delta > 0:
                improvement_count += 1
                iterations_without_improvement = 0
                if improvement_count % 20 == 0:
                    print(f"[+] Iteration {iteration}: Improved score: {best_score:.2f}, temp: {temperature:.4f}")
            
        else:
            iterations_without_improvement += 1
            
        # Cool down the temperature
        temperature *= cooling_rate
        
        # Early stopping if no improvement for a while
        if iterations_without_improvement >= early_stop:
            # If we're less than halfway through, try resetting temperature to escape local minimum
            if iteration < max_iterations // 2 and temp_resets < max_temp_resets:
                print(f"[*] Resetting temperature to escape local minimum (reset {temp_resets+1}/{max_temp_resets})")
                temperature = initial_temp * (0.7 ** (temp_resets + 1))  # Each reset has slightly lower temperature
                iterations_without_improvement = 0
                temp_resets += 1
                
                # Show current sample to indicate progress
                sample_decryption = apply_mapping(text[:200], best_mapping)
                print(f"[*] Current sample decryption: {sample_decryption}")
                continue
            
            print(f"[+] Early stopping after {iteration} iterations - no improvement for {early_stop} iterations")
            sample_decryption = apply_mapping(text[:200], best_mapping)
            print(f"[*] Final sample decryption: {sample_decryption}")
            break

    elapsed = time.time() - start_time
    print(f"[+] Refinement completed in {elapsed:.2f} seconds ({iteration+1} iterations)")
    print(f"[+] Final score: {best_score:.2f} with {improvement_count} improvements")
    print_mapping(best_mapping)
    return best_mapping


# --------------------------
# Password Extraction Logic
# --------------------------
def find_and_decrypt_password_candidates(source1_path, source2_path, source3_path, mapping, scorer, min_length=4):
    """Find and decrypt reused OTP password segments in Source-2 and return the most plausible one."""
    start_time = time.time()
    print("\n[+] Loading files for password extraction...")
    
    with open(source1_path, 'rb') as f1, open(source2_path, 'rb') as f2, open(source3_path, 'rb') as f3:
        source1 = f1.read()
        source2 = f2.read()
        source3 = f3.read()

    print(f"[+] XORing Source-1 and Source-3 to find matching segments...")
    xor_result = xor_bytes(source1, source3)
    matches = find_matching_segments(xor_result, min_length)

    if not matches:
        print("[!] No password-like segments found.")
        return

    print(f"\n[+] Found {len(matches)} matching segments (length ≥ {min_length})")

    best_score = float('-inf')
    best_segment = None
    candidate_segments = []

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
        # Normalize score by length and add bonus for common words
        score = scorer.score(decrypted_str) / max(1, len(decrypted_str))
        word_bonus = count_common_words(decrypted_str) * 2
        total_score = score + word_bonus

        print(f"[{idx}] Offset {pos}, Length {length} → Score: {total_score:.4f} → {decrypted_str}")
        candidate_segments.append((pos, length, decrypted_str, total_score))

        if total_score > best_score:
            best_score = total_score
            best_segment = (pos, length, decrypted_str)

    if best_segment:
        pos, length, best_decryption = best_segment
        print("\n[✅] Best candidate:")
        print(f"Offset: {pos}, Length: {length}, Score: {best_score:.2f}")
        print(f"Decrypted Password: {best_decryption}")
        
        # Show top 3 candidates if we have them
        if len(candidate_segments) > 1:
            print("\nTop candidates:")
            for idx, (pos, length, text, score) in enumerate(sorted(candidate_segments, 
                                                                   key=lambda x: x[3], reverse=True)[:3], 1):
                print(f"{idx}. Offset {pos}, Length {length}, Score {score:.2f}: {text}")
    else:
        print("[!] No valid decrypted segments found.")
        
    elapsed = time.time() - start_time
    print(f"[+] Password extraction completed in {elapsed:.2f} seconds")


# --------------------------
# Main Entry Point
# --------------------------
def main():
    total_start_time = time.time()
    
    print("\n[1] Loading encrypted text...")
    start_time = time.time()
    encrypted_text = load_file('Source-2-encrypted.txt')
    print(f"    - Loaded {len(encrypted_text)} characters in {time.time() - start_time:.2f} seconds")

    print("\n[2] Analyzing frequency...")
    start_time = time.time()
    frequencies = get_letter_frequencies(encrypted_text)
    print(f"    - Frequency analysis completed in {time.time() - start_time:.2f} seconds")

    print("\n[3] Creating initial mapping...")
    start_time = time.time()
    mapping = create_initial_mapping(frequencies, ENGLISH_FREQ_ORDER)
    print(f"    - Initial mapping created in {time.time() - start_time:.2f} seconds")

    print("\n[4] Loading quadgram model...")
    start_time = time.time()
    scorer = QuadgramScorer('english_quadgrams.txt')
    print(f"    - Quadgram model loaded in {time.time() - start_time:.2f} seconds")

    print("\n[5] Refining mapping using quadgram scoring and simulated annealing...")
    # Improved parameters for better results
    mapping = auto_refine_mapping(
        encrypted_text, 
        mapping, 
        scorer, 
        max_iterations=2000,       # More iterations for better results
        sample_size=8000,          # Larger sample for better scoring
        early_stop=150,            # Allow more attempts without improvement
        initial_temp=10.0,         # Starting temperature
        cooling_rate=0.99          # Slow cooling for thorough search
    )

    print("\n[6] Applying final mapping...\n")
    start_time = time.time()
    decrypted = apply_mapping(encrypted_text, mapping)
    decrypt_time = time.time() - start_time
    print(f"    - Full text decrypted in {decrypt_time:.2f} seconds")
    
    # Show more of the decrypted text for verification
    preview_length = min(3000, len(decrypted))
    for chunk in textwrap.wrap(decrypted[:preview_length], width=100):
        print(chunk)

    total_time = time.time() - total_start_time
    print(f"\n[+] Total processing time: {total_time:.2f} seconds")

    # Automatically save the decrypted text
    output_file = "decrypted_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(decrypted)
    print(f"[+] Saved decrypted text to '{output_file}'")

    # Automatically run password finder
    print("\n[7] Checking for reused OTP password segments...")
    find_and_decrypt_password_candidates(
        "Source-1-encrypted.txt",
        output_file, 
        "Source-3-encrypted.txt",
        mapping,
        scorer,
        min_length=8
    )


if __name__ == "__main__":
    main()