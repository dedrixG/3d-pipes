#!/usr/bin/env python3
"""Native 3D Pipes screensaver — no browser, no server."""
from __future__ import annotations

import argparse
import faulthandler
import json
import math
import os
import random
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import (
    QEvent,
    QObject,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QCursor,
    QGuiApplication,
    QIcon,
    QMatrix4x4,
    QOpenGLFunctions,
    QQuaternion,
    QSurfaceFormat,
    QVector3D,
    QVector4D,
)
from PySide6.QtOpenGL import (
    QOpenGLBuffer,
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLVertexArrayObject,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

CELL = 1.0
GRID = 16
MAX_PIECES = 520
STRAIGHT_BIAS = 0.78
JOIN_OVERLAP = 0.16
ROOT = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / ".config" / "pipes-screensaver"
CONFIG_PATH = CONFIG_DIR / "config.json"
STATE_DIR = Path.home() / ".local" / "state" / "pipes-screensaver"

DEFAULTS = {
    "pipe_count": 3,
    "thickness": 0.33,
    "speed": 8.5,
    "reset_seconds": 0.0,
    "reset_delay": 0.9,
    "joints": "mixed",
    "spin": True,
    "multisample": True,
}

PALETTE = [
    QVector3D(0.89, 0.13, 0.13),
    QVector3D(0.13, 0.69, 0.23),
    QVector3D(0.13, 0.35, 0.88),
    QVector3D(0.88, 0.75, 0.09),
    QVector3D(0.82, 0.13, 0.72),
    QVector3D(0.09, 0.75, 0.82),
    QVector3D(0.88, 0.41, 0.07),
    QVector3D(0.94, 0.94, 0.94),
    QVector3D(0.56, 0.16, 0.88),
    QVector3D(0.25, 0.88, 0.56),
]
DIRS = (
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
)
Y_UP = QVector3D(0, 1, 0)

VERT = """
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
uniform mat4 uMVP;
uniform mat4 uModel;
uniform mat3 uNormal;
out vec3 vN;
out vec3 vW;
void main() {
    vec4 world = uModel * vec4(aPos, 1.0);
    vW = world.xyz;
    vN = normalize(uNormal * aNormal);
    gl_Position = uMVP * vec4(aPos, 1.0);
}
"""

FRAG = """
#version 330 core
in vec3 vN;
in vec3 vW;
uniform vec3 uColor;
uniform vec3 uEye;
uniform vec3 uLight;
out vec4 FragColor;
void main() {
    vec3 n = normalize(vN);
    if (!gl_FrontFacing) n = -n;
    vec3 l = normalize(uLight);
    vec3 v = normalize(uEye - vW);
    vec3 h = normalize(l + v);
    float diff = max(dot(n, l), 0.0);
    float spec = pow(max(dot(n, h), 0.0), 56.0);
    float fill = max(dot(n, normalize(vec3(-0.4, -0.1, -0.3))), 0.0) * 0.22;
    vec3 col = uColor * (0.22 + diff * 0.80 + fill) + vec3(1.0) * spec * 0.55;
    FragColor = vec4(col, 1.0);
}
"""


def _clamp(val, lo, hi):
    return lo if val < lo else hi if val > hi else val


def sanitize_config(raw: dict | None) -> dict:
    src = raw if isinstance(raw, dict) else {}
    joints = src.get("joints", DEFAULTS["joints"])
    if joints not in {"elbow", "ball", "mixed", "cycle"}:
        joints = DEFAULTS["joints"]
    return {
        "pipe_count": int(_clamp(int(src.get("pipe_count", DEFAULTS["pipe_count"])), 1, 8)),
        "thickness": float(_clamp(float(src.get("thickness", DEFAULTS["thickness"])), 0.16, 0.48)),
        "speed": float(_clamp(float(src.get("speed", DEFAULTS["speed"])), 2.0, 20.0)),
        "reset_seconds": float(_clamp(float(src.get("reset_seconds", DEFAULTS["reset_seconds"])), 0.0, 300.0)),
        "reset_delay": float(_clamp(float(src.get("reset_delay", DEFAULTS["reset_delay"])), 0.2, 5.0)),
        "joints": joints,
        "spin": bool(src.get("spin", DEFAULTS["spin"])),
        "multisample": bool(src.get("multisample", DEFAULTS["multisample"])),
    }


def load_config() -> dict:
    try:
        return sanitize_config(json.loads(CONFIG_PATH.read_text()))
    except FileNotFoundError:
        return dict(DEFAULTS)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return dict(DEFAULTS)


def save_config(cfg: dict) -> None:
    cfg = sanitize_config(cfg)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n")
    tmp.replace(CONFIG_PATH)


def _v(a) -> QVector3D:
    if isinstance(a, QVector3D):
        return a
    return QVector3D(float(a[0]), float(a[1]), float(a[2]))


def cell_world(cell) -> QVector3D:
    o = (GRID - 1) / 2.0
    return QVector3D(
        (cell[0] - o) * CELL,
        (cell[1] - o) * CELL,
        (cell[2] - o) * CELL,
    )


def add_dir(cell, d):
    return (cell[0] + d[0], cell[1] + d[1], cell[2] + d[2])


def dir_eq(a, b) -> bool:
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]


