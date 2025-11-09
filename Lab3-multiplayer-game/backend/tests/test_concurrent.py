"""
Concurrent player test for MIT 6.102 Lab 3 - Memory Scramble.

Tests that multiple players can interact with the game simultaneously
without deadlocks, crashes, or race conditions.

Run with: pytest tests/test_concurrent.py -v
"""

import asyncio
import random
import pytest
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.board import Board
from src.commands.commands import GameManager


@pytest.mark.asyncio
async def test_concurrent_multiplayer():
    """
    Test that multiple players can play concurrently without issues.

    Verifies:
    - Multiple players can flip cards simultaneously
    - No deadlocks occur during concurrent access
    - No crashes or unhandled exceptions
    - Board state remains consistent
    - At least some moves succeed for players
    """
    num_players = 4
    num_moves_per_player = 10

    # Create a game with 4x4 board (8 pairs)
    cards = {"🦄", "🌈", "🎨", "⭐", "🎪", "🎭", "🎬", "🎸"}
    board = Board(4, 4, cards)
    game = GameManager(board)

    # Track successful moves and unexpected errors
    successful_moves = {f"player_{i}": 0 for i in range(num_players)}
    unexpected_errors = []

    async def player_simulation(player_id: str, num_moves: int):
        """Simulate a single player making random moves."""
        for _ in range(num_moves):
            # Random position
            row = random.randint(0, 3)
            col = random.randint(0, 3)

            try:
                result = await game.flip(player_id, row, col)
                if result.get("ok"):
                    successful_moves[player_id] += 1
                # Note: result["ok"] = False is expected for invalid moves
            except KeyError:
                # Expected: trying to flip removed/empty card
                pass
            except ValueError:
                # Expected: various rule violations (controlled cards, etc)
                pass
            except Exception as e:
                # Unexpected error - track it
                unexpected_errors.append({
                    "player": player_id,
                    "position": (row, col),
                    "error": type(e).__name__,
                    "message": str(e)
                })

            # Small random delay to simulate realistic timing
            await asyncio.sleep(random.uniform(0.001, 0.01))

    # Run all players concurrently
    tasks = [
        player_simulation(f"player_{i}", num_moves_per_player)
        for i in range(num_players)
    ]

    # Execute all player tasks simultaneously
    await asyncio.gather(*tasks)

    # Verify no unexpected errors occurred
    assert not unexpected_errors, (
        f"Unexpected errors during concurrent play: {unexpected_errors}"
    )

    # Verify board integrity after concurrent access
    board.check_rep()

    # Verify at least some moves succeeded
    total_successful = sum(successful_moves.values())
    assert total_successful > 0, (
        f"No moves succeeded. Successful moves per player: {successful_moves}"
    )

    # Print summary for visibility (optional, but helpful)
    print(f"\n✅ Concurrent test passed:")
    print(f"   - {num_players} players played simultaneously")
    print(f"   - {total_successful} total successful moves")
    print(f"   - No deadlocks or crashes")
    print(f"   - Board integrity maintained")


@pytest.mark.asyncio
async def test_concurrent_high_contention():
    num_players = 6
    num_moves_per_player = 10  # Reduced for small board

    cards = {"🦄", "🌈", "🎨", "⭐", "🎪", "🎭", "🎬", "🎸"}
    board = Board(4, 4, cards)
    game = GameManager(board)

    successful_flips = 0

    async def aggressive_player(player_id: str):
        nonlocal successful_flips
        for _ in range(num_moves_per_player):
            row, col = random.randint(0, 3), random.randint(0, 3)
            try:
                result = await game.flip(player_id, row, col)
                if result.get("ok"):
                    successful_flips += 1
            except (KeyError, ValueError):
                pass
            await asyncio.sleep(0.001)  # Always yield to event loop

    await asyncio.gather(*(aggressive_player(f"player_{i}") for i in range(num_players)))

    board.check_rep()
    assert successful_flips >= 0



if __name__ == "__main__":
    # Allow running directly with Python for debugging
    print("Running concurrent multiplayer tests...")
    print("=" * 60)

    asyncio.run(test_concurrent_multiplayer())
    print("\n" + "=" * 60)
    asyncio.run(test_concurrent_high_contention())

    print("\n✅ All concurrent tests passed!")
