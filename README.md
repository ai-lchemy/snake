# Terminal Snake

A dependency-free Snake game for Python 3.10+ terminals. The snake gets faster as time passes,
and the three best scores are retained between games.

```sh
python3 snake.py
```

Use the arrow keys or WASD to steer. Press `P` (or Escape) for the pause menu and `Q` to end
the game. High scores are stored under `$XDG_DATA_HOME/terminal-snake`, or under
`~/.local/share/terminal-snake` when `XDG_DATA_HOME` is unset. Use `--scores PATH` to choose a
different file.

Run the tests with:

```sh
python3 -m unittest discover -s tests -v
```
