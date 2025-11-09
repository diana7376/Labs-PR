"""
Test suite for MIT 6.102 PS4 Memory Scramble Game Rules.
"""

import pytest
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.game.board import Board
from src.commands.commands import flip, look, _player_states


@pytest.fixture(autouse=True)
def clear_state():
    """Clear player state before each test."""
    global _player_states
    _player_states.clear()
    yield
    _player_states.clear()


# ==================== RULE 1 TESTS ====================

@pytest.mark.asyncio
async def test_rule_1a_no_card_fails():
    """RULE 1-A: No card at position fails."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    board.flip_card(0, 0)
    board.set_control(0, 0, "setup")
    board.remove_card(0, 0)

    with pytest.raises(ValueError, match="No card"):
        await flip(board, "player1", 0, 0)


@pytest.mark.asyncio
async def test_rule_1b_flip_face_down_card():
    """RULE 1-B: Face-down card turns face-up."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    await flip(board, "player1", 0, 0)

    space = board.get_space(0, 0)
    assert space.is_face_up
    assert space.controlled_by == "player1"


@pytest.mark.asyncio
async def test_rule_1c_take_control_of_face_up_uncontrolled():
    """RULE 1-C: Take control of face-up uncontrolled card."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Find two different cards
    a_pos = None
    b_pos = None
    for y in range(2):
        for x in range(2):
            card = board.get_card(x, y)
            if card == "A" and a_pos is None:
                a_pos = (x, y)
            elif card == "B" and b_pos is None:
                b_pos = (x, y)

    # Player1 flips A, then B (no match) - both become uncontrolled
    await flip(board, "player1", a_pos[1], a_pos[0])
    await flip(board, "player1", b_pos[1], b_pos[0])

    assert board.is_face_up(a_pos[0], a_pos[1])
    assert board.get_space(a_pos[0], a_pos[1]).controlled_by is None

    # Player2 flips face-up uncontrolled A - should take control
    await flip(board, "player2", a_pos[1], a_pos[0])

    space = board.get_space(a_pos[0], a_pos[1])
    assert space.is_face_up
    assert space.controlled_by == "player2"


@pytest.mark.asyncio
async def test_rule_1d_blocking_when_controlled():
    """RULE 1-D: Block when another player controls card."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Player1 flips and controls a card
    await flip(board, "player1", 0, 0)
    assert board.get_space(0, 0).controlled_by == "player1"

    # Player2 attempts to flip the same controlled card - should block
    started = False
    completed = False

    async def try_controlled_card():
        nonlocal started, completed
        started = True
        await flip(board, "player2", 0, 0)
        completed = True

    task = asyncio.create_task(try_controlled_card())
    await asyncio.sleep(0.05)

    # Verify blocking occurred
    assert started, "Player2 should have started"
    assert not completed, "Player2 should be blocked"
    assert not task.done(), "Task should be running (blocked)"

    # Cleanup
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ==================== RULE 2 TESTS ====================

@pytest.mark.asyncio
async def test_rule_2a_second_card_no_card_fails():
    """RULE 2-A: Second card on empty space fails."""
    cards = {"A", "B", "C"}
    board = Board(2, 3, cards)

    # Flip first card
    await flip(board, "player1", 0, 0)

    # Manually remove a different card
    board.flip_card(1, 0)
    board.set_control(1, 0, "setup")
    board.remove_card(1, 0)

    # Try to flip removed card as second - should fail
    with pytest.raises(ValueError, match="No card"):
        await flip(board, "player1", 0, 1)

    # First card should be released
    assert board.get_space(0, 0).controlled_by is None


