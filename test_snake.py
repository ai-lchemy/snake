import json
import random
import tempfile
import unittest
from pathlib import Path

from snake import SnakeGame, load_highscores, record_highscore


class SnakeGameTests(unittest.TestCase):
    def test_starts_with_snake_and_food(self):
        game = SnakeGame(12, 30, random.Random(1))
        self.assertEqual(len(game.snake), 3)
        self.assertNotIn(game.food, game.snake)

    def test_moves_without_growing(self):
        game = SnakeGame(12, 30, random.Random(1))
        original = list(game.snake)
        game.food = (1, 1)
        self.assertFalse(game.step())
        self.assertEqual(game.snake[0], (original[0][0], original[0][1] + 1))
        self.assertEqual(len(game.snake), 3)

    def test_eating_grows_scores_and_speeds_up(self):
        game = SnakeGame(12, 30, random.Random(1))
        old_delay = game.delay_ms
        head = game.snake[0]
        game.food = (head[0], head[1] + 1)
        self.assertTrue(game.step())
        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.snake), 4)
        self.assertLess(game.delay_ms, old_delay)

    def test_continued_play_speeds_up_without_eating(self):
        game = SnakeGame(12, 40, random.Random(1))
        game.food = (1, 1)
        old_delay = game.delay_ms
        for _ in range(5):
            game.step()
        self.assertFalse(game.game_over)
        self.assertLess(game.delay_ms, old_delay)

    def test_reverse_direction_is_ignored(self):
        game = SnakeGame(12, 30)
        game.change_direction((0, -1))
        self.assertEqual(game.direction, (0, 1))
        game.change_direction((-1, 0))
        self.assertEqual(game.direction, (-1, 0))

    def test_wall_collision_ends_game(self):
        game = SnakeGame(7, 12)
        game.snake = [(1, 5), (2, 5), (3, 5)]
        game.direction = (-1, 0)
        game.step()
        self.assertTrue(game.game_over)

    def test_moving_into_vacated_tail_is_allowed(self):
        game = SnakeGame(8, 12)
        game.snake = [(3, 3), (3, 2), (2, 2), (2, 3)]
        game.direction = (-1, 0)
        game.food = (1, 1)
        game.step()
        self.assertFalse(game.game_over)
        self.assertEqual(game.snake[0], (2, 3))


class HighscoreTests(unittest.TestCase):
    def test_records_only_top_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            for score in (3, 8, 5, 10):
                scores = record_highscore(path, score)
            self.assertEqual(scores, [10, 8, 5])
            self.assertEqual(json.loads(path.read_text()), [10, 8, 5])

    def test_invalid_file_is_treated_as_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text("not json")
            self.assertEqual(load_highscores(path), [])

    def test_filters_invalid_score_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scores.json"
            path.write_text('[4, -1, true, "9", 7, 2, 8]')
            self.assertEqual(load_highscores(path), [8, 7, 4])


if __name__ == "__main__":
    unittest.main()
