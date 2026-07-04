##############################################################################################################################
# coding=utf-8
#
# wordlePyside6_UI.py
#   -- the UI for the Wordle game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2026-03-05"
__updated__ = "2026-07-05"

import subprocess
from enum import IntEnum
from sys import argv
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QMainWindow, QMessageBox, QLineEdit)
from wordleGameEngine import *

class WdFontSize(IntEnum):
    Xsmall  = 12
    Small   = 16
    SmMed   = 20
    Medium  = 24
    MedLarg = 28
    Large   = 32
    Xlarge  = 36


SMALL_FONT  = f"font-size: {WdFontSize.Small}pt;"
MEDIUM_FONT = f"font-size: {WdFontSize.Medium}pt;"
LARGE_FONT  = f"font-size: {WdFontSize.Large}pt;"
FONT_BOLD   = "font-weight: bold;"
FONT_ITALIC = "font-style: italic;"
INFO_TEXT = ("   How to Play the Game:\n"
             "---------------------------------------------\n"
             f"1) Using ONLY the displayed letters, enter a word (at least {MIN_WORD_LENGTH} letters long) in the 'Try' box.\n\n"
             "2) Any number of each displayed letter is allowed, but the Central letter MUST be present in the word.\n\n"
             "3) Press ENTER to evaluate your guess.\n\n"
             "4) FYI, most simple plurals are just ignored... \n\n"
             "5) You can press the space bar to scramble the PLACEMENT of the outer letters.\n\n"
             "6) Your Valid or Invalid guesses are displayed in the appropriate boxes.\n\n"
             "7) Pangrams are words that use ALL seven letters -- and earn DOUBLE points!\n\n"
             "8) Exit the game when you are ready and your game information will be saved to a JSON file.")
ORDERED_LETTERS = "EAOIUYSRLTNDCPMHGBKWFVZJXQ"
WDUI_DEBUG = False

def display_info():
    infobox = QMessageBox()
    infobox.setIcon(QMessageBox.Icon.Information)
    infobox.setStyleSheet(SMALL_FONT)
    infobox.setText(INFO_TEXT)
    # infobox.setMinimumWidth(960) # DOES NOTHING... ?!
    infobox.exec()

def confirm_exit():
    confirm_box = QMessageBox()
    confirm_box.setIcon(QMessageBox.Icon.Question)
    confirm_box.setStyleSheet("font-size: 16pt")
    confirm_box.setText("    Are you SURE you want to EXIT the game?    ")
    cancel_button = confirm_box.addButton("No! >> Continue the game...", QMessageBox.ButtonRole.ActionRole)
    cancel_button.setStyleSheet("background: chartreuse")
    newgame_button = confirm_box.addButton("Yes >> START a NEW game!", QMessageBox.ButtonRole.ActionRole)
    newgame_button.setStyleSheet("color: green; background: MediumVioletRed")
    proceed_button = confirm_box.addButton("Yes >> EXIT the game.", QMessageBox.ButtonRole.ActionRole)
    proceed_button.setStyleSheet("color: yellow; background: purple")
    confirm_box.setDefaultButton(cancel_button)
    return confirm_box, proceed_button, cancel_button, newgame_button

