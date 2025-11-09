"""
Space ADT representing a single card position on the board.

Representation Invariants:
- card is either a non-empty string of non-whitespace characters, or None
- is_face_up is a boolean value
- controlled_by is either None or a non-empty string (player ID)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Space:
    """
    Immutable representation of a single board space.

    Thread-safe because immutable (frozen).
    """
    card: Optional[str]
    is_face_up: bool
    controlled_by: Optional[str]

    def __post_init__(self):
        """Validate representation invariants."""
        if self.card is not None:
            assert isinstance(self.card, str), "card must be string or None"
            assert len(self.card) > 0, "card must be non-empty"
            assert not self.card.isspace(), "card cannot be only whitespace"

        assert isinstance(self.is_face_up, bool), "is_face_up must be boolean"

        if self.controlled_by is not None:
            assert isinstance(self.controlled_by, str), "controlled_by must be string or None"
            assert len(self.controlled_by) > 0, "player ID must be non-empty"

    def __repr__(self) -> str:
        """String representation of space."""
        card_str = self.card if self.card else "empty"
        face_str = "up" if self.is_face_up else "down"
        control_str = f" (controlled by {self.controlled_by})" if self.controlled_by else ""
        return f"Space({card_str}, {face_str}{control_str})"
