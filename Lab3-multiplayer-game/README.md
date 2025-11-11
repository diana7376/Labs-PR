# Lab 3: Multiplayer Memory Scramble Game

## How to Run the Project

1. **Build and launch with Docker Compose (from the `/backend` directory):**
   ```sh
   docker-compose up --build
   ```
   This starts the Memory Scramble backend server and serves the interactive web app.

2. **Access the web application:**
   - Visit [http://localhost:8000](http://localhost:8000)
   - Play Memory Scramble — either solo or with other players.

3. **Stop the server:**
   - Use `Ctrl+C` in your terminal, or run:
     ```sh
     docker-compose down
     ```

***

## Project Structure

```
Lab3-multiplayer-game/
├── backend/
│   ├── scripts/
│   │   ├── simulation.py
│   │   └── multyplayer_simulation.py
│   ├── src/
│   │   ├── commands/
│   │   │   └── commands.py
│   │   ├── game/
│   │   │   ├── board.py
│   │   │   └── space.py
│   │   └── server/
│   │       └── server.py
│   ├── tests/
│   │   ├── test_board.py
│   │   ├── test_commands.py
│   │   ├── test_concurrent.py
│   │   ├── test_game_rules.py
│   │   ├── test_map.py
│   │   ├── test_simulation.py
│   │   └── test_watch.py
│   ├── Dockerfile
│   └── docker-compose.yml
├── photos/
│   └── [component and result screenshots]
└── README.md
```

***

## Step-by-Step Tutorial & Results

### 1. Game UI and Functionality

When the server is running, open the Memory Scramble app:
- Set player ID and board size.
- Flip cards, match pairs, and compete for the best score!
- Multi-player support and animations (see below).

> ![Game UI](photos%2Fimg_3.png)
> Figure 1: Main play area — flip cards to reveal symbols and make matches.


### 2. Game Help and Controls

> ![Help Modal](photos%2Fimg_2.png)
> Figure 2: In-game help dialog explains rules and controls.

- **Goal**: Match all pairs on the board.
- **Controls**: Set board size, player ID, and start new games.
- **Card States**: Cards change color to show face/down, match, pending, etc.

### 3. Settings and Difficulty

> ![Settings Panel](photos%2Fimg_1.png)
> Figure 3: Customize board size and player settings for single or multiplayer play.

- Select board dimensions (2x2 to 10x10)
- Tune for various difficulty levels.

### 4. Automated Validation and Statistics

>![Simulation Output](photos%2Fimg_6.png)
>![img_7.png](photos%2Fimg_7.png)
>![img_8.png](photos%2Fimg_8.png)
> 
> Figure 4: Output of simulation script — validates Board ADT and game logic.

- Simulation [simulation.py](backend%2Fscripts%2Fsimulation.py) script automatically test board rules and print stats:
  - Total moves, time taken, board validation.
  - [test_board.py](backend%2Ftests%2Ftest_board.py) and [test_game_rules.py](backend%2Ftests%2Ftest_game_rules.py) ensure correctness for all rules.

### 5. Multiplayer Simulation & Robustness

> ![Multiplayer Simulation](photos%2Fimg.png)
> 
> Figure 5: Console output showing concurrent simulation — 4 players, 100 moves each, random delays; validates thread safety and robustness.
 

- [multyplayer_simulation.py](backend%2Fscripts%2Fmultyplayer_simulation.py):
  - 4 players make 100 random moves each, with 0.1–2ms random timeouts.
  - Checks safety under concurrency: **no crashes!**

***

## Automated Tests

- All core game logic covered by concise, well-commented unit tests in `/tests`.
- Simulations validate both correctness (matching pairs logic) and concurrency robustness.

***

## Specifications & Design

- **Board ADT:** Mutable board with rep invariants and checkRep()
- **Commands module:** Implements full MIT 6.102 spec, handles only via Board API
- **No data leaks:** Safety from rep exposure
- **Structured project layout:** Follows assignment and MIT skeleton guidance
