# Terminal Snake

A dependency-free Snake game for Python 3.10 or newer.

```sh
python3 snake.py
```

Move with the arrow keys or WASD. Press `P` for the pause menu and `Q` to quit.
Avoid the `#` obstacles scattered around the board. The snake becomes faster as
the round continues. The best three scores persist in
`~/.snake_highscores.json`; use `--scores PATH` to choose another location.

Run the tests with:

```sh
python3 -m unittest -v
```
