import pygame
import random
import heapq
from collections import deque
from enum import Enum
import math

class Colors:
    BACKGROUND = (18, 18, 18)
    WALL = (45, 45, 45)
    PATH = (240, 240, 240)
    START = (0, 255, 127)
    END = (255, 69, 0)
    VISITED = (30, 144, 255)
    ROUTE = (147, 112, 219)
    UI_BG = (30, 30, 30)
    UI_HOVER = (60, 60, 60)
    TEXT = (255, 255, 255)
    CHECKED = (46, 204, 113)

class State(Enum):
    WALL = 0
    PATH = 1
    VISITED = 2
    ROUTE = 3
    START = 4
    END = 5

def get_neighbors(grid, r, c, rows, cols):
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != State.WALL:
            neighbors.append((nr, nc))
    return neighbors

def reconstruct_path(grid, came_from, current, start):
    while current in came_from:
        current = came_from[current]
        if current != start:
            grid[current[0]][current[1]] = State.ROUTE
            yield

def algo_bfs(grid, start, end, rows, cols):
    queue = deque([start])
    came_from = {}
    visited = {start}
    while queue:
        current = queue.popleft()
        if current == end:
            yield from reconstruct_path(grid, came_from, end, start)
            return
        for nxt in get_neighbors(grid, current[0], current[1], rows, cols):
            if nxt not in visited:
                visited.add(nxt)
                came_from[nxt] = current
                queue.append(nxt)
                if nxt != end:
                    grid[nxt[0]][nxt[1]] = State.VISITED
        yield

def algo_dfs(grid, start, end, rows, cols):
    stack = [start]
    came_from = {}
    visited = {start}
    while stack:
        current = stack.pop()
        if current == end:
            yield from reconstruct_path(grid, came_from, end, start)
            return
        for nxt in get_neighbors(grid, current[0], current[1], rows, cols):
            if nxt not in visited:
                visited.add(nxt)
                came_from[nxt] = current
                stack.append(nxt)
                if nxt != end:
                    grid[nxt[0]][nxt[1]] = State.VISITED
        yield

def algo_dijkstra(grid, start, end, rows, cols):
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    visited = set()
    while open_set:
        _, current = heapq.heappop(open_set)
        if current in visited: continue
        visited.add(current)
        
        if current == end:
            yield from reconstruct_path(grid, came_from, end, start)
            return
            
        for nxt in get_neighbors(grid, current[0], current[1], rows, cols):
            temp_g = g_score[current] + 1
            if temp_g < g_score.get(nxt, float('inf')):
                came_from[nxt] = current
                g_score[nxt] = temp_g
                heapq.heappush(open_set, (temp_g, nxt))
                if nxt != end: grid[nxt[0]][nxt[1]] = State.VISITED
        yield

def algo_greedy(grid, start, end, rows, cols):
    h = lambda p1, p2: abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
    open_set = [(h(start, end), start)]
    came_from = {}
    visited = set()
    while open_set:
        _, current = heapq.heappop(open_set)
        if current in visited: continue
        visited.add(current)
        if current == end:
            yield from reconstruct_path(grid, came_from, end, start)
            return
        for nxt in get_neighbors(grid, current[0], current[1], rows, cols):
            if nxt not in visited:
                came_from[nxt] = current
                heapq.heappush(open_set, (h(nxt, end), nxt))
                if nxt != end: grid[nxt[0]][nxt[1]] = State.VISITED
        yield

