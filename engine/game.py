# ===== ГЛАВНЫЙ ЦИКЛ =====
import ctypes
import math
import msvcrt
import os
import sys
import time

from map import GameMap
from player import Player
from render import Renderer, FOV, WHITE, color_id, kind_color, to_text

BORDER = color_id((200, 200, 205))
CONE = color_id((140, 140, 150))
YELLOW = color_id((255, 225, 40))

PW, PH = 120, 64       # разрешение в «пикселях» (в консоли это 120 x 32 символа)

VK_W, VK_A, VK_S, VK_D = 0x57, 0x41, 0x53, 0x44
VK_Q, VK_E, VK_M = 0x51, 0x45, 0x4D
VK_LEFT, VK_UP, VK_RIGHT, VK_DOWN = 0x25, 0x26, 0x27, 0x28
VK_SPACE, VK_ESC = 0x20, 0x1B


def down(vk):
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)


def put(pix, x, y, c):
    if 0 <= x < PW and 0 <= y < PH:
        pix[y * PW + x] = c


def draw_minimap(pix, gm, pl, s, colors):
    """Миникарта прямо в пикселях: каждая клетка карты = s x s пикселей, цвет = тип блока."""
    X0 = Y0 = 2
    for my in range(-1, gm.h * s + 1):
        for mx in range(-1, gm.w * s + 1):
            if my < 0 or mx < 0 or my >= gm.h * s or mx >= gm.w * s:
                c = BORDER
            else:
                ch = gm.kind[my // s][mx // s]
                if ch not in colors:
                    colors[ch] = kind_color(ch)
                c = colors[ch]
            put(pix, X0 + mx, Y0 + my, c)
    px, py = X0 + pl.x * s, Y0 + pl.y * s
    for a in (pl.yaw - FOV / 2, pl.yaw + FOV / 2):          # конус обзора
        for t in range(1, 6 * s):
            put(pix, int(px + math.cos(a) * t), int(py + math.sin(a) * t), CONE)
    for t in range(1, 4 * s):                                # направление взгляда
        put(pix, int(px + math.cos(pl.yaw) * t), int(py + math.sin(pl.yaw) * t), WHITE)
    for ox in range(max(1, s)):                              # сам игрок
        for oy in range(max(1, s)):
            put(pix, int(px) + ox - s // 2, int(py) + oy - s // 2, YELLOW)


def main():
    os.system("")  # включает ANSI-коды в cmd
    out = sys.stdout
    out.write("\x1b[2J\x1b[?25l")
    gm = GameMap()
    pl = Player(*gm.spawn)
    rd = Renderer(gm, PW, PH)
    map_scale, m_prev = 2, False       # M: большая карта -> маленькая -> выкл
    colors = {}
    fps, last = 0.0, time.time()
    try:
        while True:
            t0 = time.time()
            dt = min(t0 - last, 0.1)
            last = t0
            while msvcrt.kbhit():       # чтобы нажатия не «печатались» в консоль
                msvcrt.getwch()
            if down(VK_ESC):
                return
            m_now = down(VK_M)
            if m_now and not m_prev:
                map_scale = {2: 1, 1: 0, 0: 2}[map_scale]
            m_prev = m_now

            pl.update(gm,
                      forward=down(VK_W) - down(VK_S),
                      strafe=down(VK_D) - down(VK_A),
                      turn=(down(VK_RIGHT) or down(VK_E)) - (down(VK_LEFT) or down(VK_Q)),
                      look=down(VK_UP) - down(VK_DOWN),
                      jump=down(VK_SPACE),
                      dt=dt)

            pix = rd.render(pl)
            if map_scale:
                draw_minimap(pix, gm, pl, map_scale, colors)
            fps = fps * 0.9 + (1 / max(dt, 1e-3)) * 0.1
            hud = (f"WASD ходьба | стрелки/Q/E камера | ПРОБЕЛ прыжок | M карта | ESC выход"
                   f"   x={pl.x:.1f} y={pl.y:.1f} z={pl.z:.1f}  {fps:.0f} fps")
            out.write("\x1b[H" + to_text(pix, PW, PH) + "\n" + hud.ljust(PW + 20)[:PW + 20])
            out.flush()
            time.sleep(max(0.0, 1 / 30 - (time.time() - t0)))
    finally:
        out.write("\x1b[?25h\x1b[0m\n")


if __name__ == "__main__":
    main()
