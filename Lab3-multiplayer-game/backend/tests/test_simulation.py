"""
Automated tests for single-player simulation.

Tests that the Board ADT works correctly in realistic gameplay scenarios
without concurrency issues.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.board import Board


class TestSimulation:
    """Test single-player gameplay scenarios."""

    def test_simple_game_2x2(self):
        """Test a simple 2x2 board (2 pairs)."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        # Verify initial state
        assert not board.is_face_up(0, 0)
        assert not board.is_face_up(0, 1)
        board.check_rep()

        # Find matching A cards
        a_positions = []
        for y in range(2):
            for x in range(2):
                if board.get_card(x, y) == "A":
                    a_positions.append((x, y))

        # Flip first A card
        x1, y1 = a_positions[0]
        board.flip_card(x1, y1)
        board.set_control(x1, y1, "Player1")
        assert board.is_face_up(x1, y1)

        # Flip second A card (should match)
        x2, y2 = a_positions[1]
        board.flip_card(x2, y2)
        board.set_control(x2, y2, "Player1")
        assert board.is_face_up(x2, y2)

        # Verify they match
        assert board.get_card(x1, y1) == board.get_card(x2, y2)

        # Both should be controlled
        assert board.get_controller(x1, y1) == "Player1"
        assert board.get_controller(x2, y2) == "Player1"

        board.check_rep()

    def test_medium_game_4x4(self):
        """Test a 4x4 board with 8 pairs."""
        cards = {f"Card{i}" for i in range(8)}
        board = Board(4, 4, cards)

        # Verify board initialization
        board.check_rep()
        assert board.width == 4
        assert board.height == 4

        # All cards should be face-down initially
        for y in range(4):
            for x in range(4):
                assert not board.is_face_up(x, y), f"Card at ({x},{y}) should be face-down"
                assert board.get_controller(x, y) is None, f"Card at ({x},{y}) should not be controlled"

        # Simulate flipping some cards
        board.flip_card(0, 0)
        board.set_control(0, 0, "Player1")
        assert board.is_face_up(0, 0)

        board.flip_card(1, 0)
        board.set_control(1, 0, "Player1")
        assert board.is_face_up(1, 0)

        # Check if they match (won't always, due to randomness)
        card1 = board.get_card(0, 0)
        card2 = board.get_card(1, 0)

        if card1 == card2:
            # They match, remove them
            board.remove_card(0, 0)
            board.remove_card(1, 0)
            assert board.get_card(0, 0) is None
            assert board.get_card(1, 0) is None
        else:
            # They don't match, flip back
            board.flip_card(0, 0)
            board.flip_card(1, 0)
            assert not board.is_face_up(0, 0)
            assert not board.is_face_up(1, 0)

        board.check_rep()

    def test_control_and_flip_interaction(self):
        """Test that control is released when flipping face-down."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        # Flip and control a card
        board.flip_card(0, 0)
        board.set_control(0, 0, "Player1")
        assert board.is_face_up(0, 0)
        assert board.get_controller(0, 0) == "Player1"

        # Flip it back face-down
        board.flip_card(0, 0)

        # Control should be released
        assert not board.is_face_up(0, 0)
        assert board.get_controller(0, 0) is None

        board.check_rep()

    def test_multiple_cards_sequence(self):
        """Test flipping many cards in sequence."""
        cards = {f"C{i}" for i in range(8)}
        board = Board(4, 4, cards)

        positions = [(x, y) for x in range(4) for y in range(4)]

        # Flip first 4 cards and track them
        flipped_cards = []
        for i in range(4):
            x, y = positions[i]
            board.flip_card(x, y)
            board.set_control(x, y, f"Player{i % 2}")
            flipped_cards.append(board.get_card(x, y))
            assert board.is_face_up(x, y)

        board.check_rep()

        # Verify all cards are different or some might match
        # (depends on random shuffle)
        print(f"Flipped cards: {flipped_cards}")

    def test_board_integrity_after_operations(self):
        """Test that board rep is always valid after operations."""
        cards = {f"X{i}" for i in range(5)}
        board = Board(5, 2, cards)

        operations = [
            ("flip", 0, 0),
            ("control", 0, 0, "P1"),
            ("flip", 0, 0),  # Flip back, should release control
            ("flip", 1, 0),
            ("control", 1, 0, "P2"),
            ("remove", 1, 0),
            ("flip", 2, 0),
            ("control", 2, 0, "P1"),
        ]

        try:
            for op in operations:
                if op[0] == "flip":
                    board.flip_card(op[1], op[2])
                elif op[0] == "control":
                    board.set_control(op[1], op[2], op[3])
                elif op[0] == "remove":
                    board.remove_card(op[1], op[2])

                # Verify board is always in valid state
                board.check_rep()
        except Exception as e:
            pytest.fail(f"Board operation failed: {e}")
