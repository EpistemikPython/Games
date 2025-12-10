##############################################################################################################################
# coding=utf-8
#
# main.py
#   -- launch the MineSweeper game
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-13"
__updated__ = "2025-12-03"

from main_window import *

if __name__ == "__main__":
    log_control.info(f"sys.argv = {sys.argv}")
    grid_len = DEFAULT_GRID_LEN
    if len(sys.argv) > 1 and sys.argv[1].isnumeric():
        grid_len = int(sys.argv[1])
    num_mines = DEFAULT_NUM_MINES
    if len(sys.argv) > 2 and sys.argv[2].isnumeric():
        num_mines = int(sys.argv[2])
    window = None
    app = None
    code = 0
    try:
        app = QApplication(sys.argv)
        window = MineSweeperUI(grid_len, num_mines)
        app.exec()
    except KeyboardInterrupt as mki:
        log_control.exception(mki)
        code = 13
    except ValueError as mve:
        log_control.error(mve)
        code = 27
    except Exception as mex:
        log_control.exception(mex)
        code = 66
    finally:
        if window:
            window.close()
        if app:
            app.exit(code)
    exit(code)
