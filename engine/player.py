# ===== ИГРОК: позиция в 3D, поворот, прыжок, гравитация, столкновения =====
import math

EYE = 1.2        # высота глаз над ногами
RADIUS = 0.25    # радиус игрока
SPEED = 4.0      # клеток/сек
TURN = 2.4       # рад/сек
LOOK = 1.6       # рад/сек (вверх/вниз)
GRAVITY = 16.0
JUMP = 7.0       # начальная скорость прыжка (хватает на блок высотой 1)
STEP = 0.3       # на какую высоту можно просто «шагнуть»


class Player:
    def __init__(self, x, y, yaw=0.0):
        self.x, self.y, self.z = x, y, 0.0   # z - уровень ног
        self.yaw = yaw
        self.pitch = 0.0
        self.vz = 0.0
        self.on_ground = True

    @property
    def eye_z(self):
        return self.z + EYE

    def _corners(self, x, y):
        for sx in (-RADIUS, RADIUS):
            for sy in (-RADIUS, RADIUS):
                yield x + sx, y + sy

    def _blocked(self, gm, x, y):
        return any(gm.height(cx, cy) > self.z + STEP for cx, cy in self._corners(x, y))

    def _ground(self, gm):
        return max(gm.height(cx, cy) for cx, cy in self._corners(self.x, self.y))

    def update(self, gm, forward, strafe, turn, look, jump, dt):
        self.yaw += turn * TURN * dt
        self.pitch = max(-1.1, min(1.1, self.pitch + look * LOOK * dt))

        if forward or strafe:
            n = math.hypot(forward, strafe)
            f, s = forward / n, strafe / n
            c, sn = math.cos(self.yaw), math.sin(self.yaw)
            dx = (c * f - sn * s) * SPEED * dt
            dy = (sn * f + c * s) * SPEED * dt
            if not self._blocked(gm, self.x + dx, self.y):
                self.x += dx
            if not self._blocked(gm, self.x, self.y + dy):
                self.y += dy

        if jump and self.on_ground:
            self.vz = JUMP
            self.on_ground = False
        self.vz -= GRAVITY * dt
        self.z += self.vz * dt
        g = self._ground(gm)
        if self.z <= g:
            self.z, self.vz, self.on_ground = g, 0.0, True
        else:
            self.on_ground = False