def cylinder_model(p0: QVector3D, p1: QVector3D, radius: float) -> QMatrix4x4 | None:
    d = p1 - p0
    length = d.length()
    if length < 1e-5:
        return None
    mid = (p0 + p1) * 0.5
    m = QMatrix4x4()
    m.translate(mid)
    m.rotate(QQuaternion.rotationTo(Y_UP, d / length))
    m.scale(radius, length, radius)
    return m


def sphere_model(pos: QVector3D, radius: float) -> QMatrix4x4:
    m = QMatrix4x4()
    m.translate(pos)
    m.scale(radius, radius, radius)
    return m


def elbow_model(cell, from_dir, to_dir) -> QMatrix4x4:
    h = CELL * 0.5
    c = cell_world(cell)
    pos = QVector3D(
        c.x() - from_dir[0] * h + to_dir[0] * h,
        c.y() - from_dir[1] * h + to_dir[1] * h,
        c.z() - from_dir[2] * h + to_dir[2] * h,
    )
    x = QVector3D(-to_dir[0], -to_dir[1], -to_dir[2]).normalized()
    y = QVector3D(float(from_dir[0]), float(from_dir[1]), float(from_dir[2])).normalized()
    z = QVector3D.crossProduct(x, y).normalized()
    y = QVector3D.crossProduct(z, x).normalized()
    m = QMatrix4x4()
    m.setColumn(0, QVector4D(x, 0.0))
    m.setColumn(1, QVector4D(y, 0.0))
    m.setColumn(2, QVector4D(z, 0.0))
    m.setColumn(3, QVector4D(pos, 1.0))
    return m


def _disc_cap(verts, idx, y: float, ny: float, slices: int) -> None:
    center = len(verts)
    verts.append((0.0, y, 0.0, 0.0, ny, 0.0))
    ring = []
    for i in range(slices):
        a = 2.0 * math.pi * i / slices
        x, z = math.cos(a), math.sin(a)
        ring.append(len(verts))
        verts.append((x, y, z, 0.0, ny, 0.0))
    for i in range(slices):
        a = ring[i]
        b = ring[(i + 1) % slices]
        if ny >= 0.0:
            idx.extend((center, a, b))
        else:
            idx.extend((center, b, a))


def make_cylinder(slices: int = 32):
    verts = []
    idx = []
    for i in range(slices + 1):
        a = 2.0 * math.pi * i / slices
        x, z = math.cos(a), math.sin(a)
        verts.append((x, -0.5, z, x, 0.0, z))
        verts.append((x, 0.5, z, x, 0.0, z))
    for i in range(slices):
        i0 = 2 * i
        i1 = i0 + 1
        i2 = i0 + 2
        i3 = i0 + 3
        idx.extend((i0, i2, i1, i1, i2, i3))
    _disc_cap(verts, idx, -0.5, -1.0, slices)
    _disc_cap(verts, idx, 0.5, 1.0, slices)
    return (
        np.array(verts, dtype=np.float32),
        np.array(idx, dtype=np.uint32),
    )


def make_sphere(slices: int = 24, stacks: int = 16):
    verts = []
    idx = []
    for i in range(stacks + 1):
        v = i / stacks
        phi = math.pi * v
        sp, cp = math.sin(phi), math.cos(phi)
        for j in range(slices + 1):
            u = j / slices
            th = 2.0 * math.pi * u
            x = sp * math.cos(th)
            y = cp
            z = sp * math.sin(th)
            verts.append((x, y, z, x, y, z))
    cols = slices + 1
    for i in range(stacks):
        for j in range(slices):
            a = i * cols + j
            b = a + cols
            idx.extend((a, b, a + 1, a + 1, b, b + 1))
    return (
        np.array(verts, dtype=np.float32),
        np.array(idx, dtype=np.uint32),
    )


