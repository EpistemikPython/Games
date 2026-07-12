##############################################################################################################################
# coding=utf-8
#
# main.py
#   -- launch the Wordle game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.11+"
__created__ = "2026-03-05"
__updated__ = "2026-07-12"

from wordleGame import *

if __name__ == "__main__":
    usage_text = f"Usage: python3 {get_filename(argv[0])} [$word_length] [$num_rows]\n"
    if len(argv) > 3:
        print(usage_text)
        log_control.debug("Usage instructions.")
        exit(0)
    window = None
    app = None
    code = 0
    try:
        app = QApplication(argv)
        if len(argv) > 2:
            if not argv[1].isdigit() or not argv[2].isdigit():
                print(usage_text)
                log_control.debug("Invalid arguments.")
                raise Exception("Invalid arguments.")
            window = WordleUI(int(argv[1]), int(argv[2]))
            print(f"argv[1]: {argv[1]}, argv[2]: {argv[2]}")
        elif len(argv) > 1:
            if not argv[1].isdigit():
                print(usage_text)
                log_control.debug("Invalid arguments.")
                raise Exception("Invalid arguments.")
            window = WordleUI(int(argv[1]))
            print(f"argv[1]: {argv[1]}, p_rows = {DEFAULT_NUM_ROWS}")
        else:
            window = WordleUI()
            print("No arguments.")
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
