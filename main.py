import pygame
import random

# ------------------------
# Game Logic (no rendering)
# ------------------------

class GameBoard:
    def __init__(self, width, height, initial_mines):
        self.width = width
        self.height = height
        self.initial_mines = initial_mines
        self.grid = self._generate_initial_board()
        self.revealed = [[False]*width for _ in range(height)]
        self.flagged = [[False]*width for _ in range(height)]
        self.first_click = True
        self.game_over = False


    def _generate_initial_board(self):#initial_mines
        # Fill the board row by row
        board = [[0] * self.width for _ in range(self.height)]
        for i in range(self.initial_mines):
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                if board[y][x] != "M":
                    board[y][x] = "M"
                    break
        self.calculate_board(board)
        return board
    
    def calculate_board(self, board):
        for y in range(self.height):
            for x in range(self.width):
                if board[y][x] == "M":
                    continue
                count = 0
                for nx, ny in self.adjacent_mines(x, y):
                    if board[ny][nx] == "M":
                        count += 1
                board[y][x] = count
        return board



    def blast(self):
        for y, row in enumerate(self.flagged):
            print(y, row)
            if all(row):  # if whole row is flagged
                if all(cell == "M" for cell in row): # if whole row is mines
                    self.grid[y] = [0] * self.width
                    self.grid = self.calculate_board(self.grid)
                    self.revealed[y] = [True]*self.width
                    self.flagged[y] = [False]*self.width




    def enact_gravity(self):
        chunks = self.identify_chunks()
        moved = True
        while moved:
            moved = False
            for chunk in chunks:
                if self.fall_chunk(chunk):
                    moved = True
                if all(self.revealed[0]):
                    self.encroach()
        self.grid = self.calculate_board(self.grid)

    def fall_chunk(self, chunk):
        # Move all cells in chunk down by 1
        if self.can_fall(chunk):
            for x, y in sorted(chunk, key=lambda c: -c[1]):  # Sort by y descending
                if self.revealed[y][x]:
                    print("Error: trying to move revealed cell")
                if not self.revealed[y + 1][x]:
                    print("Error: trying to move into non-revealed cell")
                self.grid[y + 1][x] = self.grid[y][x]
                self.revealed[y + 1][x] = self.revealed[y][x]
                self.flagged[y + 1][x] = self.flagged[y][x]
                self.grid[y][x] = 0
                self.revealed[y][x] = True
                self.flagged[y][x] = False
                chunk.remove((x, y))
                chunk.add((x, y + 1))
            #if anything is in row 1 now, it was in row 0, so this chunk is connected to new rows
            if any(y == 1 for x, y in chunk): 
                self.encroach()
                for x in range(self.width):
                    chunk.add((x, 0))
            return True
        return False
            

    def encroach(self):
        # check if row 0 is entirely revealed:
        if not all(self.revealed[0]):
            print("CATASTROPHE")
            return
        new_row = [0] * self.width
        n_mines = self.initial_mines // self.height
        n_mines = random.randint(max(0, n_mines - 2), min(self.width, n_mines + 2))
        mine_positions = random.sample(range(self.width), n_mines)
        for x in mine_positions:
            new_row[x] = "M"
        self.grid[0] = new_row
        self.grid = self.calculate_board(self.grid)
        self.revealed[0] = [False]*self.width
        self.flagged[0] = [False]*self.width

    def can_fall(self, chunk):
        for x, y in chunk:
            if y + 1 >= self.height:
                return False
            # can fall if space below is unrevealed or within same chunk
            if not (self.revealed[y + 1][x] or (x, y + 1) in chunk):
                return False
        return True

    def identify_chunks(self):
        visited = [[False]*self.width for _ in range(self.height)]
        chunks = []
        for y in range(self.height):
            for x in range(self.width):
                if not self.revealed[y][x] and not visited[y][x]:
                    chunk = set()
                    stack = [(x, y)]
                    while stack:
                        cx, cy = stack.pop()
                        visited[cy][cx] = True
                        chunk.add((cx, cy))
                        for nx, ny in self.adjacent_mines(cx, cy, plus=True):
                            if not self.revealed[ny][nx] and not visited[ny][nx]:
                                stack.append((nx, ny))
                    chunks.append(chunk)
        # any chunks touching top row are connected to each other
        top_chunks = [c for c in chunks if any(y == 0 for x, y in c)]
        if top_chunks:
            combined = set()
            for c in top_chunks:
                combined.update(c)
                chunks.remove(c)
            chunks.append(combined)
        return chunks

    def reveal_tile(self, x, y):
        if self.first_click:
            while self.grid[y][x] != 0:
                self.grid = self._generate_initial_board()
        if self.revealed[y][x] or self.flagged[y][x]:
            return True  # No action if already revealed or flagged`
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            if self.revealed[y][x]:
                continue
            self.revealed[y][x] = True
            if self.grid[y][x] == 0:
                for nx, ny in self.adjacent_mines(x, y):
                    queue.append((nx, ny))
            elif self.grid[y][x] == "M":
                self.game_over = True
                return "M"
        # if self.gravity:
        #     self.enact_gravity()

        self.first_click = False

        return self.grid[y][x]
    
    def space_bar_tile(self, x, y):
        if not self.revealed[y][x]:
            self.flag_tile(x, y)
            return "Flagged:", x, y
        else:
            # if mines are mislabeled, chording can hit a mine
            if self.chord_tile(x, y) == "M":
                return "M"
            else:
                return "Chorded:", x, y

    def chord_tile(self, x, y):
        if self.revealed[y][x] and self.grid[y][x] > 0:
            flagged_count = sum(1 for nx, ny in self.adjacent_mines(x, y) if self.flagged[ny][nx])
            if flagged_count == self.grid[y][x]:
                for nx, ny in self.adjacent_mines(x, y):
                    if not self.revealed[ny][nx] and not self.flagged[ny][nx]:
                        result = self.reveal_tile(nx, ny)
                        if result == "M":
                            self.game_over = True
                            return "M"
        return True
                        

    def flag_tile(self, x, y):
        if not self.revealed[y][x]:
             self.flagged[y][x] = not self.flagged[y][x]


    def __str__(self):
        return "\n".join(str(row) for row in self.grid)

    def adjacent_mines(self, x, y, plus=False):
        rtn = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                if plus and (abs(dy) + abs(dx) != 1):
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    rtn.append((nx, ny))
        return rtn