def make_elbow(major: float, tube: float, radial: int = 20, tubular: int = 20):
    verts = []
    idx = []
    arc = math.pi / 2.0
    for i in range(tubular + 1):
        u = arc * i / tubular
        cu, su = math.cos(u), math.sin(u)
        for j in range(radial + 1):
            v = 2.0 * math.pi * j / radial
            cv, sv = math.cos(v), math.sin(v)
            cx = (major + tube * cv) * cu
            cy = (major + tube * cv) * su
            cz = tube * sv
            nx = cv * cu
            ny = cv * su
            nz = sv
            verts.append((cx, cy, cz, nx, ny, nz))
    cols = radial + 1
    for i in range(tubular):
        for j in range(radial):
            a = i * cols + j
            b = a + cols
            idx.extend((a, b, a + 1, a + 1, b, b + 1))

    def elbow_cap(u: float, normal: tuple[float, float, float]) -> None:
        cu, su = math.cos(u), math.sin(u)
        nx, ny, nz = normal
        center = len(verts)
        verts.append((major * cu, major * su, 0.0, nx, ny, nz))
        ring = []
        for j in range(radial):
            v = 2.0 * math.pi * j / radial
            cv, sv = math.cos(v), math.sin(v)
            ring.append(len(verts))
            verts.append(
                (
                    (major + tube * cv) * cu,
                    (major + tube * cv) * su,
                    tube * sv,
                    nx,
                    ny,
                    nz,
                )
            )
        for j in range(radial):
            a = ring[j]
            b = ring[(j + 1) % radial]
            idx.extend((center, a, b))

    elbow_cap(0.0, (0.0, -1.0, 0.0))
    elbow_cap(arc, (-1.0, 0.0, 0.0))
    return (
        np.array(verts, dtype=np.float32),
        np.array(idx, dtype=np.uint32),
    )


@dataclass
class DrawItem:
    kind: str
    model: QMatrix4x4
    color: QVector3D
    visible: bool = True


class Occupancy:
    def __init__(self):
        self.cells: set[tuple[int, int, int]] = set()

    def in_bounds(self, c) -> bool:
        return 0 <= c[0] < GRID and 0 <= c[1] < GRID and 0 <= c[2] < GRID

    def free(self, c) -> bool:
        return self.in_bounds(c) and c not in self.cells

    def take(self, c) -> None:
        self.cells.add(c)

    def clear(self) -> None:
        self.cells.clear()


def prefer_straight(options, incoming):
    straight = [d for d in options if dir_eq(d, incoming)]
    if straight and random.random() < STRAIGHT_BIAS:
        return straight[0]
    return random.choice(options)