def check_screen_locked(lgr:logging.Logger=None) -> bool:
    """See if a screensaver is active."""
    try:
        output = subprocess.check_output(["mate-screensaver-command", "-q"]).decode()
        if output:
            if lgr and WDUI_DEBUG:
                lgr.debug(f"Mate screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr:
            lgr.warning("Mate screensaver NOT found!")
    try:
        output = subprocess.check_output(["gnome-screensaver-command", "-q"]).decode()
        if output:
            if lgr and WDUI_DEBUG:
                lgr.debug(f"Gnome screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr and WDUI_DEBUG:
            lgr.warning("Gnome screensaver NOT found!")
    return False

# noinspection PyAttributeOutsideInit
class WordleUI(QMainWindow):
    """UI to play the Wordle game."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Wordle Game")
        # pixels: dx from left, dx from top, width, height
        self.setGeometry(500, 50, 640, 640)

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.windowTitle()} runtime = {get_current_time()}")

        self.ge = GameEngine(self.lgr)

        main_layout = QVBoxLayout()
        main_layout.addLayout(self.create_guess_rows())
        main_layout.addWidget(self.create_message_box())
        main_layout.addLayout(self.create_result_section())
        main_layout.addLayout(self.create_button_section())

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.reset()
        self.show()

    def reset(self):
        """Reset all the items needed to start a new game."""
        self.lgr.info("\n\nStarting a NEW Game!")
        self.ge.start()
        self.guess_boxes[0].setFocus()
        self.active_row = 0
        self.active_box = 0
        # game clock
        self.clock.setText("00")
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

    def close(self, /):
        self.ge.save_record()
        super().close()

    def create_message_box(self):
        self.message_box = QLineEdit()
        self.message_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_box.setFrame(True)
        self.message_box.setReadOnly(True)
        self.message_box.setStyleSheet(f"{SMALL_FONT} color:red")
        return self.message_box

    def create_guess_box(self):
        guess_box = QLineEdit()
        guess_box.setText(' ')
        guess_box.setStyleSheet(f"color: blue; background: white; font-size: {WdFontSize.Xlarge}pt")
        guess_box.setFrame(True)
        guess_box.resize(64,64)
        guess_box.textEdited.connect(self.response_change)
        guess_box.returnPressed.connect(self.process_response)
        guess_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return guess_box

    def create_guess_rows(self):
        qvb_layout = QVBoxLayout()
        self.guess_boxes = []
        for i in range(30):
            self.guess_boxes.append(self.create_guess_box())
        self.lgr.info(f"Have {len(self.guess_boxes)} guess boxes.")

        self.guess_rows = []
        for k in range(6):
            self.lgr.info(f"Setting guess row #{k}")
            self.guess_rows.append(QHBoxLayout())
            left_spacer = QLabel()
            self.guess_rows[k].addWidget(left_spacer)
            self.guess_rows[k].setStretchFactor(left_spacer, 2)
            for l in range(5):
                self.lgr.info(f"Setting guess box #{k}-{l}")
                self.guess_rows[k].addWidget(self.guess_boxes[(5*k)+l])
                self.guess_rows[k].setStretchFactor(self.guess_boxes[(5*k)+l], 1)
            right_spacer = QLabel()
            self.guess_rows[k].addWidget(right_spacer)
            self.guess_rows[k].setStretchFactor(right_spacer, 2)
            qvb_layout.addItem(self.guess_rows[k])
        return qvb_layout

    @staticmethod
    def create_result_box(p_letter:str):
        result_box = QLineEdit()
        result_box.setText(p_letter)
        result_box.setReadOnly(True)
        result_box.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: black")
        result_box.setFrame(False)
        result_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return result_box

    def create_result_section(self):
        qvb_layout = QVBoxLayout()
        self.result_boxes = []
        for i in range(len(ORDERED_LETTERS)):
            self.result_boxes.append(self.create_result_box(ORDERED_LETTERS[i]))
        self.lgr.info(f"Have {len(self.result_boxes)} result boxes.")

        self.vowel_row = QHBoxLayout()
        for j in range(6):
            self.vowel_row.addWidget(self.result_boxes[j])
        qvb_layout.addItem(self.vowel_row)

        self.consonant_rows = []
        for k in range(4):
            self.consonant_rows.append(QHBoxLayout())
            for l in range(1,6):
                self.consonant_rows[k].addWidget(self.result_boxes[5*(k+1)+l])
            qvb_layout.addItem(self.consonant_rows[k])

        return qvb_layout

    def create_button_section(self):
        """The instructions and exit/new game buttons and clock section of the UI."""
        info_btn = QPushButton("Game Instructions")
        info_btn.setStyleSheet(f"{MEDIUM_FONT} color: yellow; background: blue")
        info_btn.setAutoDefault(False)
        info_btn.setDefault(False)
        info_btn.clicked.connect(display_info)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.update_seconds = 1
        cfont = self.font()
        cfont.setPointSize(WdFontSize.Medium)
        self.clock.setFont(cfont)
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(self.update_seconds * 1000) # update interval

        newgame_exit_btn = QPushButton("Exit Game?")
        newgame_exit_btn.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: red; background: yellow")
        newgame_exit_btn.setAutoDefault(False)
        newgame_exit_btn.setDefault(False)
        newgame_exit_btn.clicked.connect(self.exit_inquiry)

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(info_btn)
        qhb_layout.addWidget(self.clock)
        qhb_layout.addWidget(newgame_exit_btn)
        return qhb_layout

    def response_change(self, resp:str):
        self.lgr.info(f"Response changed to: '{resp}'")
        if resp:
            self.message_box.setText(f"box[{self.active_row}-{self.active_box}] has focus. Text = '{resp}'")

    def process_response(self):
        pass

    def update_clock(self):
        """Update the game clock when the game is active."""
        log_pause = 600 if self.lock_count > 10 else 60
        locked = check_screen_locked(self.lgr) # pause when the screen is locked
        if locked or self.isMinimized() or self.isHidden(): # pause when the game is inactive
            self.pause_secs += 1
            if self.pause_secs % log_pause == 0:
                self.lock_count += 1
                self.lgr.info(f"{self.pause_secs}: Screen is " + ("locked." if locked else "minimized or hidden."))
            return
        self.pause_secs = 0
        self.lock_count = 0
        self.run_secs += 1
        self.clock.setText("{:02}:{:02}:{:02}".format(self.run_secs // 3600, self.run_secs % 3600 // 60, self.run_secs % 3600 % 60))

    def exit_inquiry(self):
        """Confirm that the user wants to exit the current game."""
        confirm_box, initiate_exit_button, continue_game_button, new_game_button = confirm_exit()
        confirm_box.exec()
        if confirm_box.clickedButton() == initiate_exit_button:
            self.lgr.info("Proceed to EXIT!")
            self.close()
        elif confirm_box.clickedButton() == continue_game_button:
            self.lgr.info("Continue the game...")
        elif confirm_box.clickedButton() == new_game_button:
            self.lgr.info("Exit and START a new game.")
            self.ge.save_record()
            # new game
            self.reset()
# END class WordleUI


log_control = MhsLogger(WordleUI.__name__, con_level = DEFAULT_LOG_LEVEL)

if __name__ == "__main__":
    if len(argv) > 1:
        print(f"Usage: python3 {get_filename(argv[0])}\nLaunch the SpellingBee game UI.")
        log_control.debug("Usage instructions.")
        exit(0)
    dialog = None
    app = None
    code = 0
    try:
        app = QApplication(argv)
        dialog = WordleUI()
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
        if dialog:
            dialog.close()
        if app:
            app.exit(code)
    exit(code)