# class Chunk:
#     def __init__(self, shape, x, y):
#         self.shape = shape  # 2D list, 1 = block, 0 = empty

    # def cells(self):
    #     """Yield absolute positions of occupied cells"""
    #     for dy, row in enumerate(self.shape):
    #         for dx, val in enumerate(row):
    #             if val:
    #                 yield (self.x + dx, self.y + dy)

# ------------------------
# Rendering Layer (Pygame)
# ------------------------

TILE_SIZE = 32
Y_RESTART = 50


colors = {
    'restart': (200, 200, 0), # yellow for restart button
    'M': (0, 0, 0),    # black for mines
    1: (0, 0, 255),    # blue
    2: (0, 128, 0),    # green
    3: (255, 0, 0),    # red
    4: (0, 0, 128),    # dark blue
    5: (128, 0, 0),    # dark red
    6: (0, 128, 128),  # cyan
    7: (0, 0, 0),      # black
    8: (128, 128, 128),# gray
    'hidden': (200, 200, 200),
    'revealed': (150, 150, 150),
    'border': (100, 100, 100)
}

class GameRenderer:
    def __init__(self, screen, board: GameBoard):
        self.screen = screen
        self.board = board
        self.font = pygame.font.SysFont(None, 24)
        self.show_outlines = False

    def draw(self):
        self.screen.fill((0, 0, 0))
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, colors['border'], rect, 1)
                if self.board.revealed[y][x]:
                    pygame.draw.rect(self.screen, colors["revealed"], rect.inflate(-2, -2))
                    if cell == 0:
                        continue
                    text = self.font.render(str(cell), True, colors[cell])
                    self.screen.blit(text, text.get_rect(center=rect.center))
                elif self.board.flagged[y][x]:
                    pygame.draw.rect(self.screen, (255, 0, 0), rect.inflate(-2, -2))  # Red for flagged
                else:
                    pygame.draw.rect(self.screen, colors['hidden'], rect.inflate(-2, -2))
        if self.show_outlines:
            self.outline_chunks()
        # Draw gravity button
        rect = pygame.Rect(0, self.board.height * TILE_SIZE + Y_RESTART, self.board.width * TILE_SIZE, Y_RESTART)
        pygame.draw.rect(self.screen, colors[2], rect.inflate(-2, -2))
        text = self.font.render("GRAVITY", True, (0, 0, 0))
        self.screen.blit(text, text.get_rect(center=rect.center))
        # Draw encroach button
        rect = pygame.Rect(0, self.board.height * TILE_SIZE + 2 * Y_RESTART, self.board.width * TILE_SIZE, Y_RESTART)
        pygame.draw.rect(self.screen, colors[3], rect.inflate(-2, -2))
        text = self.font.render("BLAST", True, (0, 0, 0))
        self.screen.blit(text, text.get_rect(center=rect.center))

        if self.board.game_over:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            text = self.font.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(text, text.get_rect(center=self.screen.get_rect().center))

        # Draw restart button
        rect = pygame.Rect(0, self.board.height * TILE_SIZE, self.board.width * TILE_SIZE, Y_RESTART)
        pygame.draw.rect(self.screen, colors["restart"], rect.inflate(-2, -2))
        text = self.font.render("RESTART", True, (0, 0, 0))
        self.screen.blit(text, text.get_rect(center=rect.center))
        pygame.display.flip()
    
    # def outline_chunks(self):
    #     width = 3
    #     for chunk in self.board.identify_chunks():
    #         cell_set = set(chunk)
            
    #         for x, y in chunk:
    #             # Pixel coords of the cell
    #             px = x * TILE_SIZE
    #             py = y * TILE_SIZE
    #             rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)

    #             # Check neighbors; if neighbor missing, draw that edge
    #             neighbors = {
    #                 "top":    (x, y-1) not in cell_set,
    #                 "bottom": (x, y+1) not in cell_set,
    #                 "left":   (x-1, y) not in cell_set,
    #                 "right":  (x+1, y) not in cell_set
    #             }

    #             if neighbors["top"]:
    #                 pygame.draw.line(self.screen, colors[3], (px, py), (px + TILE_SIZE, py), width)
    #             if neighbors["bottom"]:
    #                 pygame.draw.line(self.screen, colors[3], (px, py + TILE_SIZE), (px + TILE_SIZE, py + TILE_SIZE), width)
    #             if neighbors["left"]:
    #                 pygame.draw.line(self.screen, colors[3], (px, py), (px, py + TILE_SIZE), width)
    #             if neighbors["right"]:
    #                 pygame.draw.line(self.screen, colors[3], (px + TILE_SIZE, py), (px + TILE_SIZE, py + TILE_SIZE), width)


