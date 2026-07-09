##############################################################################################################################
# coding=utf-8
#
# wordleGame.py
#   -- my Python implementation of the Wordle game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.11+"
__created__ = "2026-07-05"
__updated__ = "2026-07-09"

import subprocess
import random
from sys import argv, path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QMainWindow, QMessageBox, QLineEdit, QFrame)
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
path.append("/home/marksa/git/Python/Games/Wordle/input")
from wordle_words import all_wordle_words as all_words

MIN_WORD_LENGTH = 5
MAX_WORD_LENGTH = 13
DEFAULT_NUM_ROWS = 6

MEDIUM_FONT_SIZE = 24
SMALL_FONT  = "font-size: 16pt;"
MEDIUM_FONT = f"font-size: {MEDIUM_FONT_SIZE}pt;"
XLARGE_FONT = "font-size: 36pt;"
FONT_BOLD   = "font-weight: bold;"
INPUT_COLOR = "gray" # "rgb(241, 241, 241)"

ORDERED_LETTERS = "AEIOUYLNRSTCDHMPBFGKWJQVXZ"
INFO_TEXT = ("           How to Play Wordle:\n"
             "---------------------------------------------\n"
             f"1) You are trying to guess the secret {MIN_WORD_LENGTH}-letter word.\n\n"
             f"2) With the keyboard type a {MIN_WORD_LENGTH}-letter word and press ENTER to evaluate it.\n\n"
             "3) A letter in the correct position will shade green.\n\n"
             "4) A letter present in the secret word but in the wrong position in your guess will shade yellow.\n\n"
             "5) A letter NOT present in the secret word will shade grey.\n\n"
             "6) Your entry will NOT be accepted if it is NOT a valid Wordle word.\n\n"
             f"7) You have {DEFAULT_NUM_ROWS} attempts to find the secret word.\n\n"
             "8) When you are ready, exit the game or start a new word and your current game information will be saved to a JSON file.")

DEBUG_TARGET = "FELIS" # test words = MESSY, LEAFY, SILLY, AFFIX, SLIME, FLESH
# DEBUG_TARGET = "PUPPY" # test words = APPLE, PAPER, PLUMP, TAUPE, UPPER, GUPPY
# DEBUG_TARGET = "GUPPY" # test words = PLUMP, PAPER, UPPER, UNDUE, PUPPY, BUGGY
WORDLE_DEBUG = False

GUESS_BASIC_STYLESHEET  = f"{XLARGE_FONT}; color: blue;  background: white"
GUESS_EXACT_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: green; {FONT_BOLD}"
GUESS_OCCUR_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: yellow"
GUESS_ABSENT_STYLESHEET = f"{XLARGE_FONT}; color: white; background: gray"
RESULT_BASIC_STYLESHEET  = f"{FONT_BOLD} {MEDIUM_FONT} color: black"
RESULT_OCCUR_STYLESHEET  = f"{FONT_BOLD} {MEDIUM_FONT} color: green"
RESULT_ABSENT_STYLESHEET = f"{FONT_BOLD} {MEDIUM_FONT} color: red"
INPUTBOX_STYLESHEET = f"{SMALL_FONT} color: {INPUT_COLOR}; background: white" if WORDLE_DEBUG \
                      else f"{SMALL_FONT} color: {INPUT_COLOR}; background: {INPUT_COLOR}"

