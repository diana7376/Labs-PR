"""Test the map() function for concurrent transformation."""

import asyncio
import pytest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.game.board import Board
from src.commands.commands import GameManager


@pytest.mark.asyncio
async def test_map_basic():
    """Test basic map transformation with valid card pairs."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)

    async def double_card(card):
        """Transform each card by doubling it."""
        await asyncio.sleep(0.001)
        return card + card

    result = await board.map_cards("player_1", double_card)

    # Check that transformation succeeded
    assert result["ok"], "Map operation failed"
    assert len(result["board"]) == 4, "Wrong board height"
    assert len(result["board"][0]) == 4, "Wrong board width"

    # Verify cards were transformed (doubled)
    transformed_count = 0
    for row in result["board"]:
        for space in row:
            if space["card"]:
                # Card should be doubled (2 chars)
                if len(space["card"]) == 2:
                    transformed_count += 1

    assert transformed_count == 16, f"Only {transformed_count} cards transformed, expected 16"
    print("✅ test_map_basic PASSED")


@pytest.mark.asyncio
async def test_map_identity():
    """Test that identity transformation leaves board unchanged."""
    cards = {"🦄", "🌈", "🎨", "⭐", "🎪", "🎭", "🎬", "🎸"}
    board = Board(4, 4, cards)

    # Store original state
    original_cards = set()
    for y in range(4):
        for x in range(4):
            space = board.get_space(x, y)
            if space.card:
                original_cards.add(space.card)

    async def identity_transform(card):
        """Identity transform: return same card."""
        await asyncio.sleep(0.01)
        return card

    result = await board.map_cards("player_1", identity_transform)

    # Verify result structure
    assert result["ok"], "Map operation failed"

    # Get transformed cards
    transformed_cards = set()
    for row in result["board"]:
        for space in row:
            if space["card"]:
                transformed_cards.add(space["card"])

    # Original and transformed should match
    assert original_cards == transformed_cards, "Cards changed after identity transform"
    print("✅ test_map_identity PASSED")


@pytest.mark.asyncio
async def test_map_emoji_transform():
    """Test map with emoji transformation."""
    cards = {"🦄", "🌈", "🎨", "⭐", "🎪", "🎭", "🎬", "🎸"}
    board = Board(4, 4, cards)

    # Create a mapping of cards
    emoji_map = {
        "🦄": "🌟",
        "🌈": "☀️",
        "🎨": "🎭",
        "⭐": "💫",
        "🎪": "🎡",
        "🎭": "🎬",
        "🎬": "🎤",
        "🎸": "🎹",
    }

    async def emoji_transform(card):
        """Transform emoji to different emoji."""
        await asyncio.sleep(0.005)
        return emoji_map.get(card, card)

    result = await board.map_cards("player_1", emoji_transform)

    # Verify transformation happened
    assert result["ok"], "Map operation failed"

    # Check that cards were transformed
    transformed = set()
    for row in result["board"]:
        for space in row:
            if space["card"]:
                transformed.add(space["card"])

    # All transformed cards should be in the emoji_map values
    expected_cards = set(emoji_map.values())
    assert transformed == expected_cards, f"Transformed cards {transformed} don't match expected {expected_cards}"
    print("✅ test_map_emoji_transform PASSED")


@pytest.mark.asyncio
async def test_map_concurrent_maps():
    """Test that two map() operations can run concurrently."""
    cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
    board = Board(4, 4, cards)

    async def add_suffix(card):
        """Add suffix to card."""
        await asyncio.sleep(0.02)
        return card + "1"

    async def add_prefix(card):
        """Add prefix to card."""
        await asyncio.sleep(0.02)
        return "X" + card

    # Run two maps concurrently on DIFFERENT boards
    board2 = Board(4, 4, cards)

    map1 = asyncio.create_task(board.map_cards("player_1", add_suffix))
    map2 = asyncio.create_task(board2.map_cards("player_2", add_prefix))

    result1 = await map1
    result2 = await map2

    assert result1["ok"], "First map failed"
    assert result2["ok"], "Second map failed"
    print("✅ test_map_concurrent_maps PASSED")


if __name__ == "__main__":
    print("\n🧪 Running map tests...\n")
    try:
        asyncio.run(test_map_basic())
        asyncio.run(test_map_identity())
        asyncio.run(test_map_emoji_transform())
        asyncio.run(test_map_concurrent_maps())

        print("\n✅ ALL MAP TESTS PASSED!")
        print("✅ TASK 4 (map) IS COMPLETE!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
