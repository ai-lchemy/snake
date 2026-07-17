import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import HighScores, SnakeGame


class SnakeGameTests(unittest.TestCase):
    def test_moves_and_rejects_reverse(self):
        game = SnakeGame(8, 12, random.Random(1))
        old_head = game.snake[0]
        game.turn((0, -1))
        game.step()
        self.assertEqual(game.snake[0], (old_head[0], old_head[1] + 1))

    def test_eating_grows_scores_and_speeds_up(self):
        game = SnakeGame(8, 12)
        game.food = (game.snake[0][0], game.snake[0][1] + 1)
        initial_length, initial_delay = len(game.snake), game.delay_ms
        self.assertTrue(game.step())
        self.assertEqual((len(game.snake), game.score), (initial_length + 1, 1))
        self.assertLess(game.delay_ms, initial_delay)

    def test_wall_collision_ends_game(self):
        game = SnakeGame(5, 8)
        game.snake = [(2, 7), (2, 6), (2, 5)]
        game.step()
        self.assertFalse(game.alive)

    def test_can_move_into_vacating_tail(self):
        game = SnakeGame(6, 8)
        game.snake = [(2, 2), (2, 1), (1, 1), (1, 2)]
        game.direction = (-1, 0)
        game.food = (5, 7)
        game.step()
        self.assertTrue(game.alive)


class HighScoreTests(unittest.TestCase):
    def test_records_only_top_three(self):
        with tempfile.TemporaryDirectory() as directory:
            store = HighScores(Path(directory) / "scores.json")
            for score in (2, 9, 4, 7):
                result = store.record(score)
            self.assertEqual(result, [9, 7, 4])
            self.assertEqual(json.loads(store.path.read_text()), [9, 7, 4])

    def test_bad_file_is_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text("not json")
            self.assertEqual(HighScores(path).load(), [])


if __name__ == "__main__":
    unittest.main()
