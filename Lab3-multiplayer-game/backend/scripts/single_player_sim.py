"""
Single-player simulation of Memory Scramble game.

Simulates one player interacting with the board,
randomly flipping cards until all pairs are matched.

This helps verify that the Board ADT works correctly
without concurrency complications.
"""

import random
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game.board import Board


async def simulate_single_player(width: int, height: int, num_unique_cards: int) -> None:
    """
    Simulate a single player playing Memory Scramble.

    Args:
        width: Board width
        height: Board height
        num_unique_cards: Number of unique card types
    """
    # Create cards
    cards = set()
    for i in range(num_unique_cards):
        cards.add(f"Card{i + 1}")

    # Validate
    if len(cards) * 2 != width * height:
        print(f"Error: {len(cards)} unique cards * 2 = {len(cards) * 2}, "
              f"but {width}x{height} = {width * height} spaces")
        return

    # Create board
    print(f"Creating {width}x{height} board with {num_unique_cards} card types...")
    board = Board(width, height, cards)
    board.check_rep()
    print("Board created successfully!\n")
    print(board)
    print()

    # Track game state
    matched_pairs = 0
    total_pairs = len(cards)
    move_count = 0
    first_card_pos = None

    # Play until all pairs matched
    while matched_pairs < total_pairs:
        # Choose random face-down card
        face_down_positions = []
        for y in range(board.height):
            for x in range(board.width):
                if board.get_card(x, y) is not None and not board.is_face_up(x, y):
                    face_down_positions.append((x, y))

        if not face_down_positions:
            print("No more face-down cards! Game complete!")
            break

        # Make move
        x, y = random.choice(face_down_positions)
        move_count += 1

        print(f"Move {move_count}: Flipping card at ({x}, {y})...")
        board.flip_card(x, y)
        card_value = board.get_card(x, y)
        print(f"  → Found: {card_value}")

        # First or second card of pair?
        if first_card_pos is None:
            # First card
            first_card_pos = (x, y)
            board.set_control(x, y, "player1")
            print(f"  Player1 controls this card")
        else:
            # Second card
            fx, fy = first_card_pos
            first_card = board.get_card(fx, fy)
            second_card = board.get_card(x, y)

            if first_card == second_card:
                # Match!
                print(f"  ✓ MATCH! {first_card} matches!")
                # Remove both cards TOGETHER (must remove in same operation for invariant)
                try:
                    board.remove_card(fx, fy)
                    board.remove_card(x, y)
                except AssertionError as e:
                    # If removal fails, flip both back face-down
                    print(f"  ✗ Removal failed: {e}")
                    board.flip_card(fx, fy)
                    board.flip_card(x, y)
                    first_card_pos = None
                    continue

                matched_pairs += 1
                print(f"  Matched pairs: {matched_pairs}/{total_pairs}")

            else:
                # No match
                print(f"  ✗ No match. {first_card} ≠ {second_card}")
                board.flip_card(fx, fy)
                board.flip_card(x, y)

            first_card_pos = None

        print()

    print(f"\n🎉 Game completed in {move_count} moves!")
    print(f"   Matched all {matched_pairs} pairs!")


def main():
    """Run simulation with example parameters."""
    print("=== Memory Scramble Single-Player Simulation ===\n")

    # Run simulation with 2x4 board (4 card types)
    width, height = 2, 4
    num_cards = 4

    try:
        import asyncio
        asyncio.run(simulate_single_player(width, height, num_cards))
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")


if __name__ == "__main__":
    main()
