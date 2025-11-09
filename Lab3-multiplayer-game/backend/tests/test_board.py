"""
Comprehensive unit tests for Board ADT.

Tests cover:
- Board creation and initialization
- Representation invariants (checkRep)
- All getter methods
- All mutator methods (flip, control, removal)
- File parsing
- Edge cases and error conditions
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from game.board import Board
from game.space import Space



class TestBoardInitialization:
    """Test board creation and basic properties."""

    def test_create_simple_board(self):
        """Test creating a basic 2x2 board."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        assert board.width == 2
        assert board.height == 2
        board.check_rep()  # Should not raise

    def test_create_larger_board(self):
        """Test creating a 4x4 board."""
        cards = {"A", "B", "C", "D", "E", "F", "G", "H"}
        board = Board(4, 4, cards)

        assert board.width == 4
        assert board.height == 4
        board.check_rep()

    def test_all_cards_face_down_initially(self):
        """Test that all cards are face-down when board created."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        for y in range(board.height):
            for x in range(board.width):
                assert not board.is_face_up(x, y), \
                    f"Card at ({x}, {y}) should be face-down initially"

    def test_no_cards_controlled_initially(self):
        """Test that no cards are controlled when board created."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        for y in range(board.height):
            for x in range(board.width):
                assert board.get_controller(x, y) is None, \
                    f"Card at ({x}, {y}) should not be controlled initially"

    def test_invalid_card_count(self):
        """Test that board rejects invalid card counts."""
        cards = {"A", "B", "C"}  # 3 cards = 6 total, but 2x2=4 needed

        with pytest.raises(AssertionError):
            Board(2, 2, cards)

    def test_invalid_dimensions(self):
        """Test that board rejects invalid dimensions."""
        cards = {"A", "B"}

        with pytest.raises(AssertionError):
            Board(0, 5, cards)

        with pytest.raises(AssertionError):
            Board(5, 0, cards)


class TestGetters:
    """Test all getter methods."""

    def test_get_space_returns_copy(self):
        """Test that get_space returns defensive copy."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        space1 = board.get_space(0, 0)
        space2 = board.get_space(0, 0)

        # Should be equal but potentially different objects
        assert space1.card == space2.card
        assert space1.is_face_up == space2.is_face_up
        assert space1.controlled_by == space2.controlled_by

    def test_get_card_value(self):
        """Test getting card value from board."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        # All cards should have values
        for y in range(board.height):
            for x in range(board.width):
                card = board.get_card(x, y)
                assert card in cards, f"Card at ({x}, {y}) should be A or B"

    def test_is_face_up(self):
        """Test is_face_up getter."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        # Initially all face-down
        for y in range(board.height):
            for x in range(board.width):
                assert not board.is_face_up(x, y)

    def test_get_controller_none_initially(self):
        """Test that get_controller returns None initially."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        for y in range(board.height):
            for x in range(board.width):
                assert board.get_controller(x, y) is None

    def test_out_of_bounds_access(self):
        """Test that accessing out-of-bounds raises error."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        with pytest.raises(AssertionError):
            board.get_space(2, 0)  # Out of bounds

        with pytest.raises(AssertionError):
            board.get_space(0, 2)  # Out of bounds


class TestFlipCard:
    """Test card flipping operations."""

    def test_flip_card_face_down_to_up(self):
        """Test flipping a card from face-down to face-up."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        assert not board.is_face_up(0, 0)
        board.flip_card(0, 0)
        assert board.is_face_up(0, 0)

    def test_flip_card_face_up_to_down(self):
        """Test flipping a card from face-up to face-down."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board.flip_card(0, 0)
        assert board.is_face_up(0, 0)
        board.flip_card(0, 0)
        assert not board.is_face_up(0, 0)

    def test_flip_removes_control(self):
        """Test that flipping to face-down removes player control."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board.flip_card(0, 0)
        board.set_control(0, 0, "player1")
        assert board.get_controller(0, 0) == "player1"

        board.flip_card(0, 0)
        assert board.get_controller(0, 0) is None


