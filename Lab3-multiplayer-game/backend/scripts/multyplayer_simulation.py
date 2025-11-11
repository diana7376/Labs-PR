import asyncio
import random
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.game.board import Board


PLAYER_COUNT = 4
MOVES_PER_PLAYER = 100
MIN_DELAY = 0.0001  # 0.1ms
MAX_DELAY = 0.002   # 2ms

async def player_task(board, player_id, move_log):
    width, height = board.width, board.height
    for move in range(MOVES_PER_PLAYER):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        try:
            board.flip_card(x, y)  # Or await a flip(...) command if using async actions!
            result = f"Player {player_id} flipped ({x},{y})"
        except Exception as ex:
            result = f"Player {player_id} move ({x},{y}) failed: {ex}"
        move_log[player_id].append(result)
        print(result)  # Log each move to the console
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

async def simulate_multi_player():
    # Use a fixed board size; must match BOARD ADT/card constraints!
    width, height = 4, 4
    card_types = {"A", "B", "C", "D", "E", "F", "G", "H"}  # 8 unique; 4x4=16=8*2
    board = Board(width, height, card_types)

    move_log = {pid: [] for pid in range(PLAYER_COUNT)}
    tasks = [player_task(board, pid, move_log) for pid in range(PLAYER_COUNT)]

    start = time.perf_counter()
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    print("\n--- Simulation Complete! ---")
    for pid, moves in move_log.items():
        print(f"Player {pid}: {len(moves)} moves")

    print(f"\nSimulation ran {PLAYER_COUNT * MOVES_PER_PLAYER} moves in {elapsed:.3f} seconds\n")

if __name__ == "__main__":
    asyncio.run(simulate_multi_player())
