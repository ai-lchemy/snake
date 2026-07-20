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
DIRECTIONS: dict[int, Point] = {
    curses.KEY_UP: (-1, 0),
    curses.KEY_DOWN: (1, 0),
    curses.KEY_LEFT: (0, -1),
    curses.KEY_RIGHT: (0, 1),
}


def default_score_path() -> Path:
    """Return an XDG-friendly per-user score file path."""
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "snake" / "highscores.json"


class HighScores:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_score_path()

    def load(self) -> list[int]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                return []
            return sorted(
                (score for score in data if isinstance(score, int) and score >= 0),
                reverse=True,
            )[:3]
        except (OSError, json.JSONDecodeError):
            return []

    def record(self, score: int) -> list[int]:
        scores = sorted(self.load() + [max(0, int(score))], reverse=True)[:3]
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
    direction: Point = field(default=(0, 1), init=False)
    food: Point | None = field(init=False)
    score: int = field(default=0, init=False)
    game_over: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.height < 5 or self.width < 8:
            raise ValueError("board must be at least 5 rows by 8 columns")
        row, col = self.height // 2, self.width // 2
        self.snake = [(row, col), (row, col - 1), (row, col - 2)]
        self.food = self._place_food()

    def turn(self, direction: Point) -> None:
        if direction != (-self.direction[0], -self.direction[1]):
            self.direction = direction

    def step(self) -> None:
        if self.game_over:
            return
        head_row, head_col = self.snake[0]
        new_head = (head_row + self.direction[0], head_col + self.direction[1])
        ate = new_head == self.food
        occupied = self.snake if ate else self.snake[:-1]
        if not (0 <= new_head[0] < self.height and 0 <= new_head[1] < self.width):
            self.game_over = True
            return
        if new_head in occupied:
            self.game_over = True
            return
        self.snake.insert(0, new_head)
        if ate:
            self.score += 10
            self.food = self._place_food()
        else:
            self.snake.pop()

    def _place_food(self) -> Point | None:
        free = [
            (row, col)
            for row in range(self.height)
            for col in range(self.width)
            if (row, col) not in self.snake
        ]
        if not free:
            self.game_over = True
            return None
        return self.rng.choice(free)


def frame_delay(elapsed_seconds: float) -> float:
    """Speed up every 15 seconds, capped at a playable 20 FPS."""
    return max(0.05, 0.16 - (max(0.0, elapsed_seconds) // 15) * 0.012)


def _center(window: curses.window, row: int, text: str) -> None:
    _, width = window.getmaxyx()
    try:
        window.addstr(row, max(0, (width - len(text)) // 2), text[: width - 1])
    except curses.error:
        pass


def _pause_menu(window: curses.window) -> bool:
    """Return True to resume and False to quit."""
    window.nodelay(False)
    window.erase()
    _center(window, 2, "PAUSED")
    _center(window, 4, "[R] Resume")
    _center(window, 5, "[Q] Quit game")
    window.refresh()
    while True:
        key = window.getch()
        if key in (ord("r"), ord("R"), ord("p"), ord("P")):
            window.nodelay(True)
            return True
        if key in (ord("q"), ord("Q"), 27):
            window.nodelay(True)
            return False


def _draw(window: curses.window, game: SnakeGame, scores: list[int]) -> None:
    window.erase()
    window.border()
    title = f" Snake | Score: {game.score} | Top: {scores[0] if scores else 0} | P: pause | Q: quit "
    try:
        window.addstr(0, 2, title[: max(0, game.width - 2)])
        if game.food is not None:
            window.addch(game.food[0] + 1, game.food[1] + 1, "*")
        for index, (row, col) in enumerate(game.snake):
            window.addch(row + 1, col + 1, "@" if index == 0 else "o")
    except curses.error:
        pass
    window.refresh()


def _run_screen(screen: curses.window, scores: HighScores, clock: Callable[[], float] = time.monotonic) -> None:
    curses.curs_set(0)
    screen.keypad(True)
    screen.nodelay(True)
    rows, cols = screen.getmaxyx()
    if rows < 8 or cols < 20:
        screen.nodelay(False)
        _center(screen, 1, "Terminal too small (minimum 20x8).")
        screen.getch()
        return

    game = SnakeGame(rows - 2, cols - 2)
    started = clock()
    paused_time = 0.0
    while not game.game_over:
        _draw(screen, game, scores.load())
        frame_started = clock()
        key = screen.getch()
        if key in DIRECTIONS:
            game.turn(DIRECTIONS[key])
        elif key in (ord("p"), ord("P")):
            paused_at = clock()
            if not _pause_menu(screen):
                break
            paused_time += clock() - paused_at
            continue
        elif key in (ord("q"), ord("Q")):
            break
        game.step()
        elapsed = clock() - started - paused_time
        time.sleep(max(0.0, frame_delay(elapsed) - (clock() - frame_started)))

    leaderboard = scores.record(game.score)
    screen.nodelay(False)
    screen.erase()
    _center(screen, 1, "GAME OVER")
    _center(screen, 3, f"Score: {game.score}")
    _center(screen, 5, "Top Three")
    for index, score in enumerate(leaderboard, 1):
        _center(screen, 5 + index, f"{index}. {score}")
    _center(screen, 10, "Press any key to exit")
    screen.refresh()
    screen.getch()


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, help="path to the high-score file")
    args = parser.parse_args()
    scores = HighScores(args.scores)
    try:
        curses.wrapper(_run_screen, scores)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
