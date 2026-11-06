# ===== КАРТА (рисуется символами) =====
#   #      - высокая стена (высота 3)
#   1..9   - блок такой высоты (можно запрыгивать на низкие!)
#   .      - пол
#   P      - точка старта игрока
# Все строки должны быть одной длины.

LEVEL = [
    "##############################",
    "#............................#",
    "#..1.2.3.4............#####..#",
    "#..................#.....#...#",
    "#..........####....#.....#...#",
    "#..........#..#....#####.#...#",
    "#..........#..#..............#",
    "#..........####..............#",
    "#............................#",
    "#..22....................55..#",
    "#..22..........P.........55..#",
    "#............................#",
    "#...##########..########.....#",
    "#............................#",
    "##############################",
]


class GameMap:
    def __init__(self, rows=LEVEL):
        self.rows = rows
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.spawn = (1.5, 1.5)
        self.heights = []
        self.kind = []
        for y, row in enumerate(rows):
            line = []
            kline = []
            for x in range(self.w):
                ch = row[x] if x < len(row) else "#"
                kline.append(ch)
                if ch == "P":
                    self.spawn = (x + 0.5, y + 0.5)
                if ch == "#":
                    line.append(3)
                elif ch.isdigit():
                    line.append(int(ch))
                else:
                    line.append(0)
            self.heights.append(line)
            self.kind.append(kline)

    def height(self, fx, fy):
        """Высота блока в точке (за границей карты - очень высокая стена)."""
        ix, iy = int(fx // 1), int(fy // 1)
        if ix < 0 or iy < 0 or ix >= self.w or iy >= self.h:
            return 99
        return self.heights[iy][ix]
