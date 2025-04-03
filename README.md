# Final Assignment – Practical Applications in Computer Science

## General Instructions

- **Submission Deadline:** March 31, 2025, at 23:59
- **Submission Type:** Pairs are allowed.
- **Weight:** 50% of the final course grade.
- **Files Provided:** A program file with comments labeled `SHMULIK` is included for reference.

This assignment contains summarizing questions covering all topics learned in the course.

---

## Question 1: Fail-Safe Software Update System

Implement a software update system for a flash memory device that supports **fail-safe behavior** — i.e., it must recover from power loss and resume updating correctly.

### System Assumptions:
- Memory is divided into **blocks of 100 bytes**.
- Blocks are written/erased as whole units.
- Update order matters (blocks must be updated from 0 to 9).
- A free block (block 100) is available for temporary use.

### Failure Scenarios:
1. Power loss before erase – block remains unchanged.
2. Power loss during erase/write – block may be corrupted.
3. Power loss after write – block contains updated data.

### Your Task:
Implement `perform_update()` to safely apply updates under the constraints above.

#### Helper Functions Provided:
- `read_block(block_number)`
- `write_block(block_number, block_content)`
- `get_flash_block_signature(block_number)`
- `get_expected_block_signature_after_update(block_number)`
- `compute_block_updated_content(block_number)`
- `update_needed() -> bool`
- `set_update_finished()`

#### Boot Logic:
```python
def boot_start():
    if update_needed():
        perform_update()
        set_update_finished()
    else:
        continue_normal_boot()
```

---

## Question 2: Huffman Compression

Given alert frequency data from a security monitoring system:

| Alert Type         | Code | Frequency |
|--------------------|------|-----------|
| Login Failed       | F    | 45%       |
| Access Denied      | D    | 25%       |
| Password Reset     | R    | 15%       |
| New IP Login       | N    | 8%        |
| Malware Detected   | M    | 5%        |
| System Error       | E    | 2%        |

### Tasks:
1. Design a Huffman code for the alerts.
2. Calculate **daily storage savings** (in bits and bytes) compared to 8-bit per alert.
3. Calculate **annual savings** (365 days).
4. Should encoding change throughout the day based on alert type distribution?

---

## Question 3: Frequency Domain Audio Processing

Given an equalizer GUI that reads and processes WAV files:

### Task:
Implement `process_audio_file(fft_data, slider_values, sample_rate, output_file)` to:
- Adjust audio frequency bands (-10 to +10 dB).
- Modify volume based on slider values.
- Rebuild and save the modified audio using IFFT.

*No real-time playback needed — process in batch.*

---

## Question 4: Encryption (Code Breaking)

Three encrypted English text files were given:
- Two used the same **One-Time Pad** key.
- One used a **Caesar cipher** (fixed shift permutation).

### Tasks:
1. Identify which file was encrypted with which method.
2. Recover the encryption key and decrypt the files.
3. Provide:
   - Explanation of steps.
   - Intermediate files and tools.
   - Final decrypted "key message" (e.g., `I am the code to the Atom Secrets of Iran`).

---

## Question 5: Auto-Completion Algorithm

Enhance an existing search bar tool to support intelligent auto-completion.

### Functionality:
- Store user input (submitted via Enter).
- Suggest top 3 completions from:
  - User history (with frequency priority).
  - Default joke text file.
- Update suggestion frequency with each use.
- Avoid duplicate completions.

### Bonus:
- Add search bar that also updates suggestions.
- Add a button to replace pressing Enter.

---

## Question 6: Real-Time Video Frame Averaging

Given a program that streams video from an MJPEG URL:

### Task:
Implement `process_new_frame(self, frame)` to:
- Show the **live feed** on the left.
- Show a **running average** of the last 5 minutes of frames on the right (1 frame/second = 300 frames).

### Requirements:
- Efficient memory (no redundant full history storage).
- Avoid slow recalculations.

**Use only static/slow-changing public webcams.**

Sample URLs provided in the PDF.

---

Good luck!