import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import DOWN, LEFT, RIGHT, SnakeGame, load_highscores, pause_menu, save_highscore


class FakeScreen:
    def __init__(self, keys):
        self.keys = iter(keys)

    def timeout(self, _delay):
        pass

    def addstr(self, *_args):
        pass

    def refresh(self):
        pass

    def getch(self):
        return next(self.keys)


class SnakeGameTests(unittest.TestCase):
    def test_moves_and_cannot_reverse(self):
        game = SnakeGame(10, 20, random.Random(1))
        old_head = game.snake[0]
        game.turn(LEFT)
        self.assertEqual(game.direction, RIGHT)
        game.step()
        self.assertEqual(game.snake[0], (old_head[0], old_head[1] + 1))

    def test_eating_grows_and_scores(self):
        game = SnakeGame(10, 20, random.Random(1))
        row, col = game.snake[0]
        game.food = (row, col + 1)
        old_length = len(game.snake)
        self.assertTrue(game.step())
        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.snake), old_length + 1)

    def test_collision_ends_game(self):
        game = SnakeGame(5, 10, random.Random(1))
        game.turn(DOWN)
        game.step()
        game.step()
        self.assertTrue(game.game_over)

    def test_game_speeds_up(self):
        game = SnakeGame(10, 20)
        initial = game.delay_ms
        game.steps = 120
        self.assertLess(game.delay_ms, initial)
        game.steps = 100000
        self.assertEqual(game.delay_ms, 45)

    def test_highscores_keep_top_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            scores = save_highscore(path, [3, 9, 5], 7)
            self.assertEqual(scores, [9, 7, 5])
            self.assertEqual(load_highscores(path), [9, 7, 5])
            self.assertEqual(json.loads(path.read_text()), [9, 7, 5])

    def test_malformed_highscores_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text("not json")
            self.assertEqual(load_highscores(path), [])

    def test_invalid_highscore_entries_do_not_hide_valid_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text('[4, null, "bad", -2, 8]')
            self.assertEqual(load_highscores(path), [8, 4])

    def test_pause_menu_can_resume_or_quit(self):
        game = SnakeGame(10, 20)
        self.assertFalse(pause_menu(FakeScreen([ord("r")]), game))
        self.assertTrue(pause_menu(FakeScreen([ord("q")]), game))


if __name__ == "__main__":
    unittest.main()
