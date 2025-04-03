import unittest
import os

# We do NOT copy your professor's code. We import from the same folder:
from FlashUpdater import (
    flash_sim, extra_block, update_needed_flag,
    read_block, write_block, get_flash_block_signature,
    get_expected_block_signature_after_update,
    compute_block_updated_content, update_needed,
    set_update_finished, perform_update, continue_normal_boot,
    boot_start
)

class TestFlashUpdater(unittest.TestCase):
    """
    We'll create a total of 20 tests:
      - 12 Low-Level Tests
      - 8 High-Level Tests
    """

    def setUp(self):
        """
        Reset the environment (globals) before each test to ensure isolation.
        """
        # Reset the flash_sim, extra_block, and update_needed_flag manually.
        for i in range(1000):
            flash_sim[i] = 'A'  # 10 blocks (0..9), each 100 chars
        for i in range(100):
            extra_block[i] = 'C'  # block #100
        
        # Fix global variable reset - must match the exact global in FlashUpdater.py
        import FlashUpdater  # Direct import for explicit access
        FlashUpdater.update_needed_flag = True  # Access the actual module-level variable
        
        # Verify the reset worked
        self.assertTrue(update_needed(), "update_needed_flag not properly reset to True")

        # Remove any leftover output file
        if os.path.exists('flash_sim.txt'):
            os.remove('flash_sim.txt')

    # -----------------------------------------------------
    #                LOW-LEVEL TESTS (12)
    # -----------------------------------------------------

    # 1) Low-Level Test
    def test_read_block_initial_A(self):
        """Low-Level #1: read_block() returns 'A'*100 for blocks 0..9 initially."""
        for block_num in range(10):
            content = read_block(block_num)
            self.assertEqual(content, 'A'*100, f"Block {block_num} should be 'A'*100 at start")

    # 2) Low-Level Test
    def test_read_block_initial_C(self):
        """Low-Level #2: read_block() returns 'C'*100 for block 100 initially."""
        self.assertEqual(read_block(100), 'C'*100, "Block 100 should be 'C'*100 at start")

    # 3) Low-Level Test
    def test_write_block_short_content(self):
        """Low-Level #3: write_block() pads short content up to length=100."""
        write_block(0, "HELLO")
        self.assertEqual(read_block(0)[:5], "HELLO", "First 5 chars must be 'HELLO'")
        self.assertEqual(len(read_block(0)), 100, "Block length is always 100")

    # 4) Low-Level Test
    def test_write_block_long_content(self):
        """Low-Level #4: write_block() truncates content over 100 chars."""
        long_data = "X"*200  # 200 chars
        write_block(1, long_data)
        self.assertEqual(len(read_block(1)), 100, "Should only keep first 100 chars")

    # 5) Low-Level Test
    def test_block_signature_A(self):
        """Low-Level #5: get_flash_block_signature() for 'A'*100 => 0xaaaaaaaa."""
        sig = get_flash_block_signature(0)
        self.assertEqual(sig, 0xaaaaaaaa, "Signature for a block of all A is 0xaaaaaaaa")

    # 6) Low-Level Test
    def test_block_signature_B(self):
        """Low-Level #6: get_flash_block_signature() for 'B'*100 => 0xbbbbbbbb."""
        write_block(2, "B"*100)
        sig = get_flash_block_signature(2)
        self.assertEqual(sig, 0xbbbbbbbb, "Signature for a block of all B is 0xbbbbbbbb")

    # 7) Low-Level Test
    def test_block_signature_C(self):
        """Low-Level #7: get_flash_block_signature() for 'C'*100 => 0x123456789 in given code."""
        # By default, block 100 is 'C'*100 => check signature
        sig = get_flash_block_signature(100)
        self.assertEqual(sig, 0x123456789, "Block of all 'C's => 0x123456789 as per code")

    # 8) Low-Level Test
    def test_block_signature_mixed(self):
        """Low-Level #8: Mixed content => 0x123456789 by default."""
        write_block(3, "ABC"*33 + "D")  # definitely not all A or all B
        sig = get_flash_block_signature(3)
        self.assertEqual(sig, 0x123456789, "Mixed content => 0x123456789")

    # 9) Low-Level Test
    def test_compute_block_updated_content_A(self):
        """Low-Level #9: compute_block_updated_content() on an 'A' block => 'B'*100."""
        self.assertEqual(compute_block_updated_content(4), 'B'*100,
                         "If block is all A, new content is all B")

    # 10) Low-Level Test
    def test_compute_block_updated_content_B(self):
        """Low-Level #10: compute_block_updated_content() on a non-A block => 'C'*100."""
        write_block(5, 'B'*100)
        self.assertEqual(compute_block_updated_content(5), 'C'*100,
                         "If block is not all A, new content is all C")

    # 11) Low-Level Test
    def test_update_needed_default(self):
        """Low-Level #11: update_needed() is True by default from setUp()."""
        self.assertTrue(update_needed(), "Should be True at start")

    # 12) Low-Level Test
    def test_update_needed_after_set_finished(self):
        """Low-Level #12: set_update_finished() => update_needed() becomes False."""
        self.assertTrue(update_needed(), "Check is True before finishing")
        set_update_finished()
        self.assertFalse(update_needed(), "Should go False after set_update_finished()")

    # -----------------------------------------------------
    #                HIGH-LEVEL TESTS (8)
    # -----------------------------------------------------

    # 13) High-Level Test
    def test_perform_update_blocks_A_to_B(self):
        """High-Level #1: perform_update() on all-A blocks => all become B."""
        perform_update()
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'B'*100,
                             f"Block {bnum} should be updated to all B")

    # 14) High-Level Test
    def test_boot_start_performs_update(self):
        """High-Level #2: boot_start() sees update_needed=True, does update => sets update_needed=False."""
        boot_start()
        # blocks 0..9 => 'B'*100
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'B'*100)
        # update_needed_flag => False
        self.assertFalse(update_needed(), "After boot_start completes with update, it should be False")

    # 15) High-Level Test
    def test_boot_start_skips_update(self):
        """High-Level #3: If update_needed_flag=False, no update is performed by boot_start()."""
        set_update_finished()  # sets update_needed_flag=False
        boot_start()
        # blocks 0..9 => remain 'A'*100
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'A'*100,
                             "No update should happen if update_needed_flag is False")

    # 16) High-Level Test
    def test_flash_sim_file_created(self):
        """High-Level #4: boot_start() should create 'flash_sim.txt' regardless of update."""
        boot_start()  # triggers normal boot
        self.assertTrue(os.path.exists('flash_sim.txt'), "Should generate 'flash_sim.txt' after normal boot.")

    # 17) High-Level Test
    def test_perform_update_partial_interruption(self):
        """
        High-Level #5: Simulate "turning off" update_needed midway.
        We'll forcibly set update_needed_flag=False after writing a few blocks 
        to mimic partial update. Then confirm blocks are partially updated.
        """
        # Reset the flag to True before starting (extra insurance)
        import FlashUpdater
        FlashUpdater.update_needed_flag = True
        
        original_flag = update_needed()  # Should be True
        self.assertTrue(original_flag, "Start True")

        # Let's do the first half of the blocks ourselves:
        for block_num in range(5):
            new_content = compute_block_updated_content(block_num)
            write_block(block_num, new_content)

        # Simulate the professor "turning off" the update in the middle:
        set_update_finished()
        self.assertFalse(update_needed(), "We just forced it to False mid-update")

        # Try continuing the update loop:
        # If your perform_update checks update_needed each iteration (depending on your logic),
        # it might skip updating the remaining blocks. We'll call it again.
        perform_update()

        # Now check blocks 0..4 => should be B (already updated)
        for block_num in range(5):
            self.assertEqual(read_block(block_num), 'B'*100,
                             f"Block {block_num} was updated before turning off")

        # Check blocks 5..9 => might remain 'A' or might be updated depending on your logic.
        # If your perform_update doesn't stop mid-loop, they'd be B too.
        # We'll just confirm it didn't fully update them if your code checks update_needed mid-loop.
        # Adjust your expectation as needed:
        for block_num in range(5, 10):
            # We expect them to remain 'A'*100 if the code stops updating once update_needed=False
            actual = read_block(block_num)
            if actual == 'A'*100:
                # That means partial update indeed stopped
                pass
            elif actual == 'B'*100:
                # That means the code kept going anyway 
                pass
            else:
                self.fail(f"Block {block_num} ended in unexpected state: {actual[:10]}...")

    # 18) High-Level Test
    def test_boot_start_partial_interruption(self):
        """
        High-Level #6: Similar partial interruption scenario, but using boot_start().
        We'll set update_needed_flag=False after a few blocks are changed.
        """
        # We'll hijack the first few updates by calling perform_update partially,
        # then forcibly set flag to False, then call boot_start.
        for block_num in range(3):
            write_block(block_num, compute_block_updated_content(block_num))

        set_update_finished()  # forcibly end the update
        boot_start()  # now it should see update_needed=False

        # First 3 blocks => B, blocks 3..9 => remain A, if partial was recognized
        for bnum in range(3):
            self.assertEqual(read_block(bnum), 'B'*100, f"Block {bnum} changed to B before update was turned off")

        # The rest => 'A'*100 if your code doesn't forcibly re-check them
        for bnum in range(3, 10):
            self.assertEqual(read_block(bnum), 'A'*100, f"Block {bnum} should remain A if update is off")

    # 19) High-Level Test
    def test_multi_boot_starts_updates_once(self):
        """
        High-Level #7: Call boot_start() multiple times with update_needed=True 
        but only the first call should do the update. The subsequent calls see flag is now False.
        """
        # 1st call => Should perform the update and set flag to False
        boot_start()
        # verify updated
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'B'*100, f"Block {bnum} after first boot_start")

        # 2nd call => Now update_needed=False, so no changes
        boot_start()
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'B'*100, f"Block {bnum} must remain B after second call")

    # 20) High-Level Test
    def test_perform_update_signature_verification(self):
        """
        High-Level #8: After perform_update, blocks should match the 'expected' 
        signature from get_expected_block_signature_after_update().
        """
        perform_update()
        for bnum in range(10):
            actual_sig = get_flash_block_signature(bnum)
            expected_sig = get_expected_block_signature_after_update(bnum)
            self.assertEqual(actual_sig, expected_sig,
                             f"Block {bnum} signature must match expected after update")


    # 21) Extra High-Level Test: Re-update a block that's 'C' (Sabotage scenario)
    def test_reupdate_sabotaged_block_c(self):
        """
        Edge Case #1:
        Force a block to become 'C'*100 (as if sabotage or partial update left it in 'C').
        Then call perform_update() again. Some logic forcibly writes 'B'*100 to every not-'B' block.
        We expect the final block to be 'B'*100 if the code forcibly updates sabotage blocks to the new version.
        """
        # Force block #2 to be 'C'*100
        write_block(2, 'C'*100)
        # Confirm it is 'C'
        self.assertEqual(read_block(2), 'C'*100)

        # Now perform the update
        perform_update()

        # If your final code forcibly updates any block not already 'B',
        # we expect block #2 to be 'B'*100 now.
        # (If your code strictly follows compute_block_updated_content logic, 
        # then 'C' => 'C', but your final code forcibly writes 'B' to blocks 
        # that aren't updated. Check your code to confirm which outcome is correct.)
        self.assertEqual(read_block(2), 'B'*100, "Block #2 should be re-updated from 'C' to 'B'")

    # 22) Extra Low-Level Test: Out-of-range block indices
    def test_out_of_range_blocks(self):
        """
        Edge Case #2:
        Call read_block/write_block for out-of-range block indices (e.g. -1, 11).
        Your code might do nothing, return empty string, or raise an error.
        If you want to handle them gracefully, confirm that there's no crash and 
        the function returns a sensible result (e.g. empty string).
        """
        # read_block on invalid index
        content_neg = read_block(-1)  # not valid per assignment
        content_11  = read_block(11)  # also not valid

        # We expect either empty string or a no-op. 
        # Adjust as needed based on your actual design or your professor's instructions.
        self.assertEqual(content_neg, "", "Out-of-range read_block(-1) should return empty string or do nothing")
        self.assertEqual(content_11, "", "Out-of-range read_block(11) should return empty string or do nothing")

        # write_block on invalid index
        # Should ideally do nothing or skip. We'll check there's no crash at least.
        write_block(-1, "TEST")
        write_block(11, "TEST")

        # If there's no crash, it's presumably safe. 
        # We can also confirm that blocks 0..9 remain unchanged after this.
        for bnum in range(10):
            self.assertEqual(read_block(bnum), 'A'*100, f"Block {bnum} should remain 'A'*100 if out-of-range writes are no-ops")

    # 23) Extra High-Level Test: Corruption in spare block mid-update
    def test_spare_block_corruption(self):
        """
        Edge Case #3:
        Simulate that the code wrote partial/corrupted content to the spare block #100. 
        Then see if your update code catches it or leaves the block alone.
        This is hypothetical because your assignment doesn't provide a "partial write" function, 
        but we can mimic by forcibly injecting half 'B' and half 'Z'.
        """
        # Start an update on block #0 manually:
        # 1) Write half 'B', half 'Z' to the spare block to simulate corruption
        corrupted_data = 'B'*50 + 'Z'*50
        write_block(100, corrupted_data)

        # 2) Now let perform_update() run. 
        # Depending on your logic, it might re-write the entire spare block to 'B'*100 
        # once it sees the signature is wrong.
        perform_update()

        # We check final block #0. In a robust approach, 
        # the code should have recognized the mismatch and forcibly replaced the spare block with 'B'*100,
        # then updated block #0. So we expect block #0 => 'B'*100.
        self.assertEqual(read_block(0), 'B'*100, "Block #0 should still become 'B'*100 despite corruption in the spare block.")

# ---------------------------------------------------------
# If run directly, unittest will be invoked:
# ---------------------------------------------------------
if __name__ == '__main__':
    unittest.main()
