# Terminal Snake

A dependency-free Python Snake game with increasing speed, a persistent top-three
high-score table, and a pause menu.

Run it in a terminal (at least 30 columns by 12 rows):

```sh
python3 snake.py
```

Use the arrow keys or WASD to move. Press **P** for the pause menu, which can
resume, restart, or quit the game. Press **Q** to quit. Scores are stored in
`~/.snake_highscores.json`; use `--scores PATH` to choose another location.

Run the tests with:

```sh
python3 -m unittest -v
```
