#!/usr/bin/env python3
"""A small, dependency-free terminal Snake game."""

from __future__ import annotations

import argparse
import curses
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


Point = tuple[int, int]
Direction = tuple[int, int]

UP: Direction = (-1, 0)
DOWN: Direction = (1, 0)
LEFT: Direction = (0, -1)
RIGHT: Direction = (0, 1)

KEY_DIRECTIONS = {
    curses.KEY_UP: UP,
    curses.KEY_DOWN: DOWN,
    curses.KEY_LEFT: LEFT,
    curses.KEY_RIGHT: RIGHT,
    ord("w"): UP,
    ord("s"): DOWN,
    ord("a"): LEFT,
    ord("d"): RIGHT,
}


def default_score_path() -> Path:
    """Return a per-user location without writing inside the installation."""
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return data_home / "terminal-snake" / "highscores.json"


class HighScores:
    """Persistent top-three score table."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_score_path()

    def load(self) -> list[int]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            scores = [int(value) for value in raw if int(value) >= 0]
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []
        return sorted(scores, reverse=True)[:3]

    def record(self, score: int) -> list[int]:
        scores = sorted([*self.load(), max(0, int(score))], reverse=True)[:3]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(scores), encoding="utf-8")
        temporary.replace(self.path)
        return scores


@dataclass
class SnakeGame:
    height: int
    width: int
    rng: random.Random = field(default_factory=random.Random)
    snake: list[Point] = field(init=False)
    direction: Direction = field(default=RIGHT, init=False)
    food: Point | None = field(init=False)
    score: int = field(default=0, init=False)
    alive: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        if self.height < 5 or self.width < 8:
            raise ValueError("board must be at least 5 rows by 8 columns")
        row, col = self.height // 2, self.width // 2
        self.snake = [(row, col), (row, col - 1), (row, col - 2)]
        self.food = self._place_food()

    def turn(self, direction: Direction) -> None:
        if (direction[0] + self.direction[0], direction[1] + self.direction[1]) != (0, 0):
            self.direction = direction

    def _place_food(self) -> Point | None:
        occupied = set(self.snake)
        free = [
            (row, col)
            for row in range(1, self.height - 1)
            for col in range(1, self.width - 1)
            if (row, col) not in occupied
        ]
        return self.rng.choice(free) if free else None

    def step(self) -> bool:
        """Advance one tick and return whether food was eaten."""
        head_row, head_col = self.snake[0]
        new_head = (head_row + self.direction[0], head_col + self.direction[1])
        ate = new_head == self.food
        body = self.snake if ate else self.snake[:-1]
        row, col = new_head
        if row <= 0 or row >= self.height - 1 or col <= 0 or col >= self.width - 1 or new_head in body:
            self.alive = False
            return False
        self.snake.insert(0, new_head)
        if ate:
            self.score += 10
            self.food = self._place_food()
            if self.food is None:
                self.alive = False
        else:
            self.snake.pop()
        return ate


def tick_delay(elapsed_seconds: float) -> int:
    """Milliseconds per move, gradually decreasing over five minutes."""
    return max(55, 180 - int(max(0.0, elapsed_seconds) // 12) * 5)


def centered(window: curses.window, row: int, message: str, attr: int = 0) -> None:
    _, width = window.getmaxyx()
    try:
        window.addnstr(row, max(0, (width - len(message)) // 2), message, max(0, width - 1), attr)
    except curses.error:
        pass


def pause_menu(window: curses.window) -> bool:
    """Show the pause menu. Return False when the player chooses to quit."""
    window.nodelay(False)
    while True:
        height, _ = window.getmaxyx()
        centered(window, height // 2 - 1, "PAUSED", curses.A_BOLD)
        centered(window, height // 2, "P / Enter: resume    Q: quit")
        window.refresh()
        key = window.getch()
        if key in (ord("p"), ord("P"), 10, 13, 27):
            window.erase()
            return True
        if key in (ord("q"), ord("Q")):
            return False


def draw(window: curses.window, game: SnakeGame, highscores: list[int]) -> None:
    window.erase()
    height, width = game.height, game.width
    try:
        window.border()
        status = f" Score: {game.score}  Top 3: {', '.join(map(str, highscores)) or '-'}  P: pause  Q: quit "
        window.addnstr(0, 2, status, max(0, width - 4), curses.A_BOLD)
        if game.food is not None:
            window.addch(*game.food, "*")
        for index, point in enumerate(game.snake):
            window.addch(*point, "@" if index == 0 else "o")
    except curses.error:
        pass
    window.refresh()


def play(window: curses.window, scores: HighScores, clock: Callable[[], float] = time.monotonic) -> int:
    curses.curs_set(0)
    window.keypad(True)
    window.nodelay(True)
    height, width = window.getmaxyx()
    if height < 10 or width < 30:
        window.nodelay(False)
        centered(window, 0, "Terminal too small (minimum 30x10). Resize and try again.")
        window.getch()
        return 0

    game = SnakeGame(height, width)
    highscores = scores.load()
    started = clock()
    paused_time = 0.0
    while game.alive:
        elapsed = clock() - started - paused_time
        window.timeout(tick_delay(elapsed))
        key = window.getch()
        if key in KEY_DIRECTIONS:
            game.turn(KEY_DIRECTIONS[key])
        elif key in (ord("p"), ord("P"), 27):
            pause_started = clock()
            if not pause_menu(window):
                break
            paused_time += clock() - pause_started
            window.nodelay(True)
        elif key in (ord("q"), ord("Q")):
            break
        game.step()
        draw(window, game, highscores)

    highscores = scores.record(game.score)
    window.nodelay(False)
    window.erase()
    centered(window, height // 2 - 1, "GAME OVER" if not game.alive else "GAME ENDED", curses.A_BOLD)
    centered(window, height // 2, f"Score: {game.score}    Top 3: {', '.join(map(str, highscores))}")
    centered(window, height // 2 + 1, "Press any key to exit")
    window.refresh()
    window.getch()
    return game.score


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, help="alternate high-score file")
    args = parser.parse_args()
    curses.wrapper(play, HighScores(args.scores))


if __name__ == "__main__":
    main()