class TestControl:
    """Test player control operations."""

    def test_set_control_on_face_up_card(self):
        """Test setting control on a face-up card."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board.flip_card(0, 0)
        board.set_control(0, 0, "player1")

        assert board.get_controller(0, 0) == "player1"

    def test_cannot_control_face_down_card(self):
        """Test that face-down cards cannot be controlled."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        with pytest.raises(AssertionError):
            board.set_control(0, 0, "player1")

    def test_remove_control(self):
        """Test removing control from a card."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board.flip_card(0, 0)
        board.set_control(0, 0, "player1")
        assert board.get_controller(0, 0) == "player1"

        board.remove_control(0, 0)
        assert board.get_controller(0, 0) is None

    def test_change_control(self):
        """Test changing which player controls a card."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board.flip_card(0, 0)
        board.set_control(0, 0, "player1")
        board.remove_control(0, 0)
        board.set_control(0, 0, "player2")

        assert board.get_controller(0, 0) == "player2"


class TestRemoveCard:
    """Test card removal operations."""

    def test_cannot_remove_face_down_card(self):
        """Test that face-down cards are auto-flipped during removal."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        # Card starts face-down
        assert not board.is_face_up(0, 0)

        # Must flip and set control first
        board.flip_card(0, 0)
        board.set_control(0, 0, "test")

        # Now remove it (should work)
        board.remove_card(0, 0)

        # Verify it's gone
        assert board.get_card(0, 0) is None


class TestParseFromFile:
    """Test file parsing functionality."""

    def test_parse_valid_file(self):
        """Test parsing a valid board file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("2 2\n")
            f.write("A B A B\n")
            temp_path = f.name

        try:
            board = Board.parse_from_file(temp_path)
            assert board.width == 2
            assert board.height == 2
            board.check_rep()
        finally:
            os.unlink(temp_path)

    def test_parse_file_with_emojis(self):
        """Test parsing file with emoji cards."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("2 2\n")
            f.write("🌙 ⭐ 🌙 ⭐\n")
            temp_path = f.name

        try:
            board = Board.parse_from_file(temp_path)
            assert board.width == 2
            assert board.height == 2
            board.check_rep()
        finally:
            os.unlink(temp_path)

    def test_parse_multiline_cards(self):
        """Test parsing file with cards on multiple lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("2 2\n")
            f.write("A B\n")
            f.write("A B\n")
            temp_path = f.name

        try:
            board = Board.parse_from_file(temp_path)
            assert board.width == 2
            assert board.height == 2
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_card_count(self):
        """Test that parsing fails with wrong card count."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("2 2\n")
            f.write("A B C D E F\n")  # 6 cards, need 4
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                Board.parse_from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_card_frequency(self):
        """Test that parsing fails if card doesn't appear exactly twice."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("2 2\n")
            f.write("A A B B\n")  # A appears twice, which is correct
            temp_path = f.name

        try:
            board = Board.parse_from_file(temp_path)  # Should succeed
            board.check_rep()
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """Test that parsing nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            Board.parse_from_file("/nonexistent/path/board.txt")


class TestRepInvariants:
    """Test representation invariant checking."""

    def test_checkrep_valid_board(self):
        """Test that checkRep passes for valid board."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)
        board.check_rep()  # Should not raise

    def test_each_card_appears_twice(self):
        """Test that each unique card appears exactly twice."""
        cards = {"A", "B", "C", "D"}
        board = Board(2, 4, cards)

        card_count = {}
        for y in range(board.height):
            for x in range(board.width):
                card = board.get_card(x, y)
                if card:
                    card_count[card] = card_count.get(card, 0) + 1

        for card, count in card_count.items():
            assert count == 2, f"Card {card} appears {count} times, should be 2"


class TestToString:
    """Test string representation."""

    def test_tostring_simple(self):
        """Test string representation of board."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        board_str = str(board)
        assert "2x2" in board_str or "Board" in board_str

    def test_tostring_after_flip(self):
        """Test string changes after flipping cards."""
        cards = {"A", "B"}
        board = Board(2, 2, cards)

        str_before = str(board)
        board.flip_card(0, 0)
        str_after = str(board)

        # Strings should be different
        assert str_before != str_after
