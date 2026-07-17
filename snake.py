#!/usr/bin/env python3
"""A small, dependency-free terminal Snake game."""

from __future__ import annotations

import argparse
import curses
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

Point = tuple[int, int]
Direction = tuple[int, int]

UP: Direction = (-1, 0)
DOWN: Direction = (1, 0)
LEFT: Direction = (0, -1)
RIGHT: Direction = (0, 1)


def default_score_path() -> Path:
    return Path.home() / ".snake_highscores.json"


def load_highscores(path: Path) -> list[int]:
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(values, list):
            return []
        scores = []
        for value in values:
            try:
                score = int(value)
            except (ValueError, TypeError):
                continue
            if score >= 0:
                scores.append(score)
        return sorted(scores, reverse=True)[:3]
    except (OSError, json.JSONDecodeError):
        return []


def save_highscore(path: Path, scores: list[int], score: int) -> list[int]:
    updated = sorted([*scores, max(0, int(score))], reverse=True)[:3]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(updated), encoding="utf-8")
    except OSError:
        pass  # A read-only home directory should not prevent play.
    return updated


@dataclass
class SnakeGame:
    height: int
    width: int
    rng: random.Random = field(default_factory=random.Random)
    snake: list[Point] = field(init=False)
    obstacles: set[Point] = field(init=False)
    direction: Direction = field(default=RIGHT, init=False)
    food: Point | None = field(init=False)
    score: int = field(default=0, init=False)
    steps: int = field(default=0, init=False)
    game_over: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.height < 5 or self.width < 10:
            raise ValueError("board must be at least 5 rows by 10 columns")
        row, col = self.height // 2, self.width // 2
        self.snake = [(row, col), (row, col - 1), (row, col - 2)]
        self.obstacles = self._place_obstacles()
        self.food = self._place_food()

    def _place_obstacles(self) -> set[Point]:
        """Scatter obstacles while leaving room around the starting snake."""
        head_row, head_col = self.snake[0]
        safe = set(self.snake)
        safe.update(
            (head_row + row_delta, head_col + col_delta)
            for row_delta, col_delta in (UP, DOWN, LEFT, RIGHT)
        )
        free = [
            (row, col)
            for row in range(1, self.height - 1)
            for col in range(1, self.width - 1)
            if (row, col) not in safe
        ]
        count = min(len(free), max(1, (self.height - 2) * (self.width - 2) // 40))
        return set(self.rng.sample(free, count))

    @property
    def delay_ms(self) -> int:
        """Movement delay, decreasing steadily until the playable minimum."""
        return max(45, 150 - self.steps // 12 * 5 - self.score * 2)

    def turn(self, direction: Direction) -> None:
        if (direction[0] + self.direction[0], direction[1] + self.direction[1]) != (0, 0):
            self.direction = direction

    def _place_food(self) -> Point | None:
        free = [
            (row, col)
            for row in range(1, self.height - 1)
            for col in range(1, self.width - 1)
            if (row, col) not in self.snake and (row, col) not in self.obstacles
        ]
        return self.rng.choice(free) if free else None

    def step(self) -> bool:
        """Advance one tick and return whether the snake ate food."""
        if self.game_over:
            return False
        head_row, head_col = self.snake[0]
        row = head_row + self.direction[0]
        col = head_col + self.direction[1]
        head = (row, col)
        eating = head == self.food
        body = self.snake if eating else self.snake[:-1]
        if (
            row <= 0
            or row >= self.height - 1
            or col <= 0
            or col >= self.width - 1
            or head in body
            or head in self.obstacles
        ):
            self.game_over = True
            return False
        self.snake.insert(0, head)
        self.steps += 1
        if eating:
            self.score += 1
            self.food = self._place_food()
            if self.food is None:
                self.game_over = True
        else:
            self.snake.pop()
        return eating


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


def draw(stdscr: curses.window, game: SnakeGame, highscores: list[int]) -> None:
    stdscr.erase()
    stdscr.addstr(0, 0, "+" + "-" * (game.width - 2) + "+")
    title = f" Snake  Score: {game.score}  Best: {highscores[0] if highscores else 0} "
    stdscr.addstr(0, 2, title[: game.width - 4])
    for row in range(1, game.height - 1):
        stdscr.addch(row, 0, "|")
        stdscr.addch(row, game.width - 1, "|")
    stdscr.addstr(game.height - 1, 0, "+" + "-" * (game.width - 2) + "+")
    if game.food is not None:
        stdscr.addch(game.food[0], game.food[1], "*")
    for row, col in game.obstacles:
        stdscr.addch(row, col, "#")
    for index, (row, col) in enumerate(game.snake):
        stdscr.addch(row, col, "@" if index == 0 else "o")
    stdscr.addstr(game.height, 0, "Arrows/WASD move | P pause | Q quit")
    stdscr.refresh()


def pause_menu(stdscr: curses.window, game: SnakeGame) -> bool:
    message = " PAUSED — R resume | Q quit "
    row = game.height // 2
    col = max(0, (game.width - len(message)) // 2)
    stdscr.timeout(-1)
    stdscr.addstr(row, col, message, curses.A_REVERSE)
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in (ord("r"), ord("R"), ord("p"), ord("P"), 27):
            return False
        if key in (ord("q"), ord("Q")):
            return True


def play_round(stdscr: curses.window, height: int, width: int, highscores: list[int]) -> int:
    game = SnakeGame(height, width)
    while not game.game_over:
        draw(stdscr, game, highscores)
        stdscr.timeout(game.delay_ms)
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("p"), ord("P")) and pause_menu(stdscr, game):
            break
        if key in KEY_DIRECTIONS:
            game.turn(KEY_DIRECTIONS[key])
        game.step()
    return game.score


def curses_main(stdscr: curses.window, score_path: Path) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    while True:
        screen_height, screen_width = stdscr.getmaxyx()
        height, width = min(24, screen_height - 2), min(64, screen_width)
        stdscr.erase()
        if height < 5 or width < 10:
            stdscr.addstr(0, 0, "Terminal too small (minimum 10x7). Resize and restart.")
            stdscr.getch()
            return
        highscores = load_highscores(score_path)
        score = play_round(stdscr, height, width, highscores)
        highscores = save_highscore(score_path, highscores, score)
        stdscr.timeout(-1)
        stdscr.addstr(height // 2, max(0, width // 2 - 11), f" Game over! Score: {score} ", curses.A_REVERSE)
        stdscr.addstr(height // 2 + 1, max(0, width // 2 - 13), "Top 3: " + ", ".join(map(str, highscores)))
        stdscr.addstr(height // 2 + 2, max(0, width // 2 - 13), "R replay | Q quit")
        stdscr.refresh()
        if stdscr.getch() not in (ord("r"), ord("R")):
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, default=default_score_path(), help="high-score file")
    args = parser.parse_args()
    curses.wrapper(curses_main, args.scores)


if __name__ == "__main__":
    main()