class Pipe:
    def __init__(self, sim: PipesSim):
        self.sim = sim
        self.world = sim.world
        self.items = sim.items
        self.color = random.choice(PALETTE)
        self.path: list[tuple[int, int, int]] = []
        self.alive = True
        self.last_exit = QVector3D()
        self.last_dir = (1, 0, 0)
        self.growing = None
        self.grow_t = 0.0
        self.head = None
        self.shaft: DrawItem | None = None
        self.shaft_from = QVector3D()
        self.tip: DrawItem | None = None

    @property
    def radius(self) -> float:
        return self.sim.radius

    def spawn(self) -> bool:
        mid = (GRID - 1) / 2.0

        def spread() -> int:
            v = int(mid + (random.random() + random.random() - 1.0) * GRID * 0.32)
            return max(1, min(GRID - 2, v))

        for _ in range(80):
            s = (spread(), spread(), spread())
            if not self.world.free(s):
                continue
            options = [d for d in DIRS if self.world.free(add_dir(s, d))]
            if not options:
                continue
            d1 = random.choice(options)
            b = add_dir(s, d1)
            options2 = [
                d
                for d in DIRS
                if not (d[0] == -d1[0] and d[1] == -d1[1] and d[2] == -d1[2])
                and self.world.free(add_dir(b, d))
            ]
            if not options2:
                continue
            d2 = prefer_straight(options2, d1)
            c = add_dir(b, d2)
            self.world.take(s)
            self.world.take(b)
            self.world.take(c)
            self.path = [s, b]
            self.head = c
            self.last_dir = d2
            self.last_exit = cell_world(s)
            self.add_cap(s, 1.28)
            self.tip = DrawItem(
                "sphere",
                sphere_model(self.last_exit, self.radius * 1.16),
                self.color,
            )
            self.items.append(self.tip)
            joint = self.sim.pick_joint(not dir_eq(d1, d2))
            self.begin_segment(b, d1, d2, joint)
            self.path.append(c)
            return True
        self.alive = False
        return False

    def add_cap(self, cell, scale=1.12) -> DrawItem:
        item = DrawItem("sphere", sphere_model(cell_world(cell), self.radius * scale), self.color)
        self.items.append(item)
        return item

    def add_ball(self, cell) -> DrawItem:
        return self.add_cap(cell, 1.52)

    def add_elbow(self, cell, from_dir, to_dir) -> DrawItem:
        item = DrawItem("elbow", elbow_model(cell, from_dir, to_dir), self.color)
        self.items.append(item)
        c = cell_world(cell)
        h = CELL * 0.5
        plug = self.radius * 1.06
        p_in = QVector3D(
            c.x() - from_dir[0] * h,
            c.y() - from_dir[1] * h,
            c.z() - from_dir[2] * h,
        )
        p_out = QVector3D(
            c.x() + to_dir[0] * h,
            c.y() + to_dir[1] * h,
            c.z() + to_dir[2] * h,
        )
        self.items.append(DrawItem("sphere", sphere_model(p_in, plug), self.color))
        self.items.append(DrawItem("sphere", sphere_model(p_out, plug), self.color))
        return item

    def _set_cyl(self, item: DrawItem, p0: QVector3D, p1: QVector3D) -> None:
        mdl = cylinder_model(p0, p1, self.radius)
        if mdl is None:
            item.visible = False
        else:
            item.model = mdl
            item.visible = True

    def _place_tip(self, pos: QVector3D) -> None:
        if self.tip is None:
            return
        self.tip.model = sphere_model(pos, self.radius * 1.16)
        self.tip.visible = True

    def begin_segment(self, b, dir_in, dir_out, joint) -> None:
        origin = QVector3D(self.last_exit)
        b_world = cell_world(b)
        overlap = min(JOIN_OVERLAP, self.radius * 0.55)
        if joint == "elbow":
            hin = _v(dir_in) * (CELL * 0.5 - overlap)
            hout = _v(dir_out) * (CELL * 0.5 - overlap)
            entry = b_world - hin
            exit_p = b_world + hout
        else:
            entry = QVector3D(b_world)
            exit_p = QVector3D(b_world)

        if self.shaft is not None:
            item = self.shaft
            shaft_from = QVector3D(self.shaft_from)
        else:
            item = DrawItem("cyl", QMatrix4x4(), self.color, visible=False)
            self.items.append(item)
            self.shaft = item
            self.shaft_from = QVector3D(origin)
            shaft_from = QVector3D(origin)

        self._set_cyl(item, shaft_from, origin)
        self.growing = {
            "item": item,
            "shaft_from": shaft_from,
            "from": origin,
            "to": entry,
            "joint": joint,
            "cell": b,
            "dir_in": dir_in,
            "dir_out": dir_out,
            "exit": exit_p,
        }
        self.grow_t = 0.0
        if origin.distanceToPoint(entry) < 1e-5:
            self.finish_growing()

    def finish_growing(self) -> None:
        g = self.growing
        if g is None:
            return
        self._set_cyl(g["item"], g["shaft_from"], g["to"])
        if g["joint"] == "ball":
            self.add_ball(g["cell"])
            self.shaft = None
        elif g["joint"] == "elbow":
            self.add_elbow(g["cell"], g["dir_in"], g["dir_out"])
            self.shaft = None
        self.last_exit = QVector3D(g["exit"])
        self._place_tip(self.last_exit)
        self.growing = None

    def candidates(self, from_cell, incoming):
        out = []
        for d in DIRS:
            if incoming and d[0] == -incoming[0] and d[1] == -incoming[1] and d[2] == -incoming[2]:
                continue
            if self.world.free(add_dir(from_cell, d)):
                out.append(d)
        return out

    def step(self) -> None:
        b = self.head
        a = self.path[-2]
        dir_in = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        options = self.candidates(b, dir_in)
        if not options:
            self.die()
            return
        dir_out = prefer_straight(options, dir_in)
        c = add_dir(b, dir_out)
        self.world.take(c)
        joint = self.sim.pick_joint(not dir_eq(dir_in, dir_out))
        self.begin_segment(b, dir_in, dir_out, joint)
        self.path.append(c)
        self.head = c
        self.last_dir = dir_out

    def die(self) -> None:
        self.alive = False
        b = self.head or (self.path[-1] if self.path else None)
        if b is None:
            return
        origin = QVector3D(self.last_exit)
        dest = cell_world(b)
        if self.shaft is not None:
            item = self.shaft
            shaft_from = QVector3D(self.shaft_from)
        else:
            item = DrawItem("cyl", QMatrix4x4(), self.color, visible=False)
            self.items.append(item)
            shaft_from = QVector3D(origin)
        self.growing = {
            "item": item,
            "shaft_from": shaft_from,
            "from": origin,
            "to": dest,
            "joint": "ball",
            "cell": b,
            "dir_in": self.last_dir,
            "dir_out": self.last_dir,
            "exit": dest,
        }
        self.grow_t = 0.0

    def update(self, dt: float) -> None:
        self.grow_t += dt * self.sim.speed
        budget = 12
        while budget > 0:
            budget -= 1
            if self.growing:
                if self.grow_t >= 1.0:
                    self.grow_t -= 1.0
                    dying = not self.alive
                    self.finish_growing()
                    if not dying and self.alive:
                        self.step()
                    continue
                t = self.grow_t * self.grow_t * (3.0 - 2.0 * self.grow_t)
                cur = self.growing["from"] + (self.growing["to"] - self.growing["from"]) * max(0.0, t)
                self._set_cyl(self.growing["item"], self.growing["shaft_from"], cur)
                self._place_tip(cur)
                break
            if self.alive:
                self.step()
                continue
            break


