# ===== РЕНДЕР: настоящий 3D (проекция + z-буфер), рисуется «пикселями» =====
# Один символ = 2 пикселя по вертикали (символ ▀ с цветом текста и фона),
# поэтому картинка в 2 раза чётче, да ещё и полноцветная (24-bit).
# Карта -> 3D-меши (кубы) -> проекция камерой (yaw + pitch) -> обрезка по ближней
# плоскости -> закраска построчно с z-буфером и туманом.
import math

NEAR = 0.1
MAX_DIST = 20.0
FOV = math.radians(75)
K = 48                                   # уровней тумана в палитре
FOG = (40, 55, 90)
SKY_TOP = (8, 12, 36)

WALL_RGB = (200, 95, 65)
BLOCK_RGB = {1: (90, 200, 110), 2: (80, 180, 225), 3: (235, 205, 85), 4: (200, 115, 235),
             5: (245, 155, 60), 6: (245, 115, 165), 7: (165, 225, 95), 8: (125, 145, 245),
             9: (235, 235, 235)}
FLOOR_RGB = ((118, 128, 150), (86, 95, 118))

_L = (0.35, 0.55, 0.75)
_ln = math.sqrt(sum(c * c for c in _L))
LIGHT = tuple(c / _ln for c in _L)

# --- таблица цветов: пиксель хранит номер цвета, а в текст он превращается готовым кодом ---
_ids = {}
_FG = []
_BG = []


def color_id(c):
    r, g, b = (max(0, min(255, int(v))) for v in c)
    key = (r, g, b)
    i = _ids.get(key)
    if i is None:
        i = len(_FG)
        _ids[key] = i
        _FG.append(f"\x1b[38;2;{r};{g};{b}m")
        _BG.append(f"\x1b[48;2;{r};{g};{b}m")
    return i


WHITE = color_id((255, 255, 255))


def kind_rgb(ch):
    if ch == "#":
        return WALL_RGB
    if ch.isdigit() and ch != "0":
        return BLOCK_RGB[int(ch)]
    return None


def kind_color(ch):
    rgb = kind_rgb(ch)
    return color_id(rgb) if rgb else color_id((30, 32, 40))


_pal_cache = {}


def _pal(rgb):
    """Палитра (индекс = уровень близости, K = рядом, 0 = растворилось в тумане)."""
    key = tuple(int(v) for v in rgb)
    p = _pal_cache.get(key)
    if p is None:
        p = []
        for i in range(K + 1):
            t = (i / K) ** 0.7
            p.append(color_id([FOG[j] + (key[j] - FOG[j]) * t for j in range(3)]))
        _pal_cache[key] = p
    return p


def _shade(nx, ny, nz):
    return 0.45 + 0.55 * max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])


def build_mesh(gm):
    """Грани: (вершины, нормаль, центр, радиус, палитра)."""
    faces = []
    for y in range(gm.h):
        for x in range(gm.w):
            h = gm.heights[y][x]
            chk = (x + y) % 2
            if h == 0:
                v = [(x, y, 0), (x + 1, y, 0), (x + 1, y + 1, 0), (x, y + 1, 0)]
                faces.append((v, 0, 0, 1, x + .5, y + .5, 0, 0.8, _pal(FLOOR_RGB[chk])))
                continue
            base = kind_rgb(gm.kind[y][x]) or WALL_RGB
            k = _shade(0, 0, 1) * (0.93 if chk else 1.0)
            v = [(x, y, h), (x + 1, y, h), (x + 1, y + 1, h), (x, y + 1, h)]
            faces.append((v, 0, 0, 1, x + .5, y + .5, h, 0.8, _pal([c * k for c in base])))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nh = gm.height(x + dx, y + dy)
                for z in range(nh, h):          # стена из «кирпичей» высотой 1
                    z1 = z + 1
                    if dx == 1:
                        v = [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z1), (x + 1, y, z1)]
                    elif dx == -1:
                        v = [(x, y, z), (x, y + 1, z), (x, y + 1, z1), (x, y, z1)]
                    elif dy == 1:
                        v = [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z1), (x, y + 1, z1)]
                    else:
                        v = [(x, y, z), (x + 1, y, z), (x + 1, y, z1), (x, y, z1)]
                    k = _shade(dx, dy, 0) * (0.86 if (x + y + z) % 2 else 1.0)
                    faces.append((v, dx, dy, 0, x + .5 + dx * .5, y + .5 + dy * .5, z + .5, 0.85,
                                  _pal([c * k for c in base])))
    return faces


def _clip_near(poly):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[2] >= NEAR, b[2] >= NEAR
        if ina:
            out.append(a)
        if ina != inb:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), NEAR))
    return out


