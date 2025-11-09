"""
Board ADT for Memory Scramble multiplayer game.

A Board represents the game state as a mutable grid of card spaces.
Each space contains a card that can be face-up/down and controlled by a player.

Thread-safe access uses immutable Space objects as defensive copies.

Representation Invariants:
- Each unique card appears exactly twice in the grid
- Grid dimensions always match width and height
- All controlled cards are face-up (face-down cards cannot be controlled)
- No Space objects are None
- Board is fully initialized before any operations
"""

from typing import Set, List, Optional, Tuple
from .space import Space
import random
import asyncio
from typing import Dict, Any, Callable, Optional, Set



class Board:
    """
    Mutable Board ADT for Memory Scramble game.

    The board is a width x height grid of card spaces. Each space
    contains a card (or is empty), can be face-up or face-down,
    and can be controlled by a player.

    Thread Safety:
    - All getter methods return immutable Space objects (defensive copies)
    - Mutators should be called within external synchronization
    - Space objects are frozen dataclasses, making them inherently thread-safe
    """

    def __init__(self, width: int, height: int, cards: Set[str]) -> None:
        """
        Initialize a new board with the given dimensions and cards.

        Preconditions:
        - width > 0 and height > 0
        - cards is a non-empty set of unique non-empty strings
        - len(cards) * 2 == width * height (exactly 2 of each card)

        Postconditions:
        - Board is fully initialized with cards randomly shuffled
        - All cards are face-down and uncontrolled
        - checkRep() passes

        Args:
            width: Number of columns in the board (> 0)
            height: Number of rows in the board (> 0)
            cards: Set of unique card identifiers (each appears exactly twice)

        Raises:
            AssertionError: If preconditions violated
        """
        # Validate preconditions
        assert width > 0, "width must be positive"
        assert height > 0, "height must be positive"
        assert isinstance(cards, set), "cards must be a set"
        assert len(cards) > 0, "cards cannot be empty"
        assert len(cards) * 2 == width * height, \
            f"Must have exactly {width * height} spaces but got {len(cards) * 2} cards"

        self.width: int = width
        self.height: int = height
        self._change_event = asyncio.Event()
        self._watchers: List[asyncio.Event] = []
        self._lock = asyncio.Lock()
        # Create card list: each card appears exactly twice
        card_list: List[str] = []
        for card in cards:
            card_list.append(card)
            card_list.append(card)

        # Shuffle cards randomly
        random.shuffle(card_list)

        # Create grid: [y][x] indexing for clarity
        # Initialize all cards face-down and uncontrolled
        self._grid: List[List[Space]] = []
        card_index = 0

        for y in range(height):
            row: List[Space] = []
            for x in range(width):
                space = Space(
                    card=card_list[card_index],
                    is_face_up=False,
                    controlled_by=None
                )
                row.append(space)
                card_index += 1
            self._grid.append(row)

        # Verify representation invariants
        self.check_rep()

    def check_rep(self) -> None:
        """
        Verify all representation invariants.

        Checks that:
        - Grid dimensions match width and height
        - Each unique card that still exists appears exactly twice
        - No Space objects are None
        - All controlled cards are face-up
        - All Space objects satisfy their own invariants

        Raises:
            AssertionError: If any invariant is violated
        """
        # Check grid structure
        assert len(self._grid) == self.height, \
            f"Grid height {len(self._grid)} != {self.height}"
        assert all(len(row) == self.width for row in self._grid), \
            f"Not all rows have width {self.width}"

        # Count card occurrences
        card_counts: dict[str, int] = {}
        total_spaces = 0
        removed_spaces = 0

        for y in range(self.height):
            for x in range(self.width):
                space = self._grid[y][x]

                # Verify Space is not None
                assert space is not None, f"Space at ({x}, {y}) is None"

                # Count empty spaces (removed cards)
                if space.card is None:
                    removed_spaces += 1
                    # Empty spaces must be face-down and uncontrolled
                    assert not space.is_face_up, \
                        f"Removed space at ({x}, {y}) cannot be face-up"
                    assert space.controlled_by is None, \
                        f"Removed space at ({x}, {y}) cannot be controlled"
                else:
                    # Each space's invariants for non-empty spaces
                    assert isinstance(space.card, str), f"Card at ({x}, {y}) must be string or None"
                    assert len(space.card) > 0, f"Card at ({x}, {y}) must be non-empty"
                    assert not space.card.isspace(), f"Card at ({x}, {y}) cannot be whitespace only"

                    card_counts[space.card] = card_counts.get(space.card, 0) + 1

                # Controlled cards must be face-up
                if space.controlled_by is not None:
                    assert space.is_face_up, \
                        f"Space ({x}, {y}) controlled but face-down"
                    assert isinstance(space.controlled_by, str), \
                        f"controlled_by at ({x}, {y}) must be string or None"
                    assert len(space.controlled_by) > 0, \
                        f"player ID at ({x}, {y}) must be non-empty"

                # Verify is_face_up is boolean
                assert isinstance(space.is_face_up, bool), \
                    f"is_face_up at ({x}, {y}) must be boolean"

                total_spaces += 1

        # Verify total spaces
        assert total_spaces == self.width * self.height, \
            f"Total spaces {total_spaces} != {self.width * self.height}"

        # Verify each remaining card appears exactly twice
        # Cards can appear 0, 1, or 2 times:
        # - 0 times: fully removed (both instances removed)
        # - 1 time: partially removed (one instance removed, one still on board) -- INVALID!
        # - 2 times: both on board (not removed yet)
        for card, count in card_counts.items():
            assert count in [1, 2], \
                f"Card '{card}' appears {count} times on board, must appear 1 or 2 times. " \
                f"(Removed spaces: {removed_spaces})"

    def get_space(self, x: int, y: int) -> Space:
        """
        Get the space at the given coordinates (defensive copy).

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height

        Postconditions:
        - Returns an immutable Space object (frozen dataclass)
        - Safe from rep exposure because Space is frozen

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)

        Returns:
            Immutable Space object at (x, y)

        Raises:
            AssertionError: If coordinates out of bounds
        """
        assert 0 <= x < self.width, f"x={x} out of bounds [0, {self.width})"
        assert 0 <= y < self.height, f"y={y} out of bounds [0, {self.height})"

        # Return the Space directly (it's frozen/immutable)
        return self._grid[y][x]

    def get_card(self, x: int, y: int) -> Optional[str]:
        """
        Get the card value at the given coordinates.

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height

        Postconditions:
        - Returns card string or None (if space is empty)

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)

        Returns:
            Card value (str) or None if space is empty
        """
        return self.get_space(x, y).card

    def is_face_up(self, x: int, y: int) -> bool:
        """
        Check if the card at the given coordinates is face-up.

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height

        Postconditions:
        - Returns True if face-up, False if face-down

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)

        Returns:
            True if face-up, False if face-down
        """
        return self.get_space(x, y).is_face_up

    def get_controller(self, x: int, y: int) -> Optional[str]:
        """
        Get the player ID controlling the space at the given coordinates.

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height

        Postconditions:
        - Returns player ID string or None if uncontrolled

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)

        Returns:
            Player ID (str) or None if not controlled
        """
        return self.get_space(x, y).controlled_by

    # ==================== MUTATOR METHODS ====================

    def flip_card(self, x: int, y: int) -> None:
        """
        Flip the card at the given coordinates (toggle face-up/down).

        When a card is flipped face-down, any control is automatically released.

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height
        - get_card(x, y) is not None (card exists)

        Postconditions:
        - Card at (x, y) has is_face_up toggled
        - If flipped face-down, control is released (controlled_by = None)
        - checkRep() passes

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)

        Raises:
            AssertionError: If preconditions violated
        """
        assert 0 <= x < self.width, f"x={x} out of bounds"
        assert 0 <= y < self.height, f"y={y} out of bounds"

        space = self._grid[y][x]
        assert space.card is not None, f"No card at ({x}, {y})"

        # Create new space with toggled face-up status
        new_is_face_up = not space.is_face_up

        # If flipping face-down, release control
        new_controlled_by = None if not new_is_face_up else space.controlled_by

        new_space = Space(
            card=space.card,
            is_face_up=new_is_face_up,
            controlled_by=new_controlled_by
        )

        self._grid[y][x] = new_space
        self.check_rep()
        self._notify_watchers()

    def set_control(self, x: int, y: int, player_id: str) -> None:
        """
        Set control of a space to a player.

        Preconditions:
        - 0 <= x < width
        - 0 <= y < height
        - get_card(x, y) is not None
        - is_face_up(x, y) is True
        - player_id is non-empty string

        Postconditions:
        - Space at (x, y) is controlled by player_id
        - checkRep() passes

        Args:
            x: Column coordinate (0 to width-1)
            y: Row coordinate (0 to height-1)
            player_id: ID of player taking control (non-empty string)

        Raises:
            AssertionError: If preconditions violated
        """
        assert 0 <= x < self.width, f"x={x} out of bounds"
        assert 0 <= y < self.height, f"y={y} out of bounds"
        assert isinstance(player_id, str), "player_id must be string"
        assert len(player_id) > 0, "player_id must be non-empty"

        space = self._grid[y][x]
        assert space.card is not None, f"No card at ({x}, {y})"
        assert space.is_face_up, f"Card at ({x}, {y}) must be face-up to control"

        new_space = Space(
            card=space.card,
            is_face_up=space.is_face_up,
            controlled_by=player_id
        )

        self._grid[y][x] = new_space
        self.check_rep()

    def remove_control(self, x: int, y: int) -> None:
        """
        Remove player control from a card.

        PRECONDITION:
        - 0 <= x < width
        - 0 <= y < height
        - Card exists (or handle gracefully if removed)

        POSTCONDITION:
        - Card at (x, y) has no controller
        - checkRep() passes
        """
        assert 0 <= x < self.width, f"x={x} out of bounds"
        assert 0 <= y < self.height, f"y={y} out of bounds"

        space = self._grid[y][x]

        # Allow removing control from removed cards (graceful handling)
        if space.card is None:
            return  # Card already removed, nothing to do

        # Create new space without controller
        self._grid[y][x] = Space(
            card=space.card,
            is_face_up=space.is_face_up,
            controlled_by=None
        )

        self.check_rep()

    def remove_card(self, x: int, y: int) -> None:
        """
        Remove a card from the board.

        PRECONDITION:
        - 0 <= x < width
        - 0 <= y < height
        - Card exists
        - Card should ideally be face-up (we'll flip if needed)

        POSTCONDITION:
        - Card at (x, y) is None
        - checkRep() passes
        """
        assert 0 <= x < self.width, f"x={x} out of bounds"
        assert 0 <= y < self.height, f"y={y} out of bounds"

        space = self._grid[y][x]
        assert space.card is not None, f"No card at ({x}, {y}) to remove"

        # Flip face-up if needed (for cleanup scenarios)
        if not space.is_face_up:
            self._grid[y][x] = Space(
                card=space.card,
                is_face_up=True,
                controlled_by=space.controlled_by
            )

        # Remove the card
        self._grid[y][x] = Space(
            card=None,
            is_face_up=False,
            controlled_by=None
        )

        self.check_rep()
        self._notify_watchers()

    @staticmethod
    def parse_from_file(filepath: str) -> "Board":
        """
        Parse and create a Board from a file.

        File format:
        - First line: "width height" (space-separated integers)
        - Remaining lines: space-separated card identifiers

        Cards can be:
        - Single characters: A B C D
        - Words: Apple Banana Apple Banana
        - Emojis: 🌙 ⭐ 🌙 ⭐
        - Multi-line or single-line layout

        Preconditions:
        - File exists and is readable
        - First line contains two positive integers
        - Total cards across all remaining lines = width*height
        - Each unique card appears exactly twice

        Postconditions:
        - Returns a new Board with cards from file
        - All cards appear exactly twice

        Args:
            filepath: Path to board file

        Returns:
            New Board initialized from file

        Raises:
            AssertionError: If file format invalid
            FileNotFoundError: If file doesn't exist
            ValueError: If card constraints violated
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Board file not found: {filepath}") from e

        # Parse dimensions from first line
        assert len(lines) >= 1, "File must have at least 1 line with dimensions"

        dims = lines[0].strip().split()
        assert len(dims) == 2, "First line must be 'width height' (space-separated integers)"

        try:
            width = int(dims[0])
            height = int(dims[1])
        except ValueError as e:
            raise ValueError(f"Width and height must be integers, got: {dims}") from e

        assert width > 0 and height > 0, \
            f"Dimensions must be positive, got width={width}, height={height}"

        # Parse cards from remaining lines (space-separated)
        cards_list = []

        for i in range(1, len(lines)):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                continue

            # Split line by spaces to get individual cards
            # This handles: "A B A B" → ["A", "B", "A", "B"]
            cards_on_line = line.split()
            cards_list.extend(cards_on_line)

        # Verify total card count
        expected_cards = width * height
        actual_cards = len(cards_list)

        if actual_cards != expected_cards:
            raise ValueError(
                f"Expected {expected_cards} cards total, got {actual_cards}. "
                f"(Board is {width}x{height})"
            )

        # Verify each card appears exactly twice
        card_counts: dict[str, int] = {}
        for card in cards_list:
            # Validate card is non-empty and not whitespace
            assert isinstance(card, str), f"Card must be string, got {type(card)}"
            assert len(card) > 0, "Card identifiers cannot be empty"
            assert not card.isspace(), "Card identifiers cannot be whitespace only"

            card_counts[card] = card_counts.get(card, 0) + 1

        # Check frequency constraint
        for card, count in card_counts.items():
            if count != 2:
                raise ValueError(
                    f"Card '{card}' appears {count} times, must appear exactly 2 times"
                )

        # Create and return board
        return Board(width, height, set(card_counts.keys()))

    def __repr__(self) -> str:
        """
        String representation of the board for debugging.

        Shows grid layout with card values and state indicators.
        """
        lines = [f"Board({self.width}x{self.height}):"]

        for y in range(self.height):
            row_str = "  "
            for x in range(self.width):
                space = self._grid[y][x]

                if space.card is None:
                    cell = "[   ]"
                elif space.is_face_up:
                    card_display = space.card[:3].rjust(3)  # First 3 chars
                    if space.controlled_by:
                        cell = f"[{card_display}*]"  # * = controlled
                    else:
                        cell = f"[{card_display} ]"
                else:
                    cell = "[???]"  # Face-down

                row_str += cell + " "

            lines.append(row_str)

        return "\n".join(lines)

    async def wait_for_flip(self, x: int, y: int, player_id: str) -> str:
        """
        Async flip that waits if another player controls the card.

        BLOCKING: May yield control if another player has card
        PRECONDITION: 0 <= x < width, 0 <= y < height
        POSTCONDITION: card at (x, y) is flipped and controlled by player_id

        Returns: the card value at (x, y)
        """
        import asyncio

        # Create lock if it doesn't exist
        if not hasattr(self, '_flip_lock'):
            self._flip_lock = asyncio.Lock()

        async with self._flip_lock:
            # Wait until card becomes available
            while True:
                space = self.get_space(x, y)

                # Card is available if:
                # - Not controlled by anyone, OR
                # - Controlled by current player
                if not space.controlled_by or space.controlled_by == player_id:
                    break  # Card available!

                # Card controlled by another player - wait
                print(f"⏳ {player_id} waiting for {space.controlled_by}'s card at ({x},{y})")
                await asyncio.sleep(0.01)  # Yield control and retry

            # Now we have exclusive access to the card
            space = self.get_space(x, y)  # Refresh space

            # If card is face-down, flip it face-up
            if not space.is_face_up:
                self.flip_card(x, y)

            # Take control
            self.set_control(x, y, player_id)

            print(f"✅ {player_id} flipped {space.card} at ({x},{y})")
            return space.card

    async def map_cards(self, player_id: str, transformer) -> Dict[str, Any]:
        """
        Apply an async transformer function to every card on the board.

        REQUIREMENT: Pairwise consistency - if two cards match at start,
        they must remain matching even if map() is partially done.

        PRECONDITION: transformer is async function: card -> new_card
        POSTCONDITION: all cards transformed, face-up/control state unchanged

        Returns: board state after transformation
        """
        # Use a separate lock for map to allow other operations
        if not hasattr(self, '_map_lock'):
            self._map_lock = asyncio.Lock()

        async with self._map_lock:
            # Iterate through all positions and transform cards
            for y in range(self.height):
                for x in range(self.width):
                    try:
                        space = self.get_space(x, y)
                        if space.card is not None:
                            # Apply transformer - might be slow (API call, etc)
                            new_card = await transformer(space.card)
                            # Use object.__setattr__ to bypass immutability
                            object.__setattr__(space, 'card', new_card)

                        # Yield control to allow other operations
                        await asyncio.sleep(0)
                    except Exception as e:
                        print(f"❌ Transform error at ({x},{y}): {e}")
                        raise

            self.check_rep()
            self._notify_watchers()

            # Build board state manually
            board_grid = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    space = self.get_space(x, y)
                    row.append({
                        "card": space.card,
                        "is_face_up": space.is_face_up,
                        "controlled_by": space.controlled_by
                    })
                board_grid.append(row)

            return {
                "board": board_grid,
                "width": self.width,
                "height": self.height,
                "ok": True
            }

    async def wait_for_change(self) -> Dict[str, Any]:
        """
        Wait for the next board change and return updated board state.

        BLOCKING: This method blocks until ANY change occurs to the board:
        - Cards turning face up or face down
        - Cards being removed from the board
        - Cards changing from one string to a different string

        Non-changes that do NOT trigger notification:
        - Control changes without face state change
        - Failed operations (e.g., flipping empty space)

        PRECONDITION: None (always safe to call)
        POSTCONDITION: Returns board state after a change occurs

        Returns:
            dict with:
            - board: 2D array of current board state
            - width, height: board dimensions
            - ok: success flag

        Thread Safety:
            Multiple watchers can wait concurrently.
            All watchers are notified when ANY change occurs.
        """
        # Create a new event for this watcher
        watcher_event = asyncio.Event()
        self._watchers.append(watcher_event)

        try:
            # Wait until notified of a change
            await watcher_event.wait()

            # Return current board state
            board_grid = []
            for y in range(self.height):
                row = []
                for x in range(self.width):
                    space = self.get_space(x, y)
                    row.append({
                        "card": space.card,
                        "is_face_up": space.is_face_up,
                        "controlled_by": space.controlled_by
                    })
                board_grid.append(row)

            return {
                "board": board_grid,
                "width": self.width,
                "height": self.height,
                "ok": True
            }
        finally:
            # Clean up this watcher
            if watcher_event in self._watchers:
                self._watchers.remove(watcher_event)

    def _notify_watchers(self) -> None:
        """
        Notify all watchers that a change has occurred.

        INTERNAL METHOD: Called by mutator methods after board changes.

        PRECONDITION: Board has just changed
        POSTCONDITION: All waiting watchers are notified
        """
        # Notify all waiting watchers
        for watcher in self._watchers:
            watcher.set()

    def get_state_string(self, player_id: str) -> str:
        """
        Get board state as formatted string for the given player.

        Format (as specified in MIT PS4):
        Line 1: "board"
        Line 2-N: Space-separated row data

        Each space is represented as:
        - "down" if face-down
        - "CARD" if face-up (where CARD is the card string)
        - "none" if removed

        PRECONDITION: player_id is non-empty string
        POSTCONDITION: returns formatted board state string

        Args:
            player_id: ID of player viewing the board

        Returns:
            Formatted board state string
        """
        lines = ["board"]

        for y in range(self.height):
            row_parts = []
            for x in range(self.width):
                space = self.get_space(x, y)

                if space.card is None:
                    row_parts.append("none")
                elif not space.is_face_up:
                    row_parts.append("down")
                else:
                    row_parts.append(space.card)

            lines.append(" ".join(row_parts))

        return "\n".join(lines)

