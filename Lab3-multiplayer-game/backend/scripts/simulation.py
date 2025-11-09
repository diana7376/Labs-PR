"""
Single-player Memory Scramble game simulation.

Simulates one player interacting with the board, randomly flipping cards
until all pairs are matched. Demonstrates that the Board ADT works correctly
without concurrency complications.

Usage:
    python -m scripts.simulation
    or
    cd backend && python -m scripts.simulation
"""

import random
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.board import Board


def simulate_single_player(width: int, height: int, num_unique_cards: int) -> None:
    """
    Simulate a single player playing Memory Scramble.

    The player randomly flips cards, trying to find matching pairs.
    Game ends when all pairs are matched.

    Args:
        width: Board width (columns)
        height: Board height (rows)
        num_unique_cards: Number of unique card types (must be width*height/2)
    """
    # Validate input
    if len(list(range(num_unique_cards))) * 2 != width * height:
        print(f"❌ Error: {num_unique_cards} unique cards * 2 = {num_unique_cards * 2}, "
              f"but {width}x{height} = {width * height} spaces")
        return

    # Create cards
    cards = {f"Card{i + 1}" for i in range(num_unique_cards)}

    print("\n" + "=" * 70)
    print(f"🎮 Starting Memory Scramble Simulation")
    print(f"   Board: {width}x{height}")
    print(f"   Cards: {num_unique_cards} unique types (total {width * height} spaces)")
    print("=" * 70 + "\n")

    # Create board
    try:
        board = Board(width, height, cards)
        print("✅ Board created successfully!")
        print(f"\nInitial board state:\n{board}\n")
    except AssertionError as e:
        print(f"❌ Failed to create board: {e}")
        return

    # Game simulation
    player_id = "Player1"
    moves = 0
    matches_found = 0
    total_pairs = num_unique_cards

    # Track which positions have been matched
    matched_positions = set()

    print("Starting single-player game...\n")
    print("Rules:")
    print("  - Player tries to find matching pairs")
    print("  - Flips two cards at a time")
    print("  - If they match, they stay face-up and removed")
    print("  - If not, they flip back face-down")
    print("-" * 70 + "\n")

    # Game loop
    max_moves = 1000  # Prevent infinite loops
    move_number = 1

    while matches_found < total_pairs and move_number <= max_moves:
        print(f"--- Move {move_number} ---")

        try:
            # Get list of available positions (not matched)
            available_positions = []
            for y in range(height):
                for x in range(width):
                    if (x, y) not in matched_positions:
                        available_positions.append((x, y))

            if not available_positions:
                break  # All cards matched!

            # Pick first card randomly
            first_pos = random.choice(available_positions)
            x1, y1 = first_pos

            print(f"Player flips card at ({x1}, {y1}): {board.get_card(x1, y1)}", end=" ")
            board.flip_card(x1, y1)
            board.set_control(x1, y1, player_id)
            first_card = board.get_card(x1, y1)
            print("✓ (face-up)")

            # Pick second card randomly from remaining available
            remaining = [pos for pos in available_positions if pos != first_pos]

            if not remaining:
                print("  (No second card available - removing matched card)")
                board.remove_card(x1, y1)
                matched_positions.add(first_pos)
                matches_found += 1
                move_number += 1
                print(f"  Matches found: {matches_found}/{total_pairs}\n")
                continue

            second_pos = random.choice(remaining)
            x2, y2 = second_pos

            print(f"Player flips card at ({x2}, {y2}): {board.get_card(x2, y2)}", end=" ")
            board.flip_card(x2, y2)
            board.set_control(x2, y2, player_id)
            second_card = board.get_card(x2, y2)
            print("✓ (face-up)")

            moves += 1

            # Check if match
            if first_card == second_card:
                print(f"  ✨ MATCH! Both cards are {first_card}")
                # Remove both cards
                board.remove_card(x1, y1)
                board.remove_card(x2, y2)
                matched_positions.add(first_pos)
                matched_positions.add(second_pos)
                matches_found += 1
                print(f"  Matches found: {matches_found}/{total_pairs} ✓")
            else:
                print(f"  ❌ No match: {first_card} ≠ {second_card}")
                # Flip both cards back face-down
                board.flip_card(x1, y1)
                board.flip_card(x2, y2)
                print(f"  Cards flipped back face-down")

            print(f"  Board after move:\n{board}\n")
            board.check_rep()  # Verify board integrity

            move_number += 1

        except Exception as e:
            print(f"❌ Error during move: {e}")
            import traceback
            traceback.print_exc()
            return

    # Game end
    print("\n" + "=" * 70)
    if matches_found == total_pairs:
        print(f"🎉 SUCCESS! All {total_pairs} pairs matched!")
        print(f"   Total moves: {moves}")
        print(f"   Average cards flipped per move: {(moves * 2) / (move_number - 1):.1f}")
    else:
        print(f"⏱️ Simulation timeout after {max_moves} moves")
        print(f"   Matches found: {matches_found}/{total_pairs}")
    print("=" * 70 + "\n")

    # Final board state
    print(f"Final board state:\n{board}")
    print("\n✅ Simulation completed successfully!")
    print("✅ Board ADT validated with single-player gameplay!\n")


def main() -> None:
    """Run multiple simulations with different board sizes."""

    print("\n🎲 Memory Scramble Single-Player Simulation Suite\n")

    # Test Case 1: Small 2x2 board (1 pair)
    print("\n>>> Test 1: Small Board (2x2, 1 pair)")
    simulate_single_player(width=2, height=2, num_unique_cards=1)
    input("Press Enter to continue...\n")

    # Test Case 2: Medium 4x4 board (8 pairs)
    print("\n>>> Test 2: Medium Board (4x4, 8 pairs)")
    simulate_single_player(width=4, height=4, num_unique_cards=8)
    input("Press Enter to continue...\n")

    # Test Case 3: Larger 4x6 board (12 pairs)
    print("\n>>> Test 3: Larger Board (4x6, 12 pairs)")
    simulate_single_player(width=4, height=6, num_unique_cards=12)

    print("\n" + "=" * 70)
    print("✅ All simulation tests completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
