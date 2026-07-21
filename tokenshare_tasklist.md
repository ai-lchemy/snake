# Tokenshare Tasklist

## Configuration

allow-multiple-branches: false

## Pending Tasks

### <task> [Pending] Build a Polished Terminal Snake Game

#### Objective

Create a polished, directly runnable Snake game for Unix-like terminals using Python 3.10 or newer and only the standard library. The game must provide a colorful interactive experience while keeping its core logic independently testable.

#### Requirements

- Implement the game as `snake.py` using `curses`, with no third-party runtime dependencies.
- Start a new game with a three-cell snake, one apple on an unoccupied cell, a score of zero, and automatic timed movement.
- Accept arrow-key input for steering. Ignore an attempted immediate reversal into the snake's neck.
- Grow the snake and increment the score by one when an apple is eaten, then place a new apple uniformly among unoccupied playable cells.
- End the game when the snake hits a wall or itself. Treat moving into the cell vacated by the tail during the same step as legal unless the snake is growing.
- Increase movement speed as play continues and apples are eaten, with a lower delay limit that keeps the game playable.
- In color-capable terminals, render the entire snake, including its head and body, in green and render the apple in red using `curses` color pairs.
- Detect color availability through `curses`. If colors are unavailable or cannot be initialized, continue in monochrome with distinct snake and apple characters rather than failing.
- Display the current score, best saved score, snake, apple, bordered play area, and available controls.
- Support `P` to pause. The pause menu must allow `R` or `P` to resume, `N` to start a new game, and `Q` to quit.
- After game over, show the final score and top three scores, with `N` to start a new game and `Q` to quit.
- Persist the three highest scores as a descending JSON list at `~/.snake_highscores.json`.
- Provide `--scores PATH` to override the score file location and `--help` for usage information.
- Treat missing, malformed, unreadable, or semantically invalid score data as an empty score list. Ignore invalid entries, negative values, and booleans. A score-file write failure must not crash the game.
- Detect terminals smaller than 30 columns by 10 rows and show a resize-or-quit message instead of starting an invalid board.
- Restore terminal state on normal exit and handled initialization errors.
- Keep movement, collision, apple placement, speed calculation, and high-score handling separable from `curses` rendering so they can be unit tested with deterministic random input.
- Add `test_snake.py` using `unittest` and a `README.md` documenting requirements, launch command, controls, color behavior and fallback, score storage, and test command.

#### Validation

- `python3 -m unittest -v` passes tests covering initialization, ordinary movement, growth and scoring, apple placement, reversal prevention, wall collision, self-collision, legal movement into a vacated tail cell, progressive speed increase and its lower bound, top-three score ordering, invalid score filtering, malformed score files, write-failure tolerance, and safe color initialization with and without terminal color support.
- `python3 -m py_compile snake.py test_snake.py` succeeds.
- `python3 snake.py --help` exits successfully and documents `--scores`.
- In a color-capable interactive terminal of at least 30x10, the snake appears green, the apple appears red, controls respond correctly, play accelerates, collisions reach the game-over screen, and qualifying scores persist across launches.
- In a terminal without color support, the snake and apple remain visually distinct and the game remains fully playable without a traceback.
- In a terminal smaller than 30x10, the resize-or-quit message appears without a traceback.
- `git diff --check` reports no whitespace errors.

#### Out of scope

- Native Windows terminal support, graphical interfaces, networking, multiplayer, sound, AI-controlled snakes, difficulty selection, user-selectable themes, packaging, and third-party dependencies.
- Recreating or restoring files directly from earlier deleted commits; the implementation must satisfy this task and the current blank repository state.

### </task>

## WIP Tasks

## Completed Tasks