class Renderer:
    def __init__(self, gm, PW, PH):
        self.PW, self.PH = PW, PH
        self.faces = build_mesh(gm)
        self.fx = (PW / 2) / math.tan(FOV / 2)
        self.fy = self.fx                      # пиксели квадратные (▀ = пол-символа)

    def render(self, pl):
        """Возвращает список из PW*PH номеров цветов (см. color_id)."""
        W, H = self.PW, self.PH
        ex, ey, ez = pl.x, pl.y, pl.eye_z
        cy, sy = math.cos(pl.yaw), math.sin(pl.yaw)
        cp, sp = math.cos(pl.pitch), math.sin(pl.pitch)
        f0, f1, f2 = cp * cy, cp * sy, sp          # вперёд
        r0, r1 = -sy, cy                            # вправо
        u0, u1, u2 = -sp * cy, -sp * sy, cp         # вверх
        fx, fy, hx, hy = self.fx, self.fy, W / 2, H / 2

        # небо: градиент до линии горизонта, ниже - цвет тумана
        horizon = hy + (sp / cp) * fy
        fog_idx = color_id(FOG)
        pix = []
        for y in range(H):
            if y >= horizon:
                c = fog_idx
            else:
                s = max(0.0, min(1.0, (y + 0.5) / max(horizon, 1e-6)))
                c = color_id([SKY_TOP[j] + (FOG[j] - SKY_TOP[j]) * s for j in range(3)])
            pix.extend([c] * W)
        zbuf = [0.0] * (W * H)

        for verts, nx, ny, nz, px, py, pz, rad, pal in self.faces:
            dx, dy, dz = px - ex, py - ey, pz - ez
            if dx * nx + dy * ny + dz * nz >= 0:    # грань смотрит от нас
                continue
            zc = dx * f0 + dy * f1 + dz * f2
            if zc + rad < NEAR or zc - rad > MAX_DIST:
                continue
            poly = []
            for vx, vy, vz in verts:
                ax, ay, az = vx - ex, vy - ey, vz - ez
                poly.append((ax * r0 + ay * r1,
                             ax * u0 + ay * u1 + az * u2,
                             ax * f0 + ay * f1 + az * f2))
            poly = _clip_near(poly)
            if len(poly) < 3:
                continue
            pts = [(hx + x * fx / z, hy - y * fy / z, 1.0 / z) for x, y, z in poly]
            for i in range(1, len(pts) - 1):
                self._fill(pts[0], pts[i], pts[i + 1], pal, zbuf, pix)

        cx, cyy = W // 2, H // 2                    # прицел
        for d in (-2, -1, 1, 2):
            pix[cyy * W + cx + d] = WHITE
            pix[(cyy + d) * W + cx] = WHITE
        return pix

    def _fill(self, p0, p1, p2, pal, zbuf, pix):
        W, H = self.PW, self.PH
        x0, y0, w0 = p0
        x1, y1, w1 = p1
        x2, y2, w2 = p2
        det = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(det) < 1e-9:
            return
        a = ((w1 - w0) * (y2 - y0) - (w2 - w0) * (y1 - y0)) / det   # d(1/z)/dx
        b = ((x1 - x0) * (w2 - w0) - (x2 - x0) * (w1 - w0)) / det   # d(1/z)/dy
        ymin = max(0, math.ceil(min(y0, y1, y2) - 0.5))
        ymax = min(H - 1, math.ceil(max(y0, y1, y2) - 0.5) - 1)
        wmin = 1.0 / MAX_DIST
        inv = 1.0 / MAX_DIST
        edges = ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0))
        for y in range(ymin, ymax + 1):
            yc = y + 0.5
            xs = []
            for ax, ay, bx, by in edges:
                if (ay <= yc < by) or (by <= yc < ay):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            if len(xs) < 2:
                continue
            xa = max(0, math.ceil(min(xs) - 0.5))
            xb = min(W - 1, math.ceil(max(xs) - 0.5) - 1)
            if xa > xb:
                continue
            row = y * W
            w = w0 + a * (xa + 0.5 - x0) + b * (yc - y0)
            for x in range(xa, xb + 1):
                if w > wmin and w > zbuf[row + x]:
                    zbuf[row + x] = w
                    lv = int((1.0 - inv / w) * K)
                    pix[row + x] = pal[K if lv > K else (0 if lv < 0 else lv)]
                w += a


def to_text(pix, PW, PH):
    """Пиксели -> текст: каждая пара строк пикселей = одна строка символов ▀."""
    lines = []
    for r in range(0, PH, 2):
        top = pix[r * PW:(r + 1) * PW]
        bot = pix[(r + 1) * PW:(r + 2) * PW]
        parts = []
        pf = pb = -1
        for t, b in zip(top, bot):
            if t == b:
                if pb != b:
                    parts.append(_BG[b])
                    pb = b
                parts.append(" ")
            else:
                if pf != t:
                    parts.append(_FG[t])
                    pf = t
                if pb != b:
                    parts.append(_BG[b])
                    pb = b
                parts.append("▀")
        parts.append("\x1b[0m")
        lines.append("".join(parts))
    return "\n".join(lines)
