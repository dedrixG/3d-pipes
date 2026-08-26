# 3D Pipes

Classic Windows **3D Pipes**, as a native OpenGL screensaver for Linux.

One window per monitor. Move the mouse or press a key to exit.

![3D Pipes icon](share/icon.svg)

## Quick start

```bash
# Fedora
sudo dnf install python3-pyside6 python3-numpy

git clone https://github.com/dedrixG/3d-pipes.git
cd 3d-pipes
chmod +x start.sh
./start.sh              # fullscreen, every monitor
./start.sh --settings   # windowed preview + settings
```

`./start.sh` also installs **3D Pipes** and **3D Pipes Settings** launchers on the desktop and in the application menu.

## Controls

| | Fullscreen | Windowed / settings |
| --- | --- | --- |
| Exit | Mouse move, click, or any key | Esc |
| Restart | — | Space |
| Settings | — | S toggles the panel |

Settings are saved to `~/.config/pipes-screensaver/config.json` and used the next time you start it.

## Settings

| Setting | What it does |
| --- | --- |
| Number of pipes | How many pipes grow at once (1–8) |
| Thickness | Pipe radius |
| Speed | How fast new segments grow |
| Reset interval | `When finished` waits until pipes fill the grid; otherwise restart on a timer |
| Pause before reset | Delay after a scene ends before starting over |
| Joints | Elbow, ball, mixed, or cycling |
| Camera spin | Slow orbit |
| Smooth edges | MSAA — applies the next time you launch |

## Requirements

- Linux (Wayland or X11)
- Python 3.10+
- [PySide6](https://pypi.org/project/PySide6/) and NumPy
- OpenGL 3.3+

## License

[MIT](LICENSE)
