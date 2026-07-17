import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import DOWN, LEFT, RIGHT, HighScores, SnakeGame, tick_delay


class SnakeGameTests(unittest.TestCase):
    def test_snake_moves_and_cannot_reverse(self):
        game = SnakeGame(10, 20, random.Random(1))
        original_head = game.snake[0]
        game.turn(LEFT)
        game.step()
        self.assertEqual(game.direction, RIGHT)
        self.assertEqual(game.snake[0], (original_head[0], original_head[1] + 1))

    def test_eating_grows_snake_and_increases_score(self):
        game = SnakeGame(10, 20, random.Random(1))
        game.food = (game.snake[0][0], game.snake[0][1] + 1)
        self.assertTrue(game.step())
        self.assertEqual(game.score, 10)
        self.assertEqual(len(game.snake), 4)

    def test_wall_and_self_collisions_end_game(self):
        wall_game = SnakeGame(5, 8, random.Random(1))
        for _ in range(4):
            wall_game.step()
        self.assertFalse(wall_game.alive)

        self_game = SnakeGame(10, 20, random.Random(1))
        self_game.snake = [(5, 5), (5, 4), (6, 4), (6, 5), (6, 6)]
        self_game.direction = DOWN
        self_game.step()
        self.assertFalse(self_game.alive)

    def test_speed_increases_with_elapsed_time_and_has_floor(self):
        self.assertGreater(tick_delay(0), tick_delay(120))
        self.assertEqual(tick_delay(10000), 55)


class HighScoreTests(unittest.TestCase):
    def test_only_top_three_scores_are_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            scores = HighScores(path)
            for value in (10, 50, 20, 40):
                scores.record(value)
            self.assertEqual(scores.load(), [50, 40, 20])
            self.assertEqual(json.loads(path.read_text()), [50, 40, 20])

    def test_missing_or_invalid_score_file_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            scores = HighScores(path)
            self.assertEqual(scores.load(), [])
            path.write_text("not json")
            self.assertEqual(scores.load(), [])


if __name__ == "__main__":
    unittest.main()