class PipesSim(QObject):
    ticked = Signal()

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = sanitize_config(cfg)
        self.world = Occupancy()
        self.items: list[DrawItem] = []
        self.pipes: list[Pipe] = []
        self.cam_angle = 0.55
        self.cam_elev = 0.42
        self.reset_at = 0.0
        self.started_at = 0.0
        self.last_t = time.perf_counter()
        self.cycle_index = 0
        self.gl_ready = False
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

    @property
    def radius(self) -> float:
        return self.cfg["thickness"]

    @property
    def speed(self) -> float:
        return self.cfg["speed"]

    def apply_config(self, cfg: dict, restart: bool = True) -> None:
        self.cfg = sanitize_config(cfg)
        save_config(self.cfg)
        if restart:
            self.restart()

    def pick_joint(self, is_turn: bool) -> str:
        if not is_turn:
            return "straight"
        joints = self.cfg["joints"]
        if joints == "cycle":
            types = ("elbow", "ball")
            choice = types[self.cycle_index % 2]
            self.cycle_index += 1
            return choice
        if joints == "elbow":
            return "elbow"
        if joints == "ball":
            return "ball"
        return "ball" if random.random() < 1.0 / 3.0 else "elbow"

    def restart(self) -> None:
        self.items.clear()
        self.world.clear()
        self.pipes = []
        self.reset_at = 0.0
        self.started_at = time.perf_counter()
        self.cycle_index = 0
        for _ in range(self.cfg["pipe_count"]):
            p = Pipe(self)
            if p.spawn():
                self.pipes.append(p)
        if not self.pipes:
            p = Pipe(self)
            if p.spawn():
                self.pipes.append(p)

    def start(self) -> None:
        if not self.timer.isActive():
            self.last_t = time.perf_counter()
            self.timer.start()

    def _tick(self) -> None:
        now = time.perf_counter()
        dt = min(0.12, now - self.last_t)
        self.last_t = now
        if self.gl_ready:
            for p in self.pipes:
                p.update(dt)
            living = any(p.alive or p.growing for p in self.pipes)
            too_big = len(self.items) > MAX_PIECES
            reset_every = self.cfg["reset_seconds"]
            if reset_every > 0.0 and now - self.started_at >= reset_every:
                self.restart()
            elif not living or too_big:
                if self.reset_at == 0.0:
                    self.reset_at = now + self.cfg["reset_delay"]
                elif now >= self.reset_at:
                    self.restart()
            else:
                self.reset_at = 0.0
            if self.cfg["spin"]:
                self.cam_angle += dt * 0.22
        self.ticked.emit()


GL_FLOAT = 0x1406
GL_TRIANGLES = 0x0004
GL_COLOR_BUFFER_BIT = 0x00004000
GL_DEPTH_BUFFER_BIT = 0x00000100
GL_DEPTH_TEST = 0x0B71
GL_CULL_FACE = 0x0B44
GL_CCW = 0x0901


class Mesh:
    def __init__(self, verts: np.ndarray, indices: np.ndarray, prog: QOpenGLShaderProgram):
        verts = np.ascontiguousarray(verts, dtype=np.float32)
        indices = np.ascontiguousarray(indices, dtype=np.uint32)
        packed = np.ascontiguousarray(verts[indices], dtype=np.float32)
        self.count = int(packed.shape[0])
        self.vao = QOpenGLVertexArrayObject()
        self.vao.create()
        self.vbo = QOpenGLBuffer(QOpenGLBuffer.Type.VertexBuffer)
        self.vbo.create()
        self.vao.bind()
        self.vbo.bind()
        payload = packed.tobytes()
        self.vbo.allocate(len(payload))
        self.vbo.write(0, payload, len(payload))
        prog.enableAttributeArray(0)
        prog.setAttributeBuffer(0, GL_FLOAT, 0, 3, 24)
        prog.enableAttributeArray(1)
        prog.setAttributeBuffer(1, GL_FLOAT, 12, 3, 24)
        self.vao.release()
        self.vbo.release()

    def draw(self, gl) -> None:
        self.vao.bind()
        gl.glDrawArrays(GL_TRIANGLES, 0, self.count)
        self.vao.release()

    def destroy(self) -> None:
        self.vao.destroy()
        self.vbo.destroy()


