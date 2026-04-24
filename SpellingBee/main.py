##############################################################################################################################
# coding=utf-8
#
# main.py
#   -- launch the SpellingBee game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-11-08"
__updated__ = "2026-04-23"

from spellingbeePyside6_UI import *

if __name__ == "__main__":
    if len(argv) > 1:
        print(f"Usage: python3 {get_filename(argv[0])}\nLaunch the SpellingBee game.")
        exit(0)
    window = None
    app = None
    code = 0
    try:
        app = QApplication(argv)
        window = SpellingBeeUI()
        app.exec()
    except KeyboardInterrupt as mki:
        log_control.exception(mki)
        code = 13
    except ValueError as mve:
        log_control.exception(mve)
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