@pytest.mark.asyncio
async def test_rule_2b_second_card_controlled_fails():
    """RULE 2-B: Second card controlled fails."""
    cards = {"A", "B", "C"}
    board = Board(2, 3, cards)

    # Player1 flips first card at (0,0)
    await flip(board, "player1", 0, 0)

    # Player2 flips a DIFFERENT card at (0,1)
    await flip(board, "player2", 0, 1)

    # Player1 tries to flip player2's controlled card at (0,1) as their second - should fail
    with pytest.raises(ValueError, match="controlled"):
        await flip(board, "player1", 0, 1)

    # Player1's first card should be released
    assert board.get_space(0, 0).controlled_by is None


@pytest.mark.asyncio
async def test_rule_2c_second_card_face_down_flips_up():
    """RULE 2-C: Second face-down card turns face-up."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Find first card position
    first_pos = (0, 0)

    # Find a DIFFERENT card position for second flip
    second_pos = None
    for y in range(2):
        for x in range(2):
            if (x, y) != first_pos:
                second_pos = (x, y)
                break
        if second_pos:
            break

    # Flip first card
    await flip(board, "player1", first_pos[1], first_pos[0])

    # Second card should be face-down
    assert not board.is_face_up(second_pos[0], second_pos[1]), "Second card should start face-down"

    # Flip second card
    await flip(board, "player1", second_pos[1], second_pos[0])

    # Second card should now be face-up
    assert board.is_face_up(second_pos[0], second_pos[1]), "Second card should be face-up after flip"


@pytest.mark.asyncio
async def test_rule_2d_matching_cards_stay_controlled():
    """RULE 2-D: Matching cards stay controlled."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Find both A cards
    a_positions = []
    for y in range(2):
        for x in range(2):
            if board.get_card(x, y) == "A":
                a_positions.append((x, y))

    # Flip both A cards
    await flip(board, "player1", a_positions[0][1], a_positions[0][0])
    await flip(board, "player1", a_positions[1][1], a_positions[1][0])

    # Both should be controlled
    assert board.get_space(a_positions[0][0], a_positions[0][1]).controlled_by == "player1"
    assert board.get_space(a_positions[1][0], a_positions[1][1]).controlled_by == "player1"


