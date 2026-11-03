"""Real-to-Sim core library (TRD §2). Pure state machine + runners."""

from realtosim.game_engine import (
    Game,
    GameSetupError,
    GameStateError,
    abort,
    brief,
    new_game,
    observe,
    submit,
    to_log,
)

__all__ = [
    "Game",
    "GameSetupError",
    "GameStateError",
    "abort",
    "brief",
    "new_game",
    "observe",
    "submit",
    "to_log",
]