class PipesWidget(QOpenGLWidget):
    def __init__(self, sim: PipesSim, windowed: bool = False):
        super().__init__()
        self.sim = sim
        self.windowed = windowed
        self.gl: QOpenGLFunctions | None = None
        self.prog: QOpenGLShaderProgram | None = None
        self.meshes: dict[str, Mesh] = {}
        self._elbow_radius = 0.0
        self._ready = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFormat(make_surface_format(sim.cfg["multisample"]))
        if not windowed:
            self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        self.sim.ticked.connect(self.update)

    def initializeGL(self) -> None:
        try:
            self._initialize_gl()
        except Exception:
            traceback.print_exc()
            self._ready = False
            QTimer.singleShot(0, lambda: self._fail("OpenGL failed to start. See the terminal for details."))

    def _fail(self, msg: str) -> None:
        QMessageBox.critical(self.window(), "3D Pipes", msg)
        QApplication.quit()

    def _initialize_gl(self) -> None:
        ctx = self.context()
        if ctx is None:
            raise RuntimeError("No OpenGL context")
        gl = ctx.functions()
        if gl is None:
            raise RuntimeError("OpenGL functions unavailable")
        gl.initializeOpenGLFunctions()
        self.gl = gl
        gl.glEnable(GL_DEPTH_TEST)
        gl.glDisable(GL_CULL_FACE)
        gl.glFrontFace(GL_CCW)
        gl.glClearColor(0.0, 0.0, 0.0, 1.0)

        self.prog = QOpenGLShaderProgram(self)
        if not self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERT):
            raise RuntimeError(self.prog.log() or "vertex shader failed")
        if not self.prog.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAG):
            raise RuntimeError(self.prog.log() or "fragment shader failed")
        self.prog.bindAttributeLocation("aPos", 0)
        self.prog.bindAttributeLocation("aNormal", 1)
        if not self.prog.link():
            raise RuntimeError(self.prog.log() or "shader link failed")
        self.prog.bind()

        self.meshes["cyl"] = Mesh(*make_cylinder(), self.prog)
        self.meshes["sphere"] = Mesh(*make_sphere(), self.prog)
        self._rebuild_elbow()
        if not self.sim.gl_ready:
            self.sim.restart()
            self.sim.gl_ready = True
        self.sim.start()
        self._ready = True
        fmt = ctx.format()
        print(
            f"3D Pipes  OpenGL ready  {fmt.majorVersion()}.{fmt.minorVersion()}  "
            f"samples={fmt.samples()}",
            flush=True,
        )

    def _rebuild_elbow(self) -> None:
        old = self.meshes.pop("elbow", None)
        if old is not None:
            old.destroy()
        self.meshes["elbow"] = Mesh(*make_elbow(CELL * 0.5, self.sim.radius * 1.04), self.prog)
        self._elbow_radius = self.sim.radius

    def resizeGL(self, w: int, h: int) -> None:
        if self.gl is not None:
            self.gl.glViewport(0, 0, max(1, w), max(1, h))

    def paintGL(self) -> None:
        try:
            self._paint_gl()
        except Exception:
            traceback.print_exc()
            self._ready = False

    def _paint_gl(self) -> None:
        if self.gl is None:
            return
        self.gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if not self._ready or self.prog is None:
            return
        if abs(self._elbow_radius - self.sim.radius) > 1e-6:
            self._rebuild_elbow()

        w = max(1, self.width())
        h = max(1, self.height())
        half = GRID * CELL * 0.58
        v_fov = math.radians(56.0)
        dist = (half / math.tan(v_fov / 2.0)) * 1.08
        eye = QVector3D(
            dist * math.cos(self.sim.cam_elev) * math.sin(self.sim.cam_angle),
            dist * math.sin(self.sim.cam_elev),
            dist * math.cos(self.sim.cam_elev) * math.cos(self.sim.cam_angle),
        )
        view = QMatrix4x4()
        view.lookAt(eye, QVector3D(0, 0, 0), Y_UP)
        proj = QMatrix4x4()
        proj.perspective(56.0, w / float(h), 0.1, 250.0)

        self.prog.bind()
        self.prog.setUniformValue("uEye", eye)
        self.prog.setUniformValue("uLight", QVector3D(0.45, 0.82, 0.40).normalized())

        for item in self.sim.items:
            if not item.visible:
                continue
            mvp = proj * view * item.model
            self.prog.setUniformValue("uMVP", mvp)
            self.prog.setUniformValue("uModel", item.model)
            self.prog.setUniformValue("uNormal", item.model.normalMatrix())
            self.prog.setUniformValue("uColor", item.color)
            mesh = self.meshes.get(item.kind)
            if mesh is not None:
                mesh.draw(self.gl)

        self.prog.release()

    def keyPressEvent(self, event) -> None:
        if not self.windowed:
            return
        key = event.key()
        if key == Qt.Key.Key_Escape:
            win = self.window()
            if isinstance(win, PreviewWindow) and win.settings_visible():
                win.set_settings_visible(False)
                return
            QApplication.quit()
        elif key == Qt.Key.Key_Space:
            self.sim.restart()
        elif key == Qt.Key.Key_S:
            win = self.window()
            if isinstance(win, PreviewWindow):
                win.toggle_settings()


class ScreensaverGuard(QObject):
    """Ignore the click that launched us; quit only on real input after a short grace."""

    def __init__(self, grace_s: float = 2.8, parent=None):
        super().__init__(parent)
        self.armed_at = time.perf_counter() + grace_s
        self.origin = None

    def eventFilter(self, obj, event) -> bool:
        et = event.type()
        if et not in (
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
            QEvent.Type.Wheel,
        ):
            return False
        now = time.perf_counter()
        if et == QEvent.Type.MouseMove:
            pos = event.globalPosition()
            if self.origin is None:
                self.origin = pos
            if now < self.armed_at:
                return False
            dx = pos.x() - self.origin.x()
            dy = pos.y() - self.origin.y()
            if dx * dx + dy * dy >= 64.0:
                QApplication.quit()
                return True
            return False
        if now < self.armed_at:
            return False
        QApplication.quit()
        return True


