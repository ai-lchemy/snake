# Terminal Snake

A dependency-free Snake game for Python 3.10 or newer.

```sh
python3 snake.py
```

Use the arrow keys to steer, `P` to open the pause menu, and `Q` to quit. The
snake accelerates every 15 seconds. The top three scores persist in
`$XDG_DATA_HOME/snake/highscores.json` (or `~/.local/share/snake/highscores.json`).

Run the tests with:

```sh
python3 -m unittest -v
```
