import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import HighScores, SnakeGame, _pause_menu, frame_delay


class FakeWindow:
    def __init__(self, keys):
        self.keys = iter(keys)
        self.delay_modes = []

    def nodelay(self, enabled):
        self.delay_modes.append(enabled)

    def erase(self):
        pass

    def getmaxyx(self):
        return (12, 40)

    def addstr(self, *_args):
        pass

    def refresh(self):
        pass

    def getch(self):
        return next(self.keys)


class SnakeGameTests(unittest.TestCase):
    def test_moves_one_cell_and_cannot_reverse(self):
        game = SnakeGame(8, 12, random.Random(1))
        old_head = game.snake[0]
        game.turn((0, -1))
        game.step()
        self.assertEqual(game.snake[0], (old_head[0], old_head[1] + 1))

    def test_eating_grows_snake_and_scores(self):
        game = SnakeGame(8, 12, random.Random(1))
        game.food = (game.snake[0][0], game.snake[0][1] + 1)
        game.step()
        self.assertEqual(game.score, 10)
        self.assertEqual(len(game.snake), 4)
        self.assertNotIn(game.food, game.snake)

    def test_wall_collision_ends_game(self):
        game = SnakeGame(5, 8, random.Random(1))
        game.snake = [(0, 4), (1, 4), (2, 4)]
        game.direction = (-1, 0)
        game.step()
        self.assertTrue(game.game_over)

    def test_self_collision_ends_game(self):
        game = SnakeGame(8, 12, random.Random(1))
        game.snake = [(3, 4), (3, 5), (4, 5), (4, 4), (4, 3)]
        game.direction = (1, 0)
        game.step()
        self.assertTrue(game.game_over)

    def test_speed_increases_and_is_capped(self):
        self.assertGreater(frame_delay(0), frame_delay(30))
        self.assertEqual(frame_delay(10_000), 0.05)


class HighScoreTests(unittest.TestCase):
    def test_tracks_only_top_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            scores = HighScores(path)
            for score in (10, 40, 20, 30):
                scores.record(score)
            self.assertEqual(scores.load(), [40, 30, 20])
            self.assertEqual(json.loads(path.read_text()), [40, 30, 20])

    def test_invalid_score_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text("not json")
            self.assertEqual(HighScores(path).load(), [])


class PauseMenuTests(unittest.TestCase):
    def test_resume_restores_nonblocking_input(self):
        window = FakeWindow([ord("x"), ord("r")])
        self.assertTrue(_pause_menu(window))
        self.assertEqual(window.delay_modes, [False, True])

    def test_quit_restores_nonblocking_input(self):
        window = FakeWindow([ord("q")])
        self.assertFalse(_pause_menu(window))
        self.assertEqual(window.delay_modes, [False, True])


if __name__ == "__main__":
    unittest.main()
