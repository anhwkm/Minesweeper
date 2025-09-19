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
        self.score = 0


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
    
    def get_score(self):
        return self.score

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
        grid_T = list(zip(*self.flagged))
        to_blast_x = [x for x in range(self.width) if all(grid_T[x])]
        to_blast_y = [y for y in range(self.height) if all(self.flagged[y])]
        for x in range(self.width):
            for y in range(self.height):
                if x in to_blast_x or y in to_blast_y:
                    self.revealed[y][x] = True
                    self.flagged[y][x] = False
                    if self.grid[y][x] == "M":
                        self.grid[y][x] = "0"
                    else:
                        self.game_over = True
        self.score += self.height * len(to_blast_x) + self.width * len(to_blast_y)
        self.grid = self.calculate_board(self.grid)

    def print_grid(self):
        print("\nCurrent Grid:")
        for y, row in enumerate(self.grid):
            row_str = ""
            for x, cell in enumerate(row):
                if self.revealed[y][x]:
                    if self.flagged[y][x]:
                        row_str += "F"  # flagged
                    else:
                        row_str += str(cell)  # show actual value
                else:
                    row_str += "#"  # unrevealed
            print(row_str)
        print("-" * self.width)



    def enact_gravity(self):
        top_chunk, chunks = self.identify_chunks()
        moved = True
        while moved: # keep going until no chunks can fall
            moved = False
            for chunk in chunks:
                if self.can_fall(chunk):
                    print("fall")
                    self.fall_chunk(chunk)
                    moved = True
                # if top chunk can fall, it does, and a new row is added
            if top_chunk:
                if self.can_fall(top_chunk):
                    print("top fall")
                    self.fall_chunk(top_chunk)
                    top_chunk = self.encroach(top_chunk)
                    print(top_chunk)
                    moved = True
                else:
                    print("top can't fall")
                    print(top_chunk)
                    self.print_grid()
            elif all(self.revealed[0]):
                print("new top")
                top_chunk = self.encroach()
                print(top_chunk)
                moved = True
            else:
                print("no top fall")
        self.grid = self.calculate_board(self.grid)
    
    def encroach(self, top_chunk=None):
        if top_chunk is None:
            top_chunk = set()
        print(top_chunk)
        # check if row 0 is entirely revealed:
        if not all(self.revealed[0]):
            print("CATASTROPHE")
            raise ValueError("Trying to encroach when top row not fully revealed")
        new_row = [0] * self.width
        n_mines = self.initial_mines // self.height
        n_mines = random.randint(max(0, n_mines - 2), min(self.width, n_mines + 2))
        mine_positions = random.sample(range(self.width), n_mines)
        for x in mine_positions:
            new_row[x] = "M"
        self.grid[0] = new_row
        self.revealed[0] = [False]*self.width
        self.flagged[0] = [False]*self.width
        # self.grid = self.calculate_board(self.grid)

        # if any chunk touches the top row, add this row to it
        # previous steps made sure only one chunk can touch top row
        # top_chunks = [c for c in chunks if any(y == 1 for x, y in c)]
        # if len(top_chunks) > 1: print("CATASTROPHE 2")
        kerchunk = set([(x, 0) for x in range(self.width)])
        print(self.width, self.height)
        print(kerchunk)
        # for c in top_chunks:
        #         kerchunk.update(c)
        #         chunks.remove(c)
        top_chunk.update(kerchunk)
        print(top_chunk)
        return top_chunk

    def cheat(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != "M":
                    self.revealed[y][x] = True
                else:
                    self.flagged[y][x] = True
        self.grid = self.calculate_board(self.grid)

    def fall_chunk(self, chunk):
        # input("Press Enter to step...")
        # self.print_grid()
        new_chunk = set()
        # Move all cells in chunk down by 1
        for x, y in sorted(chunk, key=lambda c: -c[1]):  # Sort by y descending
            if self.revealed[y][x]:
                print("Error: trying to move revealed cell", x, y)
                print(self.revealed)
                print(self.grid)
                print(chunk)
                raise ValueError("Trying to move revealed cell")
            if not self.revealed[y + 1][x]:
                print("Error: trying to move into non-revealed cell", x, y)
                print(self.revealed)
                print(self.grid)
                print(chunk)
            self.grid[y + 1][x] = self.grid[y][x]
            self.revealed[y + 1][x] = self.revealed[y][x]
            self.flagged[y + 1][x] = self.flagged[y][x]
            self.grid[y][x] = 0
            self.revealed[y][x] = True
            self.flagged[y][x] = False
            new_chunk.add((x, y + 1))
        chunk.clear()
        chunk.update(new_chunk)
            

    

    def can_fall(self, chunk):
        for x, y in chunk:
            if y + 1 >= self.height:
                return False
            # can fall if space below is unrevealed or within same chunk
            if not (self.revealed[y + 1][x] or (x, y + 1) in chunk):
                return False
        return True

    def identify_chunks(self):
        # shallow copy, mark revealed as visited
        visited = [row[:] for row in self.revealed]
        flagged_chunks = []
        for y in range(self.height):
            for x in range(self.width):
                if self.flagged[y][x]:
                    flagged_chunks.append(set([(x, y)]))
                    visited[y][x] = True  # treat empty as visited

        chunks = []    
        for y in range(self.height):
            for x in range(self.width):
                if not visited[y][x]:
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
        top_chunk = set()
        top_chunks = [c for c in chunks if any(y == 0 for x, y in c)]
        if top_chunks:
            for c in top_chunks:
                top_chunk.update(c)
                chunks.remove(c)
        chunks.extend(flagged_chunks)
        print(f"Identified {len(chunks)} chunks, top chunk size {len(top_chunk)}")
        return top_chunk, chunks

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




colors = {
    'GRAVITY': (0, 128, 0), # green for gravity button
    'BLAST': (255, 0, 0), # red for blast button
    'RESTART': (200, 200, 0), # yellow for restart button
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
        self.font_small = pygame.font.SysFont(None, 18)
        # self.show_outlines = False

    def draw_button(self, text, starting_y, height, font, color=None, font_color=(0, 0, 0)):
        if color is None:
            color = colors[text]
        rect = pygame.Rect(0, starting_y, self.board.width * TILE_SIZE, height)
        pygame.draw.rect(self.screen, color, rect.inflate(-2, -2))
        text = font.render(text, True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def draw(self):
        self.screen.fill((0, 0, 0))
        for y, row in enumerate(self.board.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE + SCORE_HEIGHT, TILE_SIZE, TILE_SIZE)
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

        if self.board.game_over:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            text = self.font.render("GAME OVER", True, (255, 0, 0))
            self.screen.blit(text, text.get_rect(center=self.screen.get_rect().center))

        self.draw_button(f"SCORE: {self.board.get_score()}", 0, SCORE_HEIGHT, self.font_small, (0, 0, 0), (255, 255, 255))
        self.draw_button("GRAVITY", SCORE_HEIGHT + GRID_HEIGHT, BUTTON_HEIGHT, self.font)
        self.draw_button("BLAST", SCORE_HEIGHT + GRID_HEIGHT + BUTTON_HEIGHT, BUTTON_HEIGHT, self.font)
        self.draw_button("RESTART", SCORE_HEIGHT + GRID_HEIGHT + 2 * BUTTON_HEIGHT, BUTTON_HEIGHT, self.font)
        pygame.display.flip()











# ------------------------
# Main Loop
# ------------------------

TILE_SIZE = 30
BUTTON_HEIGHT = 60
SCORE_HEIGHT = 30

N_TILES_X = 10
N_TILES_Y = 15
N_MINES = 20
GRID_HEIGHT = N_TILES_Y * TILE_SIZE

def main():
    pygame.init()
    screen = pygame.display.set_mode((N_TILES_X * TILE_SIZE, GRID_HEIGHT + (3 * BUTTON_HEIGHT) + SCORE_HEIGHT))
    board = GameBoard(width=N_TILES_X, height=N_TILES_Y, initial_mines = N_MINES)
    renderer = GameRenderer(screen, board)

    clock = pygame.time.Clock()

    def pixel_to_grid(x, y):
        grid_x = x // TILE_SIZE
        grid_y = (y - SCORE_HEIGHT) // TILE_SIZE
        return grid_x, grid_y
    

    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if not board.game_over:
                    if (y > SCORE_HEIGHT) and (y < SCORE_HEIGHT + GRID_HEIGHT):
                        print('CLICK', x, y)
                        grid_x, grid_y = pixel_to_grid(x, y)
                        board.reveal_tile(grid_x, grid_y)
                    elif (y > SCORE_HEIGHT + GRID_HEIGHT) and (y < SCORE_HEIGHT + GRID_HEIGHT + BUTTON_HEIGHT):
                        print('GRAVITY')
                        board.enact_gravity()
                    elif (y > SCORE_HEIGHT + GRID_HEIGHT + BUTTON_HEIGHT) and (y < SCORE_HEIGHT + GRID_HEIGHT + 2 * BUTTON_HEIGHT):
                        print('BLAST')
                        board.blast()
                if (y > SCORE_HEIGHT + GRID_HEIGHT + 2 * BUTTON_HEIGHT):
                    print('RESTART')
                    # board.cheat()  # For testing, reveal all
                    board = GameBoard(width=N_TILES_X, height=N_TILES_Y, initial_mines = N_MINES)
                    renderer.board = board
                    
            elif event.type == pygame.KEYDOWN and not board.game_over:
                if event.key == pygame.K_SPACE:
                    x, y = pygame.mouse.get_pos()
                    grid_x, grid_y = pixel_to_grid(x, y)
                    if grid_y <= N_TILES_Y:
                        board.space_bar_tile(grid_x, grid_y)
        renderer.draw()
        clock.tick(30)


if __name__ == "__main__":
    main()