@pytest.mark.asyncio
async def test_rule_2e_non_matching_cards_released():
    """RULE 2-E: Non-matching cards released."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Find A and B
    a_pos = None
    b_pos = None
    for y in range(2):
        for x in range(2):
            card = board.get_card(x, y)
            if card == "A" and a_pos is None:
                a_pos = (x, y)
            elif card == "B" and b_pos is None:
                b_pos = (x, y)

    # Flip A and B (no match)
    await flip(board, "player1", a_pos[1], a_pos[0])
    await flip(board, "player1", b_pos[1], b_pos[0])

    # Both face-up but not controlled
    assert board.is_face_up(a_pos[0], a_pos[1])
    assert board.is_face_up(b_pos[0], b_pos[1])
    assert board.get_space(a_pos[0], a_pos[1]).controlled_by is None
    assert board.get_space(b_pos[0], b_pos[1]).controlled_by is None


# ==================== RULE 3 TESTS ====================

@pytest.mark.asyncio
async def test_rule_3a_matched_cards_removed():
    """RULE 3-A: Matched cards removed on new move."""
    cards = {"A", "B"}
    board = Board(2, 2, cards)

    # Find A cards
    a_positions = []
    for y in range(2):
        for x in range(2):
            if board.get_card(x, y) == "A":
                a_positions.append((x, y))

    # Match A cards
    await flip(board, "player1", a_positions[0][1], a_positions[0][0])
    await flip(board, "player1", a_positions[1][1], a_positions[1][0])

    # Find B card
    b_positions = []
    for y in range(2):
        for x in range(2):
            if board.get_card(x, y) == "B":
                b_positions.append((x, y))

    # Start new move - should remove A cards
    await flip(board, "player1", b_positions[0][1], b_positions[0][0])

    # A cards should be removed
    assert board.get_card(a_positions[0][0], a_positions[0][1]) is None
    assert board.get_card(a_positions[1][0], a_positions[1][1]) is None


@pytest.mark.asyncio
async def test_rule_3b_unmatched_cards_flipped_down():
    """RULE 3-B: Unmatched cards flip down on new move."""
    cards = {"A", "B", "C"}
    board = Board(3, 2, cards)

    # Find A, B, C
    a_pos = b_pos = c_pos = None
    for y in range(2):
        for x in range(3):
            card = board.get_card(x, y)
            if card == "A" and a_pos is None:
                a_pos = (x, y)
            elif card == "B" and b_pos is None:
                b_pos = (x, y)
            elif card == "C" and c_pos is None:
                c_pos = (x, y)

    # Flip A and B (no match)
    await flip(board, "player1", a_pos[1], a_pos[0])
    await flip(board, "player1", b_pos[1], b_pos[0])

    # Both face-up
    assert board.is_face_up(a_pos[0], a_pos[1])
    assert board.is_face_up(b_pos[0], b_pos[1])

    # Start new move with C
    await flip(board, "player1", c_pos[1], c_pos[0])

    # A and B should be face-down
    assert not board.is_face_up(a_pos[0], a_pos[1])
    assert not board.is_face_up(b_pos[0], b_pos[1])


@pytest.mark.asyncio
async def test_rule_3b_doesnt_flip_controlled_cards():
    """RULE 3-B: Cleanup doesn't flip controlled cards."""
    cards = {"A", "B", "C"}
    board = Board(3, 2, cards)

    # Find positions
    a_pos = b_pos = c_pos = None
    for y in range(2):
        for x in range(3):
            card = board.get_card(x, y)
            if card == "A" and a_pos is None:
                a_pos = (x, y)
            elif card == "B" and b_pos is None:
                b_pos = (x, y)
            elif card == "C" and c_pos is None:
                c_pos = (x, y)

    # Player1 flips A and B (no match)
    await flip(board, "player1", a_pos[1], a_pos[0])
    await flip(board, "player1", b_pos[1], b_pos[0])

    # Player2 takes control of A
    await flip(board, "player2", a_pos[1], a_pos[0])

    # Player1 starts new move
    await flip(board, "player1", c_pos[1], c_pos[0])

    # A should stay face-up (controlled by player2)
    assert board.is_face_up(a_pos[0], a_pos[1])
    # B should be face-down
    assert not board.is_face_up(b_pos[0], b_pos[1])


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_complete_game_flow():
    """Complete game flow test."""
    cards = {"🦄", "🌈"}
    board = Board(2, 2, cards)

    positions = {}
    for y in range(2):
        for x in range(2):
            card = board.get_card(x, y)
            if card not in positions:
                positions[card] = []
            positions[card].append((x, y))

    # Match unicorns
    unicorn_pos = positions["🦄"]
    await flip(board, "player1", unicorn_pos[0][1], unicorn_pos[0][0])
    await flip(board, "player1", unicorn_pos[1][1], unicorn_pos[1][0])

    # Start new move - unicorns should be removed
    rainbow_pos = positions["🌈"]
    await flip(board, "player1", rainbow_pos[0][1], rainbow_pos[0][0])

    assert board.get_card(unicorn_pos[0][0], unicorn_pos[0][1]) is None
    assert board.get_card(unicorn_pos[1][0], unicorn_pos[1][1]) is None


@pytest.mark.asyncio
async def test_concurrent_players_with_rules():
    """Concurrent players test."""
    cards = {"A", "B", "C", "D"}
    board = Board(4, 2, cards)

    async def player1_moves():
        await flip(board, "player1", 0, 0)
        await asyncio.sleep(0.01)
        await flip(board, "player1", 0, 1)

    async def player2_moves():
        await asyncio.sleep(0.005)
        await flip(board, "player2", 1, 0)
        await asyncio.sleep(0.01)
        await flip(board, "player2", 1, 1)

    await asyncio.gather(player1_moves(), player2_moves())
    board.check_rep()
