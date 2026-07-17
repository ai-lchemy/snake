#!/usr/bin/env python3
"""A small, dependency-free terminal Snake game."""

from __future__ import annotations

import argparse
import curses
import json
import random
from pathlib import Path


DIRECTIONS = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
    ord("w"): (-1, 0),
    ord("s"): (1, 0),
    ord("a"): (0, -1),
    ord("d"): (0, 1),
}


class SnakeGame:
    """Game rules, kept separate from curses so they can be tested."""

    def __init__(self, height: int, width: int, rng: random.Random | None = None):
        if height < 5 or width < 8:
            raise ValueError("board must be at least 5 by 8")
        self.height, self.width = height, width
        middle = (height // 2, width // 2)
        self.snake = [middle, (middle[0], middle[1] - 1), (middle[0], middle[1] - 2)]
        self.direction = (0, 1)
        self.score = 0
        self.rng = rng or random.Random()
        self.food = self._place_food()
        self.alive = True

    @property
    def delay_ms(self) -> int:
        """The delay falls with score, giving a smooth, bounded speed increase."""
        return max(45, 150 - self.score * 4)

    def turn(self, direction: tuple[int, int]) -> None:
        if direction != (-self.direction[0], -self.direction[1]):
            self.direction = direction

    def step(self) -> bool:
        """Advance one tick and return whether the snake ate food."""
        head_y, head_x = self.snake[0]
        new_head = (head_y + self.direction[0], head_x + self.direction[1])
        eating = new_head == self.food
        body = self.snake if eating else self.snake[:-1]
        if not (0 <= new_head[0] < self.height and 0 <= new_head[1] < self.width) or new_head in body:
            self.alive = False
            return False
        self.snake.insert(0, new_head)
        if eating:
            self.score += 1
            self.food = self._place_food()
        else:
            self.snake.pop()
        return eating

    def _place_food(self) -> tuple[int, int] | None:
        free = [(y, x) for y in range(self.height) for x in range(self.width) if (y, x) not in self.snake]
        return self.rng.choice(free) if free else None


class HighScores:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> list[int]:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(values, list):
                return []
            return sorted((value for value in values if isinstance(value, int) and value >= 0), reverse=True)[:3]
        except (OSError, json.JSONDecodeError):
            return []

    def record(self, score: int) -> list[int]:
        scores = sorted(self.load() + [max(0, score)], reverse=True)[:3]
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(scores), encoding="utf-8")
        except OSError:
            pass  # A read-only home directory should not prevent playing.
        return scores


def _center(screen, row: int, text: str) -> None:
    height, width = screen.getmaxyx()
    if 0 <= row < height:
        screen.addnstr(row, max(0, (width - len(text)) // 2), text, max(0, width - 1))


def _pause(screen) -> str:
    screen.nodelay(False)
    while True:
        screen.erase()
        height, _ = screen.getmaxyx()
        _center(screen, height // 2 - 1, "PAUSED")
        _center(screen, height // 2, "R: resume   Q: quit")
        screen.refresh()
        key = screen.getch()
        if key in (ord("r"), ord("R"), ord("p"), ord("P"), 27):
            screen.nodelay(True)
            return "resume"
        if key in (ord("q"), ord("Q")):
            return "quit"


def _draw(screen, game: SnakeGame, scores: list[int]) -> None:
    screen.erase()
    screen.border()
    screen.addnstr(0, 2, f" Score: {game.score} | P: pause | Q: quit ", max(0, screen.getmaxyx()[1] - 4))
    for index, (y, x) in enumerate(game.snake):
        screen.addch(y + 1, x + 1, "@" if index == 0 else "o")
    if game.food is not None:
        screen.addch(game.food[0] + 1, game.food[1] + 1, "*")
    screen.addnstr(game.height + 1, 2, "Top 3: " + ", ".join(map(str, scores or [0])), game.width - 2)
    screen.refresh()


def run(screen, score_store: HighScores) -> None:
    curses.curs_set(0)
    screen.keypad(True)
    screen.nodelay(True)
    height, width = screen.getmaxyx()
    board_height, board_width = height - 3, width - 2
    if board_height < 5 or board_width < 8:
        raise RuntimeError("Terminal too small; resize it to at least 8 rows by 10 columns.")
    game = SnakeGame(board_height, board_width)
    scores = score_store.load()
    while game.alive:
        screen.timeout(game.delay_ms)
        _draw(screen, game, scores)
        key = screen.getch()
        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("p"), ord("P"), 27) and _pause(screen) == "quit":
            break
        if key in DIRECTIONS:
            game.turn(DIRECTIONS[key])
        game.step()
    scores = score_store.record(game.score)
    screen.nodelay(False)
    screen.erase()
    _center(screen, height // 2 - 1, f"Game over — score: {game.score}")
    _center(screen, height // 2, "Top 3: " + ", ".join(map(str, scores)))
    _center(screen, height // 2 + 1, "Press any key to exit")
    screen.refresh()
    screen.getch()


def main() -> int:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, default=Path.home() / ".snake_highscores.json")
    args = parser.parse_args()
    try:
        curses.wrapper(run, HighScores(args.scores))
    except (curses.error, RuntimeError) as exc:
        parser.exit(1, f"snake: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