def algo_astar(grid, start, end, rows, cols):
    count = 0
    h = lambda p1, p2: abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
    open_set = [(0, count, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: h(start, end)}
    open_set_hash = {start}
    
    while open_set:
        current = heapq.heappop(open_set)[2]
        open_set_hash.remove(current)
        
        if current == end:
            yield from reconstruct_path(grid, came_from, end, start)
            return
            
        for nxt in get_neighbors(grid, current[0], current[1], rows, cols):
            temp_g = g_score[current] + 1
            if temp_g < g_score.get(nxt, float('inf')):
                came_from[nxt] = current
                g_score[nxt] = temp_g
                f_score[nxt] = temp_g + h(nxt, end)
                if nxt not in open_set_hash:
                    count += 1
                    heapq.heappush(open_set, (f_score[nxt], count, nxt))
                    open_set_hash.add(nxt)
                    if nxt != end: grid[nxt[0]][nxt[1]] = State.VISITED
        yield

ALGORITHMS = {
    "A* (A-Star)": algo_astar,
    "BFS": algo_bfs,
    "DFS": algo_dfs,
    "Dijkstra": algo_dijkstra,
    "Greedy": algo_greedy
}

class Button:
    def __init__(self, x, y, w, h, text, font, toggleable=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.toggleable = toggleable
        self.checked = False
        self.is_hovered = False

    def draw(self, screen):
        color = Colors.CHECKED if self.checked else (Colors.UI_HOVER if self.is_hovered else Colors.UI_BG)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, Colors.TEXT, self.rect, 2, border_radius=5)
        text_surf = self.font.render(self.text, True, Colors.TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def click(self):
        if self.toggleable:
            self.checked = not self.checked
        return True

class GridInstance:
    def __init__(self, base_grid, rect, algo_name, algo_func, start, end, rows, cols):
        self.grid = [row[:] for row in base_grid]
        self.rect = pygame.Rect(rect)
        self.algo_name = algo_name
        self.rows = rows
        self.cols = cols
        self.cell_size = min(self.rect.width // cols, self.rect.height // rows)
        
        self.offset_x = self.rect.x + (self.rect.width - (cols * self.cell_size)) // 2
        self.offset_y = self.rect.y + (self.rect.height - (rows * self.cell_size)) // 2
        
        self.generator = algo_func(self.grid, start, end, rows, cols)
        self.done = False
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        
        self.visited_count = 0
        self.path_length = 0

    def calculate_metrics(self):
        self.visited_count = 0
        self.path_length = 0
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == State.VISITED:
                    self.visited_count += 1
                elif self.grid[r][c] == State.ROUTE:
                    self.path_length += 1
                    self.visited_count += 1
        
        self.path_length += 2
        self.visited_count += 2

    def step(self):
        if not self.done:
            try:
                next(self.generator)
            except StopIteration:
                self.done = True
                self.calculate_metrics()

    def draw(self, screen):
        color_map = {
            State.WALL: Colors.WALL, State.PATH: Colors.PATH,
            State.VISITED: Colors.VISITED, State.ROUTE: Colors.ROUTE,
            State.START: Colors.START, State.END: Colors.END
        }
        pygame.draw.rect(screen, Colors.UI_BG, self.rect)
        pygame.draw.rect(screen, Colors.TEXT, self.rect, 2)
        
        for r in range(self.rows):
            for c in range(self.cols):
                color = color_map.get(self.grid[r][c], Colors.WALL)
                pygame.draw.rect(screen, color, 
                                 (self.offset_x + c * self.cell_size, 
                                  self.offset_y + r * self.cell_size, 
                                  self.cell_size - 1, self.cell_size - 1))
                
        label_text = self.algo_name + (" (Bitti)" if self.done else "")
        label = self.font.render(label_text, True, Colors.TEXT)
        screen.blit(label, (self.rect.x + 10, self.rect.y + 10))


class Engine:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Maze Generator & Pathfinding Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20)
        
        self.rows, self.cols = 41, 41
        self.start_pos = (1, 1)
        self.end_pos = (self.rows - 2, self.cols - 2)
        self.base_grid = []
        self.generate_maze()
        
        self.state = "MAIN"
        self.instances = []
        self.setup_ui()

    def generate_maze(self):
        self.base_grid = [[State.WALL for _ in range(self.cols)] for _ in range(self.rows)]
        stack = [(1, 1)]
        self.base_grid[1][1] = State.PATH
        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        
        while stack:
            r, c = stack[-1]
            neighbors = []
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 1 <= nr < self.rows - 1 and 1 <= nc < self.cols - 1 and self.base_grid[nr][nc] == State.WALL:
                    neighbors.append((nr, nc, dr, dc))
            if neighbors:
                nr, nc, dr, dc = random.choice(neighbors)
                self.base_grid[r + dr//2][c + dc//2] = State.PATH
                self.base_grid[nr][nc] = State.PATH
                stack.append((nr, nc))
            else:
                stack.pop()
                
        walls_to_break = (self.rows * self.cols) // 15
        for _ in range(walls_to_break):
            r = random.randint(1, self.rows - 2)
            c = random.randint(1, self.cols - 2)
            self.base_grid[r][c] = State.PATH
                
        self.base_grid[self.start_pos[0]][self.start_pos[1]] = State.START
        self.base_grid[self.end_pos[0]][self.end_pos[1]] = State.END

    def setup_ui(self):
        self.btn_compare = Button(self.WIDTH//2 - 100, self.HEIGHT//2, 200, 50, "Karşılaştır", self.font)
        self.btn_new = Button(self.WIDTH//2 - 100, self.HEIGHT//2 + 70, 200, 50, "Yeni Labirent", self.font)
        
        self.algo_buttons = []
        y_offset = 200
        for name in ALGORITHMS.keys():
            self.algo_buttons.append(Button(self.WIDTH//2 - 150, y_offset, 300, 40, name, self.font, toggleable=True))
            y_offset += 60
        self.btn_start = Button(self.WIDTH//2 - 150, y_offset + 20, 300, 50, "Tamam (Başla)", self.font)
        self.btn_back = Button(20, 20, 100, 40, "Geri", self.font)

    def start_comparison(self):
        selected = [b.text for b in self.algo_buttons if b.checked]
        if not selected: return
        
        self.instances = []
        n = len(selected)
        
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / cols))
        w = self.WIDTH // cols
        h = self.HEIGHT // rows
        
        for idx, algo_name in enumerate(selected):
            r = idx // cols
            c = idx % cols
            rect = (c * w, r * h, w, h)
            self.instances.append(GridInstance(
                self.base_grid, rect, algo_name, ALGORITHMS[algo_name],
                self.start_pos, self.end_pos, self.rows, self.cols
            ))
        self.state = "RUNNING"

    def draw_leaderboard(self, mouse_pos):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(Colors.BACKGROUND)
        self.screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 750, 450
        panel_rect = pygame.Rect(self.WIDTH//2 - panel_w//2, self.HEIGHT//2 - panel_h//2, panel_w, panel_h)
        pygame.draw.rect(self.screen, Colors.UI_BG, panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, Colors.TEXT, panel_rect, 2, border_radius=15)
        
        title = self.font.render("Simülasyon Sonuçları", True, Colors.START)
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, panel_rect.y + 30))
        
        sorted_inst = sorted(self.instances, key=lambda x: (x.path_length, x.visited_count))
        
        cols_x = [panel_rect.x + 40, panel_rect.x + 280, panel_rect.x + 550]
        y_offset = panel_rect.y + 100
        headers = ["Algoritma", "Yol Uzunluğu (Optimalite)", "Taranan Alan (Verimlilik)"]
        for i, h in enumerate(headers):
            self.screen.blit(self.font.render(h, True, Colors.TEXT), (cols_x[i], y_offset))
        pygame.draw.line(self.screen, Colors.TEXT, (panel_rect.x + 40, y_offset + 30), (panel_rect.x + panel_w - 40, y_offset + 30))
        
        y_offset += 50
        for rank, inst in enumerate(sorted_inst):
            color = Colors.START if rank == 0 else Colors.TEXT
            r1 = self.font.render(f"{rank + 1}. {inst.algo_name}", True, color)
            r2 = self.font.render(f"{inst.path_length} adım", True, color)
            r3 = self.font.render(f"{inst.visited_count} hücre", True, color)
            
            self.screen.blit(r1, (cols_x[0], y_offset))
            self.screen.blit(r2, (cols_x[1], y_offset))
            self.screen.blit(r3, (cols_x[2], y_offset))
            y_offset += 45
            
        self.btn_back.rect.topleft = (panel_rect.x + panel_w//2 - 50, panel_rect.y + panel_h - 70)
        self.btn_back.check_hover(mouse_pos)
        self.btn_back.draw(self.screen)

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "MAIN":
                        if self.btn_compare.is_hovered: self.state = "MENU"
                        elif self.btn_new.is_hovered: self.generate_maze()
                    elif self.state == "MENU":
                        if self.btn_back.is_hovered: self.state = "MAIN"
                        elif self.btn_start.is_hovered: self.start_comparison()
                        for b in self.algo_buttons:
                            if b.is_hovered: b.click()
                    elif self.state in ["RUNNING", "RESULTS"]:
                        if self.btn_back.is_hovered: self.state = "MENU"
            
            self.screen.fill(Colors.BACKGROUND)
            
            if self.state == "MAIN":
                dummy = GridInstance(self.base_grid, (0,0,self.WIDTH,self.HEIGHT), "", lambda *args: iter([]), self.start_pos, self.end_pos, self.rows, self.cols)
                dummy.draw(self.screen)
                s = pygame.Surface((self.WIDTH, self.HEIGHT)); s.set_alpha(150); s.fill((0,0,0)); self.screen.blit(s, (0,0))
                
                for btn in [self.btn_compare, self.btn_new]:
                    btn.check_hover(mouse_pos)
                    btn.draw(self.screen)
                    
            elif self.state == "MENU":
                title = self.font.render("Karşılaştırılacak Algoritmaları Seçin", True, Colors.TEXT)
                self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 120))
                for btn in self.algo_buttons + [self.btn_start, self.btn_back]:
                    btn.check_hover(mouse_pos)
                    btn.draw(self.screen)
                    
            elif self.state in ["RUNNING", "RESULTS"]:
                all_done = True
                for inst in self.instances:
                    if self.state == "RUNNING":
                        inst.step()
                        if not inst.done: all_done = False
                    inst.draw(self.screen)
                
                if self.state == "RUNNING" and all_done:
                    self.state = "RESULTS"
                
                if self.state == "RESULTS":
                    self.draw_leaderboard(mouse_pos)
                else:
                    self.btn_back.rect.topleft = (20, 20)
                    self.btn_back.check_hover(mouse_pos)
                    self.btn_back.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(120 if self.state == "RUNNING" else 60)

        pygame.quit()

if __name__ == "__main__":
    Engine().run()
