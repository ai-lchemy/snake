#!/usr/bin/env python3
"""A small, dependency-free terminal Snake game."""

from __future__ import annotations

import argparse
import curses
import json
import random
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def default_score_path() -> Path:
    return Path.home() / ".snake_highscores.json"


def load_scores(path: Path) -> list[int]:
    """Read the three best scores, tolerating missing or damaged files."""
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
        scores = [int(value) for value in values if int(value) >= 0]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return []
    return sorted(scores, reverse=True)[:3]


def save_score(path: Path, score: int) -> list[int]:
    scores = sorted(load_scores(path) + [max(0, int(score))], reverse=True)[:3]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scores), encoding="utf-8")
    except OSError:
        pass  # A read-only home directory should not prevent playing.
    return scores


def tick_delay(elapsed: float, score: int) -> float:
    """Return a progressively shorter delay, with a playable lower bound."""
    return max(0.045, 0.16 - elapsed * 0.002 - score * 0.0015)


@dataclass
class Game:
    height: int
    width: int
    rng: random.Random = field(default_factory=random.Random)
    snake: deque[tuple[int, int]] = field(init=False)
    direction: tuple[int, int] = field(default=RIGHT, init=False)
    food: tuple[int, int] | None = field(default=None, init=False)
    score: int = field(default=0, init=False)
    over: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        row, col = self.height // 2, self.width // 2
        self.snake = deque([(row, col), (row, col - 1), (row, col - 2)])
        self.place_food()

    def place_food(self) -> None:
        free = [
            (row, col)
            for row in range(self.height)
            for col in range(self.width)
            if (row, col) not in self.snake
        ]
        self.food = self.rng.choice(free) if free else None
        if not free:
            self.over = True

    def turn(self, direction: tuple[int, int]) -> None:
        if direction != OPPOSITE[self.direction]:
            self.direction = direction

    def step(self) -> bool:
        """Advance one cell and return whether food was eaten."""
        if self.over:
            return False
        row, col = self.snake[0]
        dr, dc = self.direction
        head = (row + dr, col + dc)
        growing = head == self.food
        body = self.snake if growing else list(self.snake)[:-1]
        if not (0 <= head[0] < self.height and 0 <= head[1] < self.width) or head in body:
            self.over = True
            return False
        self.snake.appendleft(head)
        if growing:
            self.score += 1
            self.place_food()
        else:
            self.snake.pop()
        return growing


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


def center(window: curses.window, row: int, text: str, attr: int = 0) -> None:
    height, width = window.getmaxyx()
    if 0 <= row < height and width > 1:
        clipped = text[: width - 1]
        window.addstr(row, max(0, (width - len(clipped)) // 2), clipped, attr)


def pause_menu(screen: curses.window) -> str:
    options = [("Resume", "resume"), ("Restart", "restart"), ("Quit", "quit")]
    selected = 0
    screen.timeout(-1)
    while True:
        screen.erase()
        height, _ = screen.getmaxyx()
        center(screen, max(1, height // 2 - 3), "PAUSED", curses.A_BOLD)
        for index, (label, _) in enumerate(options):
            attr = curses.A_REVERSE if index == selected else 0
            center(screen, max(2, height // 2 - 1 + index), label, attr)
        center(screen, max(5, height // 2 + 3), "Up/Down + Enter (or P to resume)")
        screen.refresh()
        key = screen.getch()
        if key in (curses.KEY_UP, ord("w")):
            selected = (selected - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord("s")):
            selected = (selected + 1) % len(options)
        elif key in (10, 13, curses.KEY_ENTER):
            return options[selected][1]
        elif key in (ord("p"), ord("P"), 27):
            return "resume"


def draw(screen: curses.window, game: Game, scores: Iterable[int]) -> None:
    screen.erase()
    screen.addstr(0, 1, f" Score: {game.score}   P: pause   Q: quit ", curses.A_BOLD)
    top = list(scores)
    if top:
        label = "Top 3: " + ", ".join(map(str, top))
        _, width = screen.getmaxyx()
        screen.addstr(0, max(1, width - len(label) - 2), label[: max(0, width - 2)])
    for col in range(game.width + 2):
        screen.addch(1, col, "#")
        screen.addch(game.height + 2, col, "#")
    for row in range(game.height + 2):
        screen.addch(row + 1, 0, "#")
        screen.addch(row + 1, game.width + 1, "#")
    if game.food is not None:
        screen.addch(game.food[0] + 2, game.food[1] + 1, "*")
    for index, (row, col) in enumerate(game.snake):
        screen.addch(row + 2, col + 1, "@" if index == 0 else "o")
    screen.refresh()


def wait_for_size(screen: curses.window) -> tuple[int, int] | None:
    while True:
        height, width = screen.getmaxyx()
        if height >= 12 and width >= 30:
            return min(22, height - 4), min(60, width - 2)
        screen.erase()
        center(screen, height // 2, "Terminal too small (minimum 30x12). Resize or press Q.")
        screen.refresh()
        screen.timeout(250)
        if screen.getch() in (ord("q"), ord("Q")):
            return None


def run(screen: curses.window, score_path: Path) -> None:
    curses.curs_set(0)
    screen.keypad(True)
    while True:
        dimensions = wait_for_size(screen)
        if dimensions is None:
            return
        game = Game(*dimensions)
        started = time.monotonic()
        paused_for = 0.0
        while not game.over:
            scores = load_scores(score_path)
            draw(screen, game, scores)
            elapsed = time.monotonic() - started - paused_for
            screen.timeout(max(1, int(tick_delay(elapsed, game.score) * 1000)))
            key = screen.getch()
            if key in KEY_DIRECTIONS:
                game.turn(KEY_DIRECTIONS[key])
            elif key in (ord("p"), ord("P")):
                pause_started = time.monotonic()
                action = pause_menu(screen)
                paused_for += time.monotonic() - pause_started
                if action == "quit":
                    return
                if action == "restart":
                    break
                continue
            elif key in (ord("q"), ord("Q")):
                return
            game.step()
        else:
            scores = save_score(score_path, game.score)
            draw(screen, game, scores)
            center(screen, game.height // 2 + 1, "GAME OVER", curses.A_BOLD)
            center(screen, game.height // 2 + 3, "R: restart   Q: quit")
            screen.timeout(-1)
            while True:
                key = screen.getch()
                if key in (ord("r"), ord("R")):
                    break
                if key in (ord("q"), ord("Q"), 27):
                    return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play Snake in your terminal")
    parser.add_argument("--scores", type=Path, default=default_score_path(), help="high-score file")
    args = parser.parse_args(argv)
    try:
        curses.wrapper(run, args.scores)
    except curses.error:
        parser.error("Snake needs an interactive terminal at least 30 columns by 12 rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
