from fastapi import FastAPI, Path, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
from game.board import Board
from commands.commands import GameManager

app = FastAPI(title="Memory Scramble API")

# Enable CORS for all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store all games here
games = {}

# Serve static frontend files (adjust path if needed)
public_dir = Path(__file__).parent.parent.parent.parent / "public"

@app.get("/")
async def serve_game():
    index_file = public_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "Frontend not found"}

@app.post("/games/new")
async def create_new_game(request: Request):
    data = await request.json()
    width = data.get("width", 4)
    height = data.get("height", 4)
    player_id = data.get("player_id", "player1")

    num_pairs = (width * height) // 2
    available_cards = ["🎮", "🌈", "🎨", "⭐", "🎪", "🎭", "🎬", "🎸", "⚽", "🏀", "🎲", "🎯"]
    cards = set(available_cards[:num_pairs])

    board = Board(width, height, cards)
    game = GameManager(board)
    game_id = f"game_{len(games)}"
    games[game_id] = game

    state = await game.look(player_id)
    return {
        "ok": True,
        "game_id": game_id,
        "board": state.get("board", []),
        "scores": state.get("scores", {})
    }

@app.post("/games/{game_id}/flip")
async def flip_card(game_id: str, request: Request):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]
    data = await request.json()
    player_id = data.get("player_id")
    row = data.get("row")
    column = data.get("column")

    if player_id is None or row is None or column is None:
        raise HTTPException(status_code=400, detail="Missing parameters")
    try:
        result = await game.flip(player_id, row, column)
        return result
    except Exception as e:
        return {"ok": False, "message": str(e)}

@app.get("/games/{game_id}/look")
async def look(game_id: str, player_id: str):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[game_id]
    result = await game.look(player_id)
    return result