class SettingsPanel(QFrame):
    applied = Signal()

    def __init__(self, sim: PipesSim, parent=None):
        super().__init__(parent)
        self.sim = sim
        self.setObjectName("settings")
        self.setFixedWidth(320)
        self._loading = False
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(220)
        self._debounce.timeout.connect(self._commit)

        title = QLabel("3D Pipes")
        title.setObjectName("settingsTitle")

        self.pipe_count = QSpinBox()
        self.pipe_count.setRange(1, 8)

        self.thickness = QSlider(Qt.Orientation.Horizontal)
        self.thickness.setRange(16, 48)
        self.thickness_lbl = QLabel()

        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(20, 200)
        self.speed_lbl = QLabel()

        self.reset_seconds = QSpinBox()
        self.reset_seconds.setRange(0, 300)
        self.reset_seconds.setSuffix(" s")
        self.reset_seconds.setSpecialValueText("When finished")

        self.reset_delay = QDoubleSpinBox()
        self.reset_delay.setRange(0.2, 5.0)
        self.reset_delay.setSingleStep(0.1)
        self.reset_delay.setDecimals(1)
        self.reset_delay.setSuffix(" s")

        self.joints = QComboBox()
        self.joints.addItem("Elbow", "elbow")
        self.joints.addItem("Ball", "ball")
        self.joints.addItem("Mixed", "mixed")
        self.joints.addItem("Cycle", "cycle")

        self.spin = QCheckBox("Camera spin")
        self.msaa = QCheckBox("Smooth edges (next launch)")

        restart = QPushButton("Restart now")
        restart.clicked.connect(self.sim.restart)

        form = QFormLayout()
        form.setSpacing(8)
        form.addRow("Number of pipes", self.pipe_count)
        thick_row = QHBoxLayout()
        thick_row.addWidget(self.thickness, 1)
        thick_row.addWidget(self.thickness_lbl)
        form.addRow("Thickness", thick_row)
        speed_row = QHBoxLayout()
        speed_row.addWidget(self.speed, 1)
        speed_row.addWidget(self.speed_lbl)
        form.addRow("Speed", speed_row)
        form.addRow("Reset interval", self.reset_seconds)
        form.addRow("Pause before reset", self.reset_delay)
        form.addRow("Joints", self.joints)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(self.spin)
        layout.addWidget(self.msaa)
        layout.addWidget(restart)
        hint = QLabel("S hides this panel · Space restarts · Esc quits")
        hint.setObjectName("settingsHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch(1)

        self.setStyleSheet(
            """
            QFrame#settings { background: #1c1c1c; color: #e6e6e6; border-left: 1px solid #3a3a3a; }
            QLabel { color: #e6e6e6; }
            QLabel#settingsTitle { font-size: 16px; font-weight: 600; padding-bottom: 6px; }
            QLabel#settingsHint { color: #9a9a9a; font-size: 11px; }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background: #111; color: #eee; border: 1px solid #444; padding: 3px 6px;
            }
            QPushButton {
                background: #2a2a2a; color: #eee; border: 1px solid #555; padding: 6px 10px;
            }
            QPushButton:hover { background: #353535; }
            QSlider::groove:horizontal { height: 4px; background: #444; }
            QSlider::handle:horizontal { width: 12px; margin: -5px 0; background: #ddd; }
            QCheckBox { color: #e6e6e6; spacing: 8px; }
            """
        )

        for w in (
            self.pipe_count,
            self.thickness,
            self.speed,
            self.reset_seconds,
            self.reset_delay,
            self.joints,
        ):
            w.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for w in (
            self.pipe_count,
            self.reset_seconds,
            self.reset_delay,
            self.joints,
            self.spin,
            self.msaa,
        ):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._changed)
            if hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(self._changed)
            if hasattr(w, "toggled"):
                w.toggled.connect(self._changed)
        self.thickness.valueChanged.connect(self._thickness_moved)
        self.speed.valueChanged.connect(self._speed_moved)

        self.load_from_sim()

    def load_from_sim(self) -> None:
        self._loading = True
        cfg = self.sim.cfg
        self.pipe_count.setValue(cfg["pipe_count"])
        self.thickness.setValue(int(round(cfg["thickness"] * 100)))
        self.speed.setValue(int(round(cfg["speed"] * 10)))
        self.reset_seconds.setValue(int(round(cfg["reset_seconds"])))
        self.reset_delay.setValue(cfg["reset_delay"])
        idx = self.joints.findData(cfg["joints"])
        self.joints.setCurrentIndex(max(0, idx))
        self.spin.setChecked(cfg["spin"])
        self.msaa.setChecked(cfg["multisample"])
        self._refresh_labels()
        self._loading = False

    def _refresh_labels(self) -> None:
        self.thickness_lbl.setText(f"{self.thickness.value() / 100:.2f}")
        self.speed_lbl.setText(f"{self.speed.value() / 10:.1f}")

    def _thickness_moved(self, _v: int) -> None:
        self._refresh_labels()
        self._changed()

    def _speed_moved(self, _v: int) -> None:
        self._refresh_labels()
        self._changed()

    def _changed(self, *_args) -> None:
        if self._loading:
            return
        self._debounce.start()

    def _commit(self) -> None:
        cfg = {
            "pipe_count": self.pipe_count.value(),
            "thickness": self.thickness.value() / 100.0,
            "speed": self.speed.value() / 10.0,
            "reset_seconds": float(self.reset_seconds.value()),
            "reset_delay": float(self.reset_delay.value()),
            "joints": self.joints.currentData() or "mixed",
            "spin": self.spin.isChecked(),
            "multisample": self.msaa.isChecked(),
        }
        restart = (
            cfg["pipe_count"] != self.sim.cfg["pipe_count"]
            or abs(cfg["thickness"] - self.sim.cfg["thickness"]) > 1e-6
            or cfg["joints"] != self.sim.cfg["joints"]
        )
        self.sim.apply_config(cfg, restart=restart)
        self.applied.emit()


