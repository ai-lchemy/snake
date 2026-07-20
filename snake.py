#!/usr/bin/env python3
"""A small terminal Snake game using only Python's standard library."""

from __future__ import annotations

import argparse
import curses
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


Point = tuple[int, int]
DIRECTIONS: dict[int, Point] = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
}
OPPOSITE = {(-1, 0): (1, 0), (1, 0): (-1, 0), (0, -1): (0, 1), (0, 1): (0, -1)}


def default_score_path() -> Path:
    return Path.home() / ".snake_highscores.json"


def load_highscores(path: Path) -> list[int]:
    """Load, validate, and sort up to three scores."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        scores = [value for value in data if isinstance(value, int) and not isinstance(value, bool) and value >= 0]
        return sorted(scores, reverse=True)[:3]
    except (OSError, json.JSONDecodeError):
        return []


def record_highscore(path: Path, score: int) -> list[int]:
    """Persist a score and return the new top three."""
    scores = sorted(load_highscores(path) + [max(0, int(score))], reverse=True)[:3]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scores), encoding="utf-8")
    except OSError:
        pass  # A read-only home directory should not prevent the game from running.
    return scores


@dataclass
class SnakeGame:
    height: int
    width: int
    rng: random.Random = field(default_factory=random.Random)
    snake: list[Point] = field(init=False)
    direction: Point = field(init=False, default=(0, 1))
    food: Point | None = field(init=False, default=None)
    score: int = field(init=False, default=0)
    moves: int = field(init=False, default=0)
    game_over: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        if self.height < 5 or self.width < 10:
            raise ValueError("board must be at least 5 rows by 10 columns")
        middle = (self.height // 2, self.width // 2)
        self.snake = [middle, (middle[0], middle[1] - 1), (middle[0], middle[1] - 2)]
        self.place_food()

    @property
    def delay_ms(self) -> int:
        """Movement delay decreases with score and time in play."""
        return max(45, 150 - self.score * 4 - (self.moves // 5) * 3)

    def change_direction(self, direction: Point) -> None:
        if direction != OPPOSITE[self.direction]:
            self.direction = direction

    def place_food(self) -> None:
        available = [
            (row, col)
            for row in range(1, self.height - 1)
            for col in range(1, self.width - 1)
            if (row, col) not in self.snake
        ]
        self.food = self.rng.choice(available) if available else None
        if self.food is None:
            self.game_over = True

    def step(self) -> bool:
        """Advance one cell. Return True when food was eaten."""
        if self.game_over:
            return False
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        grows = new_head == self.food
        body_hit_area = self.snake if grows else self.snake[:-1]
        if (
            new_head[0] <= 0
            or new_head[0] >= self.height - 1
            or new_head[1] <= 0
            or new_head[1] >= self.width - 1
            or new_head in body_hit_area
        ):
            self.game_over = True
            return False
        self.snake.insert(0, new_head)
        self.moves += 1
        if grows:
            self.score += 1
            self.place_food()
        else:
            self.snake.pop()
        return grows


def centered(window: curses.window, row: int, text: str) -> None:
    height, width = window.getmaxyx()
    if 0 <= row < height and width > 1:
        window.addnstr(row, max(0, (width - len(text)) // 2), text, width - 1)


def draw_game(window: curses.window, game: SnakeGame, highscores: Sequence[int]) -> None:
    window.erase()
    height, width = window.getmaxyx()
    window.border()
    status = f" Score: {game.score}  Best: {highscores[0] if highscores else 0}  P: pause  Q: quit "
    window.addnstr(0, 2, status, max(0, width - 4))
    if game.food is not None:
        window.addch(game.food[0], game.food[1], "*")
    for index, (row, col) in enumerate(game.snake):
        window.addch(row, col, "@" if index == 0 else "o")
    window.refresh()


def pause_menu(window: curses.window) -> str:
    window.nodelay(False)
    height, _ = window.getmaxyx()
    centered(window, height // 2 - 1, "PAUSED")
    centered(window, height // 2, "R resume   N new game   Q quit")
    window.refresh()
    while True:
        key = window.getch()
        if key in (ord("r"), ord("R"), ord("p"), ord("P")):
            return "resume"
        if key in (ord("n"), ord("N")):
            return "restart"
        if key in (ord("q"), ord("Q")):
            return "quit"


def wait_for_size(window: curses.window) -> tuple[int, int] | None:
    while True:
        height, width = window.getmaxyx()
        if height >= 10 and width >= 30:
            return height, width
        window.erase()
        centered(window, max(0, height // 2), "Terminal too small (need 30x10). Resize or press Q.")
        window.refresh()
        window.timeout(250)
        if window.getch() in (ord("q"), ord("Q")):
            return None


def run(window: curses.window, score_path: Path) -> None:
    curses.curs_set(0)
    window.keypad(True)
    while True:
        size = wait_for_size(window)
        if size is None:
            return
        game = SnakeGame(*size)
        highscores = load_highscores(score_path)
        last_move = time.monotonic()
        restart = False
        while not game.game_over:
            draw_game(window, game, highscores)
            window.timeout(max(1, game.delay_ms - int((time.monotonic() - last_move) * 1000)))
            key = window.getch()
            if key in DIRECTIONS:
                game.change_direction(DIRECTIONS[key])
            elif key in (ord("p"), ord("P")):
                action = pause_menu(window)
                if action == "quit":
                    return
                if action == "restart":
                    restart = True
                    break
                last_move = time.monotonic()
                window.nodelay(True)
                continue
            elif key in (ord("q"), ord("Q")):
                return
            if (time.monotonic() - last_move) * 1000 >= game.delay_ms:
                game.step()
                last_move = time.monotonic()
        if restart:
            continue
        highscores = record_highscore(score_path, game.score)
        draw_game(window, game, highscores)
        height, _ = window.getmaxyx()
        centered(window, height // 2, f"GAME OVER — Score: {game.score}")
        centered(window, height // 2 + 1, "N new game   Q quit")
        centered(window, height // 2 + 3, "Top 3: " + (", ".join(map(str, highscores)) or "none"))
        window.refresh()
        window.nodelay(False)
        while True:
            key = window.getch()
            if key in (ord("n"), ord("N")):
                break
            if key in (ord("q"), ord("Q")):
                return


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, default=default_score_path(), help="high-score JSON file")
    args = parser.parse_args()
    try:
        curses.wrapper(run, args.scores)
    except curses.error:
        parser.error("could not initialize a terminal; run Snake in an interactive terminal")


if __name__ == "__main__":
    main()
