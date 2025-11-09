"""
Tests for commands module.
Verifies that commands are simple glue code.
"""

import pytest
import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.board import Board
from src.commands.commands import GameManager


class TestGameManager:
    """Test GameManager (commands module)."""

    @pytest.fixture
    def game(self):
        """Create a test game."""
        cards = {"A", "B", "C", "D"}
        board = Board(2, 4, cards)
        return GameManager(board)

    @pytest.mark.asyncio
    async def test_look_returns_board_state(self, game):
        """Test look() returns serialized board."""
        result = await game.look("Player1")

        assert result["ok"] == True
        assert result["width"] == 2
        assert result["height"] == 4
        assert len(result["board"]) == 4
        assert len(result["board"][0]) == 2

    @pytest.mark.asyncio
    async def test_look_includes_scores(self, game):
        """Test look() includes scores."""
        result = await game.look("Player1")

        assert "scores" in result
        assert isinstance(result["scores"], dict)

    @pytest.mark.asyncio
    async def test_flip_face_down_card(self, game):
        """Test flipping a face-down card."""
        result = await game.flip("Player1", 0, 0)

        assert result["ok"] == True
        assert "board" in result  # Check board is returned
        assert result["board"][0][0]["is_face_up"] == True
        assert result["board"][0][0]["controlled_by"] == "Player1"

    @pytest.mark.asyncio
    async def test_flip_empty_space_fails(self, game):
        """Test flipping empty space returns error."""
        # Remove a card
        game.board.flip_card(0, 0)
        game.board.set_control(0, 0, "Player1")
        game.board.remove_card(0, 0)

        # Try to flip
        result = await game.flip("Player1", 0, 0)

        assert result["ok"] == False
        assert "No card" in result["message"]

    @pytest.mark.asyncio
    async def test_flip_already_controlled_card_fails(self, game):
        """Test flipping card controlled by another player fails."""
        # Player 1 flips
        result1 = await game.flip("Player1", 0, 0)
        assert result1["ok"] == True, "Player1 should successfully flip"

        # Player 2 tries to flip same card
        result2 = await game.flip("Player2", 0, 0)

        assert result2["ok"] == False
        # Check for either "already controlled" OR "controlled by"
        assert ("already controlled" in result2["message"].lower() or
                "controlled by" in result2["message"].lower())

    def test_serialize_board(self, game):
        """Test board serialization."""
        board_json = game._serialize_board()

        assert isinstance(board_json, list)
        assert len(board_json) == 4
        assert all(isinstance(row, list) for row in board_json)
        assert all(len(row) == 2 for row in board_json)
        assert all("card" in cell for row in board_json for cell in row)
        assert all("is_face_up" in cell for row in board_json for cell in row)
        assert all("controlled_by" in cell for row in board_json for cell in row)