class PreviewWindow(QWidget):
    def __init__(self, sim: PipesSim, show_settings: bool = True):
        super().__init__()
        self.sim = sim
        self.setWindowTitle("3D Pipes")
        self.resize(1480, 860)
        self.view = PipesWidget(sim, windowed=True)
        self.panel = SettingsPanel(sim)
        self.hint = QLabel("S settings  ·  Space restart  ·  Esc quit")
        self.hint.setObjectName("hint")
        self.hint.setParent(self)
        self.hint.adjustSize()
        self.hint_hide = QTimer(self)
        self.hint_hide.setSingleShot(True)
        self.hint_hide.setInterval(5000)
        self.hint_hide.timeout.connect(lambda: self.hint.hide())
        self.hint_hide.start()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view, 1)
        layout.addWidget(self.panel)
        self.panel.setVisible(show_settings)
        self.setStyleSheet("#hint { background: rgba(0,0,0,180); color: #ccc; padding: 6px 12px; }")

    def settings_visible(self) -> bool:
        return self.panel.isVisible()

    def set_settings_visible(self, visible: bool) -> None:
        self.panel.setVisible(visible)
        self._place_hint()

    def toggle_settings(self) -> None:
        self.set_settings_visible(not self.panel.isVisible())

    def _place_hint(self) -> None:
        self.hint.adjustSize()
        x = (self.view.width() - self.hint.width()) // 2
        y = self.height() - self.hint.height() - 18
        self.hint.move(max(8, x), max(8, y))
        self.hint.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_hint()


class CoverWindow(QWidget):
    def __init__(self, sim: PipesSim, screen):
        super().__init__()
        self.screen_ref = screen
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )
        self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.view = PipesWidget(sim, windowed=False)
        layout.addWidget(self.view)

    def place(self) -> None:
        self.show()
        handle = self.windowHandle()
        if handle is not None:
            handle.setScreen(self.screen_ref)
        self.setGeometry(self.screen_ref.geometry())
        self.showFullScreen()
        self.view.setFocus()


def make_surface_format(multisample: bool) -> QSurfaceFormat:
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setSamples(4 if multisample else 0)
    fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    fmt.setSwapInterval(1)
    return fmt


def configure_surface(multisample: bool) -> None:
    QSurfaceFormat.setDefaultFormat(make_surface_format(multisample))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="3D Pipes screensaver")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--window", action="store_true", help="windowed preview")
    mode.add_argument("--settings", action="store_true", help="windowed preview with settings open")
    mode.add_argument("--fullscreen", action="store_true", help="cover every monitor (default)")
    return p.parse_args(argv)


def enable_crash_log() -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        log = open(STATE_DIR / "faulthandler.log", "a", buffering=1)
        faulthandler.enable(file=log, all_threads=True)
    except OSError:
        faulthandler.enable()


def main(argv: list[str] | None = None) -> int:
    enable_crash_log()
    args = parse_args(argv)
    windowed = bool(args.window or args.settings)
    cfg = load_config()

    os.environ.setdefault("QT_OPENGL", "desktop")
    configure_surface(cfg["multisample"])
    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("3D Pipes")
    app.setApplicationDisplayName("3D Pipes")
    try:
        app.setWindowIcon(QIcon(str(ROOT / "share" / "icon.svg")))
    except Exception:
        pass

    sim = PipesSim(cfg, parent=app)

    if windowed:
        win = PreviewWindow(sim, show_settings=True)
        win.show()
        win.raise_()
        win.activateWindow()
        win.view.setFocus()
        return app.exec()

    app.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
    guard = ScreensaverGuard(parent=app)
    app.installEventFilter(guard)
    covers: list[CoverWindow] = []
    screens = QGuiApplication.screens() or [app.primaryScreen()]
    for screen in screens:
        if screen is None:
            continue
        cover = CoverWindow(sim, screen)
        covers.append(cover)
        cover.place()
    if not covers:
        QMessageBox.critical(None, "3D Pipes", "No screens available.")
        return 1
    covers[0].view.setFocus()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
