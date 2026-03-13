##############################################################################################################################
# coding=utf-8
#
# g2048.py
#   -- Python implementation of the 2048 game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>
#
# modified from the ORIGINAL code @ https://github.com/DBgirl/PyGames
#

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2026-03-09"
__updated__ = "2026-03-11"

import pygame
import random
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsLogging import *

GAME_LENGTH = 4 # 4x4 tiles
TILE_SIZE = 150 # pixels per side
GAP_SIZE = 10
MARGIN = 20
FRAME_LENGTH = GAME_LENGTH*TILE_SIZE + (GAME_LENGTH+1)*GAP_SIZE + 2*MARGIN
BACKGROUND_COLOR = (248, 248, 236)
TILE_COLORS = {
    2   : (238, 238, 118),
    4   : ( 76, 214, 180),
    8   : (242, 177, 121),
    16  : (245, 149,  49),
    32  : (246, 124,  95),
    64  : (137, 204,  97),
    128 : ( 37, 107, 114),
    256 : (146, 124, 239),
    512 : (237, 200,  80),
    1024: (117,  27, 238),
    2048: (  3, 244, 246)
}
FONT_COLOR = (0, 0, 0)

def draw_tile(screen, value, x, y):
    color = TILE_COLORS.get(value, (60, 58, 50))
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, color, rect)
    if value != 0:
        text = gfont.render(str(value), True, FONT_COLOR)
        text_rect = text.get_rect(center=(x + TILE_SIZE / 2, y + TILE_SIZE / 2))
        screen.blit(text, text_rect)

def draw_board(screen, board):
    screen.fill(BACKGROUND_COLOR)
    for row in range(GAME_LENGTH):
        for col in range(GAME_LENGTH):
            value = board[row][col]
            x = MARGIN + GAP_SIZE + col * (TILE_SIZE + GAP_SIZE)
            y = MARGIN + GAP_SIZE + row * (TILE_SIZE + GAP_SIZE)
            draw_tile(screen, value, x, y)

def add_new_tile(board):
    empty_tiles = [(r, c) for r in range(GAME_LENGTH) for c in range(GAME_LENGTH) if board[r][c] == 0]
    if empty_tiles:
        row, col = random.choice(empty_tiles)
        board[row][col] = 2 if random.random() < 0.9 else 4

def slide_row_left(row):
    new_row = [i for i in row if i != 0]
    new_row += [0] * (GAME_LENGTH-len(new_row))
    for i in range(GAME_LENGTH-1):
        if new_row[i] == new_row[i + 1] and new_row[i] != 0:
            new_row[i] *= 2
            new_row[i + 1] = 0
    new_row = [i for i in new_row if i != 0]
    new_row += [0] * (GAME_LENGTH-len(new_row))
    return new_row

def move_left(board):
    new_board = []
    for row in board:
        new_board.append(slide_row_left(row))
    return new_board

def move_right(board):
    new_board = []
    for row in board:
        new_board.append(slide_row_left(row[::-1])[::-1])
    return new_board

def move_up(board):
    lgr.debug(f"board = {board}")
    lgr.debug(f"zip(*board) = {zip(*board)}")
    lgr.debug(f"list(zip(*board)) = {list(zip(*board))}")
    new_board = list(zip(*board))
    new_board = move_left(new_board)
    lgr.debug(f"new_board = {new_board}")
    result = [list(row) for row in zip(*new_board)]
    lgr.debug(f"result = {result}")
    return result

def move_down(board):
    new_board = list(zip(*board))
    new_board = move_right(new_board)
    return [list(row) for row in zip(*new_board)]

def check_win(board):
    for row in board:
        if 2048 in row:
            return True
    return False

def check_moves_available(board):
    for row in range(GAME_LENGTH):
        if 0 in board[row]:
            return True
        for col in range(GAME_LENGTH-1):
            if board[row][col] == board[row][col + 1]:
                return True
    for col in range(GAME_LENGTH):
        for row in range(GAME_LENGTH-1):
            if board[row][col] == board[row + 1][col]:
                return True
    return False

def run():
    frame = pygame.display.set_mode((FRAME_LENGTH, FRAME_LENGTH))
    pygame.display.set_caption("My 2048 Game")
    # frame.
    clock = pygame.time.Clock()

    board = [[0]*GAME_LENGTH for _ in range(GAME_LENGTH)]
    add_new_tile(board)
    add_new_tile(board)

    running = True
    won = False
    lost = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if not won and not lost:
                    if event.key == pygame.K_LEFT:
                        board = move_left(board)
                    elif event.key == pygame.K_RIGHT:
                        board = move_right(board)
                    elif event.key == pygame.K_UP:
                        board = move_up(board)
                    elif event.key == pygame.K_DOWN:
                        board = move_down(board)
                    add_new_tile(board)
                    won = check_win(board)
                    lost = not check_moves_available(board)

        draw_board(frame, board)
        rect_dim = FRAME_LENGTH // 2
        if won:
            text = gfont.render("You won!", True, (255, 0, 0))
            text_rect = text.get_rect(center=(rect_dim, rect_dim))
            frame.blit(text, text_rect)
        elif lost:
            text = gfont.render("You lost!", True, (255, 0, 0))
            text_rect = text.get_rect(center=(rect_dim, rect_dim))
            frame.blit(text, text_rect)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


log_control = MhsLogger("Game2048", con_level = DEFAULT_LOG_LEVEL)

if __name__ == "__main__":
    code = 0
    try:
        lgr = log_control.get_logger()
        pygame.init()
        gfont = pygame.font.SysFont('arial', 40)
        run()
    except KeyboardInterrupt as mki:
        log_control.exception(mki)
        code = 13
    except ValueError as mve:
        log_control.error(mve)
        code = 27
    except Exception as mex:
        log_control.exception(mex)
        code = 66
    exit(code)
