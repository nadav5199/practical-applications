# Global buffers and flag
import os

flash_sim = ['A'] * 1000
extra_block = ['C'] * 100  # Initialize with 'C'*100
update_needed_flag = True


def read_block(block_number):
    block_content = ""
    if block_number == 100:
        block_content = ''.join(extra_block[:100])
    elif 0 <= block_number <= 9:
        start = block_number * 100
        block_content = ''.join(flash_sim[start:start + 100])
    return block_content


def write_block(block_number, block_content):
    # Pad block_content to 100 chars if needed
    content = list(block_content[:100])
    if len(content) < 100:
        content.extend(['0'] * (100 - len(content)))

    if block_number == 100:
        global extra_block
        extra_block = content
    elif 0 <= block_number <= 9:
        start = block_number * 100
        global flash_sim
        flash_sim[start:start + 100] = content


def get_flash_block_signature(block_number):
    if block_number == 100:
        block = extra_block[:100]
    elif 0 <= block_number <= 9:
        start = block_number * 100
        block = flash_sim[start:start + 100]

    if all(c == 'A' for c in block):
        return 0xaaaaaaaa
    elif all(c == 'B' for c in block):
        return 0xbbbbbbbb
    else:
        return 0x123456789


def get_expected_block_signature_after_update(block_number):
    return 0xbbbbbbbb


def compute_block_updated_content(block_number):
    if 0 <= block_number <= 9:
        start = block_number * 100
        block = flash_sim[start:]
        if all(c == 'A' for c in block):
            return 'B' * 100
        else:
            return 'C' * 100


def update_needed():
    global update_needed_flag
    return update_needed_flag


def set_update_finished():
    global update_needed_flag
    update_needed_flag = False

# SHMULIK: This is your entry point
def perform_update():
    # Step 1: Check each block's status and determine update strategy
    for block_number in range(10):
        current_sig = get_flash_block_signature(block_number)
        expected_sig = get_expected_block_signature_after_update(block_number)
        
        # Skip if already updated
        if current_sig == expected_sig:
            continue
            
        # Step 2: Prepare update content in extra block
        # Always update to 'B'*100 for blocks 0-9
        new_content = 'B' * 100
        
        # Store original extra block content
        original_extra_block = read_block(100)
        
        # Write new content to extra block first (safe storage)
        write_block(100, new_content)
        
        # Verify extra block content is correct
        extra_block_sig = get_flash_block_signature(100)
        if extra_block_sig != expected_sig:
            # If verification fails, retry writing to extra block
            write_block(100, new_content)
            extra_block_sig = get_flash_block_signature(100)
            if extra_block_sig != expected_sig:
                # If still fails, skip this block and continue with others
                write_block(100, original_extra_block)  # Restore original content
                continue
        
        # Step 3: Write to target block
        write_block(block_number, new_content)
        
        # Verify target block was written correctly
        final_sig = get_flash_block_signature(block_number)
        if final_sig != expected_sig:
            # If verification fails, retry writing to target block
            write_block(block_number, new_content)
            final_sig = get_flash_block_signature(block_number)
            if final_sig != expected_sig:
                # If still fails, skip this block and continue with others
                write_block(100, original_extra_block)  # Restore original content
                continue
        
        # Restore original extra block content after successful update
        write_block(100, original_extra_block)
    
    # Step 4: Mark update as complete
    set_update_finished()


def continue_normal_boot():
    # Write flash_sim content to file
    buffer_str = ''.join(flash_sim)
    with open('flash_sim.txt', 'w') as f:
        for i in range(0, 1000, 100):
            line = buffer_str[i:i+100]
            f.write(line + '\n')
        f.write('\n')
        # Write extra block content
        f.write(''.join(extra_block))

def boot_start():
    if update_needed():
        perform_update()
        set_update_finished()
        continue_normal_boot()
    else:
        continue_normal_boot()


# Example usage
if __name__ == "__main__":
    # Test the functions

    # Read initial block
    block_content = read_block(0)

    print("Initial block 0:", block_content[:10], "...")

    # Get signature
    sig = get_flash_block_signature(0)
    print("Block 0 signature:", hex(sig))

    # Perform boot
    boot_start()

    # Check result
    block_content = read_block(0)
    print("After update block 0:", block_content[:10], "...")

    sig = get_flash_block_signature(0)
    print("New block 0 signature:", hex(sig))