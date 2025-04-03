# Global buffers and flag
import os

flash_sim = ['A'] * 1000
extra_block = ['C'] * 100
update_needed_flag = True

# State machine states
STATE_INIT = 'INIT'
STATE_ERASING = 'ERASING'
STATE_WRITING = 'WRITING'
STATE_COMPLETE = 'COMPLETE'

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
        block = flash_sim[start:start + 100]
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

def save_state(state, current_block):
    """Save current state and block number to extra block"""
    state_data = f"{state}:{current_block}"
    write_block(100, state_data)

def get_state():
    """Read current state from extra block"""
    state_data = read_block(100)
    if not state_data:
        return STATE_INIT, -1
    try:
        state, block = state_data.split(':')
        return state, int(block)
    except:
        return STATE_INIT, -1

def perform_update():
    """Fail-safe update implementation"""
    current_state, current_block = get_state()
    print(f"Starting update from state: {current_state}, block: {current_block}")
    
    if current_state == STATE_INIT:
        # Start update process
        print("Initializing update process")
        save_state(STATE_ERASING, 0)
        current_block = 0
    
    if current_state == STATE_ERASING:
        # Erase current block
        print(f"Erasing block {current_block}")
        write_block(current_block, '0' * 100)
        save_state(STATE_WRITING, current_block)
    
    if current_state == STATE_WRITING:
        # Write new content to current block
        print(f"Writing new content to block {current_block}")
        new_content = compute_block_updated_content(current_block)
        write_block(current_block, new_content)
        
        # Move to next block or complete
        if current_block < 9:
            current_block += 1
            print(f"Moving to next block: {current_block}")
            save_state(STATE_ERASING, current_block)
        else:
            print("Update complete")
            save_state(STATE_COMPLETE, current_block)
    
    if current_state == STATE_COMPLETE:
        # Update is complete
        print("Setting update as finished")
        set_update_finished()

def continue_normal_boot():
    buffer_str = ''.join(flash_sim)
    with open('flash_sim.txt', 'w') as f:
        for i in range(0, 1000, 100):
            line = buffer_str[i:i+100]
            f.write(line + '\n')
        f.write('\n')
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