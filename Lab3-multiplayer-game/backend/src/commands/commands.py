"""
Commands module for Memory Scramble - MIT 6.102 PS4 specification.
"""

from typing import Dict, Optional, Callable, Any
import asyncio
from src.game.board import Board


# ==================== PLAYER STATE ====================

class PlayerState:
    def __init__(self):
        self.first_card: Optional[tuple[int, int, str]] = None
        self.second_card: Optional[tuple[int, int, str]] = None

    def has_no_cards(self) -> bool:
        return self.first_card is None and self.second_card is None

    def has_one_card(self) -> bool:
        return self.first_card is not None and self.second_card is None

    def has_two_cards(self) -> bool:
        return self.first_card is not None and self.second_card is not None

    def cards_match(self) -> bool:
        if not self.has_two_cards():
            return False
        return self.first_card[2] == self.second_card[2]

    def reset(self):
        self.first_card = None
        self.second_card = None


_player_states: Dict[tuple, PlayerState] = {}


def _get_player_state(board: Board, player_id: str) -> PlayerState:
    key = (id(board), player_id)
    if key not in _player_states:
        _player_states[key] = PlayerState()
    return _player_states[key]


# ==================== STANDALONE FUNCTIONS ====================

async def look(board: Board, player_id: str) -> str:
    return board.get_state_string(player_id)


async def flip(board: Board, player_id: str, row: int, column: int) -> str:
    """Flips card following MIT PS4 rules."""
    player_state = _get_player_state(board, player_id)

    # RULE 3: Cleanup if we have two cards
    if player_state.has_two_cards():
        await _cleanup_previous_move(board, player_state)

    x, y = column, row

    if x < 0 or x >= board.width or y < 0 or y >= board.height:
        raise ValueError(f"Position ({row}, {column}) out of bounds")

    space = board.get_space(x, y)

    # RULE 1-A / 2-A: No card → FAIL
    if space.card is None:
        if player_state.has_one_card():
            x1, y1, _ = player_state.first_card
            board.remove_control(x1, y1)
            player_state.reset()
        raise ValueError(f"No card at position ({row}, {column})")

    if player_state.has_no_cards():
        return await _flip_first_card(board, player_id, player_state, x, y, space)
    elif player_state.has_one_card():
        return await _flip_second_card(board, player_id, player_state, x, y, space)
    else:
        raise RuntimeError("Invalid state")


async def _flip_first_card(board: Board, player_id: str, player_state: PlayerState,
                           x: int, y: int, space) -> str:
    """RULE 1."""
    # RULE 1-D: Block if controlled by another
    while space.controlled_by and space.controlled_by != player_id:
        await asyncio.sleep(0.01)
        space = board.get_space(x, y)
        # Check if card was removed while waiting
        if space.card is None:
            raise ValueError(f"Card was removed while waiting")

    # RULE 1-B: Flip if face-down
    if not space.is_face_up:
        board.flip_card(x, y)

    board.set_control(x, y, player_id)
    player_state.first_card = (x, y, board.get_card(x, y))

    return board.get_state_string(player_id)


async def _flip_second_card(board: Board, player_id: str, player_state: PlayerState,
                            x: int, y: int, space) -> str:
    """RULE 2."""
    # RULE 2-B: Controlled → FAIL
    if space.controlled_by is not None:
        x1, y1, _ = player_state.first_card
        board.remove_control(x1, y1)
        player_state.reset()
        raise ValueError(f"Card at ({y}, {x}) is already controlled")

    # RULE 2-C: Flip if face-down
    if not space.is_face_up:
        board.flip_card(x, y)

    board.set_control(x, y, player_id)
    player_state.second_card = (x, y, board.get_card(x, y))

    # RULE 2-D/E: Keep control if match, release if no match
    if not player_state.cards_match():
        x1, y1, _ = player_state.first_card
        x2, y2, _ = player_state.second_card
        board.remove_control(x1, y1)
        board.remove_control(x2, y2)

    return board.get_state_string(player_id)


async def _cleanup_previous_move(board: Board, player_state: PlayerState):
    """RULE 3: Cleanup."""
    if not player_state.has_two_cards():
        return

    x1, y1, card1 = player_state.first_card
    x2, y2, card2 = player_state.second_card

    space1 = board.get_space(x1, y1)
    space2 = board.get_space(x2, y2)

    # Skip if already cleaned
    if space1.card is None and space2.card is None:
        player_state.reset()
        return

    if player_state.cards_match():
        # RULE 3-A: Remove matched
        if space1.card is not None:
            if not space1.is_face_up:
                board.flip_card(x1, y1)
            if space1.controlled_by:
                board.remove_control(x1, y1)
            board.remove_card(x1, y1)

        if space2.card is not None:
            if not space2.is_face_up:
                board.flip_card(x2, y2)
            if space2.controlled_by:
                board.remove_control(x2, y2)
            board.remove_card(x2, y2)
    else:
        # RULE 3-B: Flip down unmatched
        if space1.card and space1.is_face_up and not space1.controlled_by:
            board.flip_card(x1, y1)
        if space2.card and space2.is_face_up and not space2.controlled_by:
            board.flip_card(x2, y2)

    player_state.reset()


async def map(board: Board, player_id: str, f: Callable[[str], str]) -> str:
    await board.map_cards(player_id, f)
    return board.get_state_string(player_id)


async def watch(board: Board, player_id: str) -> str:
    await board.wait_for_change()
    return board.get_state_string(player_id)


# ==================== GAMEMANAGER CLASS ====================

class GameManager:
    """Manages game session with JSON responses."""

    def __init__(self, board: Board) -> None:
        self.board = board
        self.scores: Dict[str, int] = {}

    async def look(self, player_id: str) -> Dict[str, Any]:
        """Get board state as JSON."""
        return {
            "ok": True,
            "width": self.board.width,
            "height": self.board.height,
            "board": self._serialize_board(),
            "scores": self.scores
        }

    async def flip(self, player_id: str, row: int, column: int) -> Dict[str, Any]:
        try:
            # Perform the flip, which includes calls to cleanup previous matches
            await flip(self.board, player_id, row, column)

            # Immediately check if the game is over after applying flip and cleanup
            game_over = self.is_game_over()

            return {
                "ok": True,
                "board": self._serialize_board(),
                "scores": self.scores,
                "game_over": game_over
            }
        except Exception as e:
            return {
                "ok": False,
                "message": str(e)
            }

    async def watch(self, player_id: str) -> Dict[str, Any]:
        """Wait for board change and return new state."""
        try:
            await watch(self.board, player_id)
            return {
                "ok": True,
                "board": self._serialize_board()
            }
        except Exception as e:
            return {
                "ok": False,
                "message": str(e)
            }

    def _serialize_board(self) -> list:
        """Convert board to JSON format."""
        result = []
        for y in range(self.board.height):
            row = []
            for x in range(self.board.width):
                space = self.board.get_space(x, y)
                row.append({
                    "card": space.card,
                    "is_face_up": space.is_face_up,
                    "controlled_by": space.controlled_by
                })
            result.append(row)
        return result

    def is_game_over(self) -> bool:
        for y in range(self.board.height):
            for x in range(self.board.width):
                if self.board.get_space(x, y).card is not None:
                    return False
        return True