def check_screen_locked(lgr:logging.Logger=None) -> bool:
    """See if a screensaver is active."""
    try:
        output = subprocess.check_output(["mate-screensaver-command", "-q"]).decode()
        if output:
            if lgr and WORDLE_DEBUG:
                lgr.debug(f"Mate screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr:
            lgr.warning("Mate screensaver NOT found!")
    try:
        output = subprocess.check_output(["gnome-screensaver-command", "-q"]).decode()
        if output:
            if lgr and WORDLE_DEBUG:
                lgr.debug(f"Gnome screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr and WORDLE_DEBUG:
            lgr.warning("Gnome screensaver NOT found!")
    return False

# noinspection PyAttributeOutsideInit
class WordleUI(QMainWindow):
    """UI to play the Wordle game."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Wordle Game")
        # pixels: dx from left, dy from top, width, height
        self.setGeometry(575, 140, 600, 750)

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.windowTitle()} runtime = {get_current_time()}")

        self.ge = WordleGameEngine(self.lgr)

        # TODO: implement hard mode
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.create_top_section())
        main_layout.addLayout(self.create_guess_section())
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
        self.lgr.info("Starting a NEW Game!")
        self.ge.start()
        self.active = True
        self.current_guess = ''
        self.input_box.clear()
        self.reset_guesses()
        self.reset_results()
        self.active_row = 0
        self.button_hover = False
        self.input_box.setFocus()
        # game clock
        self.clock.setText("00")
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

    def close(self, /):
        self.ge.save_record()
        super().close()

    def create_top_section(self):
        """The input and clock section of the UI."""
        self.input_box = QLineEdit()
        self.input_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_box.setFrame(False)
        self.input_box.setReadOnly(False)
        # restrict acceptable input to 5 uppercase letters
        self.input_box.setInputMask(">AAAAA")
        self.input_box.setStyleSheet(INPUTBOX_STYLESHEET)
        self.input_box.textEdited.connect(self.response_change)
        self.input_box.returnPressed.connect(self.process_response)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.update_seconds = 1
        cfont = self.font()
        cfont.setPointSize(MEDIUM_FONT_SIZE)
        self.clock.setFont(cfont)
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(self.update_seconds * 1000) # update interval

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.input_box)
        qhb_layout.setStretchFactor(self.input_box, 1)
        left_spacer = QLabel()
        qhb_layout.addWidget(left_spacer)
        qhb_layout.setStretchFactor(left_spacer, 2 if WORDLE_DEBUG else 20)
        qhb_layout.addWidget(self.clock)
        qhb_layout.setStretchFactor(self.clock, 2)
        return qhb_layout

    def create_message_box(self):
        self.message_box = QLineEdit()
        self.message_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_box.setFrame(True)
        self.message_box.setReadOnly(True)
        self.message_box.setStyleSheet(f"{SMALL_FONT} color:red")
        return self.message_box

    @staticmethod
    def create_guess_box(p_text:str=''):
        guess_box = QLabel()
        guess_box.resize(75,75)
        guess_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        guess_box.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        if p_text:
            guess_box.setText(p_text)
        return guess_box

    def create_guess_section(self):
        qvb_layout = QVBoxLayout()
        row_len = self.ge.word_length
        num_rows = self.ge.num_rows
        self.guess_boxes = [[self.create_guess_box(f"{j}-{i}") for i in range(row_len)] for j in range(num_rows)]
        for j in range(num_rows):
            for k in range(row_len):
                self.lgr.debug(self.guess_boxes[j][k].text())

        layout_rows = []
        for k in range(num_rows):
            self.lgr.debug(f"Setting guess row #{k}")
            layout_rows.append(QHBoxLayout())
            left_spacer = QLabel()
            layout_rows[k].addWidget(left_spacer)
            layout_rows[k].setStretchFactor(left_spacer, 2)
            for l in range(row_len):
                self.lgr.debug(f"Setting guess box #{k}-{l}")
                self.guess_boxes[k][l].setText('')
                layout_rows[k].addWidget(self.guess_boxes[k][l])
                layout_rows[k].setStretchFactor(self.guess_boxes[k][l], 1)
            right_spacer = QLabel()
            layout_rows[k].addWidget(right_spacer)
            layout_rows[k].setStretchFactor(right_spacer, 2)
            qvb_layout.addItem(layout_rows[k])
        return qvb_layout

    def reset_guesses(self):
        for i in range(self.ge.num_rows):
            for j in range(self.ge.word_length):
                self.guess_boxes[i][j].setText('')
                self.guess_boxes[i][j].setStyleSheet(GUESS_BASIC_STYLESHEET)

    @staticmethod
    def create_result_box(p_letter:str):
        result_box = QLabel()
        result_box.setText(p_letter)
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

    def reset_results(self):
        for i in range(len(ORDERED_LETTERS)):
            self.result_boxes[i].setStyleSheet(RESULT_BASIC_STYLESHEET)

    # prevent input box from stealing focus when cursor over a button
    def eventFilter(self, obj, event):
        """Override eventFilter to catch QEvent.Type.Enter/Leave."""
        if obj == self.info_btn or obj == self.new_word_btn or obj == self.exit_btn:
            if event.type() == QEvent.Type.Enter:
                self.lgr.debug("Button hover.")
                self.button_hover = True
            if event.type() == QEvent.Type.Leave:
                self.lgr.debug("Button leave.")
                self.button_hover = False
        return super().eventFilter(obj, event)

    def create_button_section(self):
        """The instructions, exit and new game buttons of the UI."""
        self.info_btn = QPushButton("Instructions")
        self.info_btn.installEventFilter(self)
        self.info_btn.setStyleSheet(f"{MEDIUM_FONT} color: yellow; background: blue")
        self.info_btn.setAutoDefault(False)
        self.info_btn.setDefault(False)
        self.info_btn.clicked.connect(self.display_info)

        # TODO: add keystroke combination to start a new word
        self.new_word_btn = QPushButton("New Word?")
        self.new_word_btn.installEventFilter(self)
        self.new_word_btn.setStyleSheet(f"{MEDIUM_FONT} color: green; background: orange")
        self.new_word_btn.setAutoDefault(False)
        self.new_word_btn.setDefault(False)
        self.new_word_btn.clicked.connect(self.new_word_inquiry)

        self.exit_btn = QPushButton("Exit Game?")
        self.exit_btn.installEventFilter(self)
        self.exit_btn.setStyleSheet(f"{MEDIUM_FONT} color: red; background: yellow")
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.setDefault(False)
        self.exit_btn.clicked.connect(self.exit_inquiry)

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.info_btn)
        qhb_layout.addWidget(self.new_word_btn)
        qhb_layout.addWidget(self.exit_btn)
        return qhb_layout

    def response_change(self, resp:str):
        """Parse the current response and place the appropriate letters in the proper guess boxes."""
        if not self.active:
            return
        self.lgr.info(f"Response changed to '{resp}'; Input box text = {self.input_box.text()}")
        self.clear_guess_row(self.active_row)
        self.message_box.setText(f"Row {self.active_row+1} is active. Text = '{resp}'")
        if resp:
            self.current_guess = resp
            current_box = 0
            for letter in resp:
                self.guess_boxes[self.active_row][current_box].setText(letter)
                current_box += 1

    def process_response(self):
        """'Enter' key was pressed so check if the current response is a valid word then mark the guess and result boxes."""
        if not self.active:
            return
        entry = self.current_guess
        self.lgr.info(f">> Process response '{entry}'.")
        if not entry:
            return
        if self.ge.check_guess(entry):
            self.lgr.info(f"'{entry}' is a valid word.")
            self.mark_current_guess()
            self.active_row += 1
            self.current_guess = ''
            self.input_box.clear()
            if self.active and self.active_row == DEFAULT_NUM_ROWS:
                self.failure()
        else:
            self.lgr.info(f"'{entry}' is NOT a valid word.")
            self.message_box.setText(f"'{entry}' is NOT a valid word... :(")

    def clear_guess_row(self, row_num:int):
        for i in range(self.ge.word_length):
            self.guess_boxes[row_num][i].setText('')

    def mark_current_guess(self):
        # mark guess boxes
        guess = [ _ for _ in range(len(self.current_guess)) ]
        self.lgr.info(f"guess index list = {guess}.")
        targ = self.ge.current_target
        for i in range(self.ge.word_length):
            # EXACT match of letter position in guess and target
            if self.current_guess[i] == self.ge.current_target[i]:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_EXACT_STYLESHEET)
                guess.remove(i)
                idx = targ.index(self.ge.current_target[i])
                targ = targ[:idx] + targ[idx+1:]
                self.lgr.info(f"Exact[{i}] > guess = '{guess}'; targ = '{targ}'; current_target = '{self.ge.current_target}'")
            # guessed letter is ABSENT from target
            elif self.current_guess[i] not in self.ge.current_target:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_ABSENT_STYLESHEET)
                guess.remove(i)
                self.lgr.info(f"Absent[{i}] > guess = '{guess}' and targ = '{targ}'")
            else:
                self.lgr.info(f"No exact or absent at index[{i}]")
        self.lgr.info(f"guess = '{guess}' and targ = '{targ}'")
        # find target letters present in the guess but at a different position
        for j in guess:
            if self.current_guess[j] in targ:
                self.guess_boxes[self.active_row][j].setStyleSheet(GUESS_OCCUR_STYLESHEET)
                self.lgr.info(f"Index[{j}]: Mark occurrence of '{self.current_guess[j]}'")
                idx = targ.index(self.current_guess[j])
                targ = targ[:idx] + targ[idx+1:]
                self.lgr.info(f"Occurrence[{j}] > guess = '{guess}' and targ = '{targ}'")
            else:
                self.guess_boxes[self.active_row][j].setStyleSheet(GUESS_ABSENT_STYLESHEET)
        # mark result boxes
        for j in range(len(self.result_boxes)):
            check_letter = self.result_boxes[j].text()
            if check_letter in self.current_guess:
                if check_letter in self.ge.current_target:
                    self.result_boxes[j].setStyleSheet(RESULT_OCCUR_STYLESHEET)
                else:
                    self.result_boxes[j].setStyleSheet(RESULT_ABSENT_STYLESHEET)
        if self.current_guess == self.ge.current_target:
            self.victory()

    def victory(self):
        self.message_box.setText("Victory!")
        self.lgr.info("Victory!")
        self.active = False

    def failure(self):
        self.message_box.setText(f"Fail... :(  The secret word was '{self.ge.current_target}'.")
        self.lgr.info("Fail.")
        self.active = False

    def update_clock(self):
        """Update the game clock when the game is active."""
        log_pause = 600 if self.lock_count > 10 else 60
        locked = check_screen_locked(self.lgr) # pause when the screen is locked
        if not self.active or locked or self.isMinimized() or self.isHidden(): # pause when the game is inactive
            self.pause_secs += 1
            if self.pause_secs % log_pause == 0:
                self.lock_count += 1
                self.lgr.info(f"{self.pause_secs}: Screen is " + ("locked." if locked else "minimized or hidden."))
            return
        self.pause_secs = 0
        self.lock_count = 0
        self.run_secs += 1
        self.clock.setText("{:02}:{:02}:{:02}".format(self.run_secs // 3600, self.run_secs % 3600 // 60, self.run_secs % 3600 % 60))
        # make sure keyboard input gets to the input box
        if not self.button_hover:
            self.lgr.debug("set focus to input box")
            self.input_box.setFocus()

    def exit_inquiry(self):
        """Confirm that the user wants to exit the current game."""
        confirm_box, initiate_exit_button, continue_button = self.confirm_exit()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing the game.")
        elif confirm_box.clickedButton() == initiate_exit_button:
            self.lgr.info("Exiting.")
            self.close()

    def new_word_inquiry(self):
        """Confirm that the user wants a NEW secret word."""
        confirm_box, continue_button, new_game_button = self.confirm_new_game()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing the game.")
        elif confirm_box.clickedButton() == new_game_button:
            self.lgr.info("Starting over with a new word.")
            self.ge.save_record()
            # new game
            self.reset()

    @staticmethod
    def display_info():
        infobox = QMessageBox()
        infobox.setIcon(QMessageBox.Icon.Information)
        infobox.setStyleSheet(SMALL_FONT)
        infobox.setText(INFO_TEXT)
        infobox.setMinimumWidth(720) # DOES NOTHING... ?!
        infobox.exec()

    @staticmethod
    def confirm_exit():
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet("font-size: 16pt")
        confirm_box.setText("Are you SURE you want to EXIT the game?")
        cancel_button = confirm_box.addButton("No! >> Continue the game...", QMessageBox.ButtonRole.ActionRole)
        cancel_button.setStyleSheet("background: chartreuse")
        proceed_button = confirm_box.addButton("Yes >> EXIT the game.", QMessageBox.ButtonRole.ActionRole)
        proceed_button.setStyleSheet("color: yellow; background: purple")
        confirm_box.setDefaultButton(cancel_button)
        return confirm_box, proceed_button, cancel_button

    @staticmethod
    def confirm_new_game():
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet("font-size: 16pt")
        confirm_box.setText("Are you SURE you want to END this game and get a NEW word?")
        cancel_button = confirm_box.addButton("No! >> Continue with this word...", QMessageBox.ButtonRole.ActionRole)
        cancel_button.setStyleSheet("background: chartreuse")
        newgame_button = confirm_box.addButton("Yes >> Get a NEW word!", QMessageBox.ButtonRole.ActionRole)
        newgame_button.setStyleSheet("color: green; background: MediumVioletRed")
        confirm_box.setDefaultButton(cancel_button)
        return confirm_box, cancel_button, newgame_button
# END class WordleUI

# noinspection PyAttributeOutsideInit
class WordleGameEngine:
    """The Wordle game internal data and procedures."""
    def __init__(self, p_lgr:logging.Logger, p_len:int=5):
        self.lgr = p_lgr
        # TODO: check and use specified word length
        if p_len <= MAX_WORD_LENGTH:
            pass
        self.lgr.info(f"Initialized Game Engine >> total number of words = {len(all_words)}")
        self.word_length = MIN_WORD_LENGTH
        self.num_rows = DEFAULT_NUM_ROWS

    def start(self):
        self.previous_guess = ""
        self.num_guesses = 0
        self.good_guesses = []
        self.bad_guesses = []
        self.current_target = DEBUG_TARGET if WORDLE_DEBUG else all_words[random.randrange(0, len(all_words))]
        self.lgr.info(f"current target word = {self.current_target}")
        self.saved = False

    def check_guess(self, resp:str) -> bool:
        """Check for a good response."""
        self.lgr.debug(f"check response '{resp}':")
        if resp == self.current_target or resp in all_words:
            self.previous_guess = resp
            self.num_guesses += 1
            self.good_guesses.append(resp)
            return True
        self.bad_guesses.append(resp)
        return False

    def save_record(self):
        # save all important information from this game
        if not self.saved and self.good_guesses:
            game_record = {"TARGET WORD":self.current_target, "GOOD GUESSES":self.good_guesses, "BAD GUESSES":self.bad_guesses}
            grfile = save_to_json(f"WordleGameRecord_{self.current_target}", game_record)
            self.lgr.info(f"Saved game record as: {grfile}")
            self.saved = True
# END class WordleGameEngine


log_control = MhsLogger(WordleUI.__name__, con_level = DEFAULT_LOG_LEVEL)

if __name__ == "__main__":
    if len(argv) > 1:
        print(f"Usage: python3 {get_filename(argv[0])}\nLaunch the Wordle game.")
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