# ------------------------
# Main Loop
# ------------------------

N_TILES_X = 10
N_TILES_Y = 15
N_MINES = 20

def main():
    pygame.init()
    screen = pygame.display.set_mode((N_TILES_X * TILE_SIZE, N_TILES_Y * TILE_SIZE + 3 * Y_RESTART))
    board = GameBoard(width=N_TILES_X, height=N_TILES_Y, initial_mines = N_MINES)
    renderer = GameRenderer(screen, board)

    clock = pygame.time.Clock()
    # game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if y <= N_TILES_Y * TILE_SIZE and not board.game_over:
                    print('CLICK', x, y)
                    grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
                    board.reveal_tile(grid_x, grid_y)
                    # if board.reveal_tile(grid_x, grid_y) == "M":
                    #     print("Game Over!")
                    #     game_over = True
                elif y >= N_TILES_Y * TILE_SIZE and y <= N_TILES_Y * TILE_SIZE + Y_RESTART:
                    print('RESTART')
                    board = GameBoard(width=N_TILES_X, height=N_TILES_Y, initial_mines = N_MINES)
                    renderer.board = board
                    # game_over = False
                elif not board.game_over and y >= N_TILES_Y * TILE_SIZE + Y_RESTART and y <= N_TILES_Y * TILE_SIZE + 2 * Y_RESTART:
                    print('GRAVITY')
                    board.enact_gravity()
                elif not board.game_over and y >= N_TILES_Y * TILE_SIZE + 2 * Y_RESTART:
                    print('BLAST')
                    board.blast()
                else:
                    print("Clicked outside grid")
                    
            elif event.type == pygame.KEYDOWN and not board.game_over:
                if event.key == pygame.K_SPACE:
                    x, y = pygame.mouse.get_pos()
                    grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
                    if grid_y <= N_TILES_Y:
                        text = board.space_bar_tile(grid_x, grid_y)
                        # if text == "M":
                        #     print("Game Over!")
                        #     game_over = True
                        # else:
                        #     print(text)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_o:
                        renderer.show_outlines = not renderer.show_outlines


        renderer.draw()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
