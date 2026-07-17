import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import DOWN, LEFT, RIGHT, Game, load_scores, save_score, tick_delay


class GameTests(unittest.TestCase):
    def test_moves_and_cannot_reverse(self):
        game = Game(10, 12, random.Random(1))
        old_head = game.snake[0]
        game.turn(LEFT)
        game.step()
        self.assertEqual(game.snake[0], (old_head[0], old_head[1] + 1))
        game.turn(DOWN)
        game.step()
        self.assertEqual(game.direction, DOWN)

    def test_eating_grows_and_scores(self):
        game = Game(10, 12, random.Random(1))
        before = len(game.snake)
        row, col = game.snake[0]
        game.food = (row, col + 1)
        self.assertTrue(game.step())
        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.snake), before + 1)

    def test_wall_collision_ends_game(self):
        game = Game(5, 6, random.Random(1))
        for _ in range(4):
            game.step()
        self.assertTrue(game.over)

    def test_speed_increases_but_is_bounded(self):
        self.assertGreater(tick_delay(0, 0), tick_delay(20, 3))
        self.assertEqual(tick_delay(10000, 1000), 0.045)


class ScoreTests(unittest.TestCase):
    def test_keeps_top_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            for score in (2, 8, 4, 10, 1):
                result = save_score(path, score)
            self.assertEqual(result, [10, 8, 4])
            self.assertEqual(load_scores(path), [10, 8, 4])
            self.assertEqual(json.loads(path.read_text()), [10, 8, 4])

    def test_invalid_file_is_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text("not json")
            self.assertEqual(load_scores(path), [])


if __name__ == "__main__":
    unittest.main()
