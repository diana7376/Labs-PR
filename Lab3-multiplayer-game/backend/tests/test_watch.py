"""Test the watch() function for board change notifications."""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.game.board import Board
from src.commands.commands import GameManager


async def test_watch_basic():
    """Test that watch() waits for a change."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)
    game = GameManager(board)

    # Start watching in background
    watch_task = asyncio.create_task(game.watch("player_1"))

    # Give watch time to start
    await asyncio.sleep(0.01)

    # Make a change - flip a card
    await game.flip("player_2", 0, 0)

    # Watch should now complete
    result = await watch_task

    assert result["ok"], "Watch failed"
    assert len(result["board"]) == 4, "Board size wrong"

    print("✅ test_watch_basic PASSED")


async def test_watch_multiple_watchers():
    """Test that multiple watchers all get notified."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)
    game = GameManager(board)

    # Start multiple watchers
    watch1 = asyncio.create_task(game.watch("player_1"))
    watch2 = asyncio.create_task(game.watch("player_2"))
    watch3 = asyncio.create_task(game.watch("player_3"))

    await asyncio.sleep(0.01)

    # Make ONE change
    await game.flip("player_4", 1, 1)

    # All watchers should complete
    results = await asyncio.gather(watch1, watch2, watch3)

    assert all(r["ok"] for r in results), "Some watchers failed"
    print("✅ test_watch_multiple_watchers PASSED")


async def test_watch_no_change_blocks():
    """Test that watch() blocks if no change occurs."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)
    game = GameManager(board)

    # Start watching
    watch_task = asyncio.create_task(game.watch("player_1"))

    await asyncio.sleep(0.05)

    # Watch should still be waiting
    assert not watch_task.done(), "Watch completed without change"

    # Cancel the watch
    watch_task.cancel()

    print("✅ test_watch_no_change_blocks PASSED")


async def test_watch_with_map():
    """Test that watch() detects map() changes."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)

    # Start watching
    watch_task = asyncio.create_task(board.wait_for_change())

    await asyncio.sleep(0.01)

    # Transform cards
    async def add_suffix(card):
        return card + "1"

    await board.map_cards("player_1", add_suffix)

    # Watch should complete
    result = await watch_task
    assert result["ok"], "Watch failed"

    print("✅ test_watch_with_map PASSED")


if __name__ == "__main__":
    print("\n🧪 Running watch tests...\n")

    try:
        asyncio.run(test_watch_basic())
        asyncio.run(test_watch_multiple_watchers())
        asyncio.run(test_watch_no_change_blocks())
        asyncio.run(test_watch_with_map())

        print("\n✅ ALL WATCH TESTS PASSED!")
        print("✅ TASK 5 (watch) IS COMPLETE!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
