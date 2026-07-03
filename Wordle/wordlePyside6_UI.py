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
__updated__ = "2026-07-03"

import subprocess
from enum import IntEnum
from sys import argv
from PySide6.QtCore import Qt, QTimer
# from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout, QFrame,
                               QLabel, QPushButton, QMainWindow, QMessageBox)
from spellingbeeGameEngine import *

class SbFontSize(IntEnum):
    Xsmall  = 12
    Small   = 16
    SmMed   = 20
    Medium  = 24
    MedLarg = 28
    Large   = 32
    Xlarge  = 36


SMALL_FONT  = f"font-size: {SbFontSize.Small}pt;"
MEDIUM_FONT = f"font-size: {SbFontSize.Medium}pt;"
LARGE_FONT  = f"font-size: {SbFontSize.Large}pt;"
FONT_BOLD   = "font-weight: bold;"
FONT_ITALIC = "font-style: italic;"
PLURALS_MSG = "Most simple PLURALS are IGNORED  :p"
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
SBUI_DEBUG = False

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

def set_label_letter_style(qlabel:QLabel, font_size:int = SbFontSize.Large):
    qlabel.setStyleSheet(f"{FONT_BOLD} color: white; background: white; font-size: {font_size}pt")
    qlabel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
    qlabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

def set_label_bold(qlabel:QLabel, font_size:int = SbFontSize.Medium):
    qlabel.setStyleSheet(f"{FONT_BOLD} font-size: {font_size}pt")

def check_screen_locked(lgr:logging.Logger=None) -> bool:
    """See if a screensaver is active."""
    try:
        output = subprocess.check_output(["mate-screensaver-command", "-q"]).decode()
        if output:
            if lgr and SBUI_DEBUG:
                lgr.debug(f"Mate screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr:
            lgr.warning("Mate screensaver NOT found!")
    try:
        output = subprocess.check_output(["gnome-screensaver-command", "-q"]).decode()
        if output:
            if lgr and SBUI_DEBUG:
                lgr.debug(f"Gnome screensaver output: {output}")
            return "is active" in output
    except FileNotFoundError:
        if lgr and SBUI_DEBUG:
            lgr.warning("Gnome screensaver NOT found!")
    return False

class GuessRow(QHBoxLayout):
    """Row of 5 WordleBox to play the Wordle game."""
    def __init__(self):
        super().__init__()
        left_spacer = QLabel()
        self.addWidget(left_spacer)
        self.setStretchFactor(left_spacer, 2)
        self.letter_1 = GuessBox()
        self.addWidget(self.letter_1)
        self.setStretchFactor(self.letter_1, 1)
        self.letter_2 = GuessBox()
        self.addWidget(self.letter_2)
        self.setStretchFactor(self.letter_2, 1)
        self.letter_3 = GuessBox()
        self.addWidget(self.letter_3)
        self.setStretchFactor(self.letter_3, 1)
        self.letter_4 = GuessBox()
        self.addWidget(self.letter_4)
        self.setStretchFactor(self.letter_4, 1)
        self.letter_5 = GuessBox()
        self.addWidget(self.letter_5)
        self.setStretchFactor(self.letter_5, 1)
        right_spacer = QLabel()
        self.addWidget(right_spacer)
        self.setStretchFactor(right_spacer, 2)

class ResultRow(QHBoxLayout):
    """Row of 5 WordleBox to play the Wordle game."""
    def __init__(self, p_letters:str, p_size:int = 5):
        super().__init__()
        self.letter_1 = ResultBox(p_letters[0])
        self.addWidget(self.letter_1)
        self.letter_2 = ResultBox(p_letters[1])
        self.addWidget(self.letter_2)
        self.letter_3 = ResultBox(p_letters[2])
        self.addWidget(self.letter_3)
        self.letter_4 = ResultBox(p_letters[3])
        self.addWidget(self.letter_4)
        self.letter_5 = ResultBox(p_letters[4])
        self.addWidget(self.letter_5)
        if p_size > 5:
            self.letter_6 = ResultBox(p_letters[5])
            self.addWidget(self.letter_6)

class GuessBox(QLabel):
    """Box to contain a letter of the Wordle game."""
    def __init__(self):
        super().__init__()
        self.setText('?')
        set_label_letter_style(self)

class ResultBox(QLabel):
    """Box to contain a letter of the Wordle game."""
    def __init__(self, letter:str):
        super().__init__()
        self.setText(letter)
        # set_label_letter_style(self)
        self.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: black")

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
        main_layout.addLayout(self.create_game_section())
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
        self.clock.setText("00")
        self.valid_responses = []
        self.invalid_responses = []
        # game clock
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

    def close(self, /):
        self.ge.save_record()
        super().close()

    def create_game_section(self):
        """The game play section of the UI."""
        qf_layout = QFormLayout()
        # guess rows
        self.guess_section = QVBoxLayout()
        self.row_1 = GuessRow()
        self.guess_section.addLayout(self.row_1)
        self.row_2 = GuessRow()
        self.guess_section.addLayout(self.row_2)
        self.row_3 = GuessRow()
        self.guess_section.addLayout(self.row_3)
        self.row_4 = GuessRow()
        self.guess_section.addLayout(self.row_4)
        self.row_5 = GuessRow()
        self.guess_section.addLayout(self.row_5)
        self.row_6 = GuessRow()
        self.guess_section.addLayout(self.row_6)
        qf_layout.addItem(self.guess_section)
        return qf_layout

    def create_result_section(self):
        """The result section of the UI."""
        qvb_layout = QVBoxLayout()

        self.vowel_row = ResultRow("EAOIUY", 6)
        # self.E = ResultBox('E')
        # self.vowel_display.addWidget(self.E)
        # self.A = ResultBox('A')
        # self.vowel_display.addWidget(self.A)
        # self.O = ResultBox('O')
        # self.vowel_display.addWidget(self.O)
        # self.I = ResultBox('I')
        # self.vowel_display.addWidget(self.I)
        # self.U = ResultBox('U')
        # self.vowel_display.addWidget(self.U)
        # self.Y = ResultBox('Y')
        # self.vowel_display.addWidget(self.Y)

        # most common: SRLTN
        self.consonant_toprow = ResultRow("SRLTN")
        # self.S = ResultBox('S')
        # self.consonant_toprow.addWidget(self.S)
        # self.R = ResultBox('R')
        # self.consonant_toprow.addWidget(self.R)
        # self.L = ResultBox('L')
        # self.consonant_toprow.addWidget(self.L)
        # self.T = ResultBox('T')
        # self.consonant_toprow.addWidget(self.T)
        # self.N = ResultBox('N')
        # self.consonant_toprow.addWidget(self.N)

        # next: DCPMH
        self.consonant_midrow_1 = ResultRow("DCPMH")
        # self.D = ResultBox('D')
        # self.consonant_midrow1.addWidget(self.D)
        # self.C = ResultBox('C')
        # self.consonant_midrow1.addWidget(self.C)
        # self.P = ResultBox('P')
        # self.consonant_midrow1.addWidget(self.P)
        # self.M = ResultBox('M')
        # self.consonant_midrow1.addWidget(self.M)
        # self.H = ResultBox('H')
        # self.consonant_midrow1.addWidget(self.H)
        # self.consonant_display.addRow(self.consonant_midrow_1)

        # next: GBKWF
        self.consonant_midrow_2 = ResultRow("GBKWF")
        # self.G = ResultBox('G')
        # self.consonant_midrow2.addWidget(self.G)
        # self.B = ResultBox('B')
        # self.consonant_midrow2.addWidget(self.B)
        # self.K = ResultBox('K')
        # self.consonant_midrow2.addWidget(self.K)
        # self.W = ResultBox('W')
        # self.consonant_midrow2.addWidget(self.W)
        # self.F = ResultBox('F')
        # self.consonant_midrow2.addWidget(self.F)
        # self.consonant_display.addRow(self.consonant_midrow_2)

        # final: VZJXQ
        self.consonant_botrow = ResultRow("VZJXQ")
        # self.V = ResultBox('V')
        # self.consonant_botrow.addWidget(self.V)
        # self.Z = ResultBox('Z')
        # self.consonant_botrow.addWidget(self.Z)
        # self.J = ResultBox('J')
        # self.consonant_botrow.addWidget(self.J)
        # self.X = ResultBox('X')
        # self.consonant_botrow.addWidget(self.X)
        # self.Q = ResultBox('Q')
        # self.consonant_botrow.addWidget(self.Q)

        qvb_layout.addItem(self.vowel_row)
        qvb_layout.addItem(self.consonant_toprow)
        qvb_layout.addItem(self.consonant_midrow_1)
        qvb_layout.addItem(self.consonant_midrow_2)
        qvb_layout.addItem(self.consonant_botrow)

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
        cfont.setPointSize(SbFontSize.Medium)
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

    def update_clock(self):
        """Update the game clock when the game is active."""
        log_pause = 600 if self.lock_count > 10 else 60
        locked = check_screen_locked(self.lgr) # pause when the screen is locked
        if locked or self.isMinimized() or self.isHidden(): # pause when the game is inactive
            self.pause_secs += 1
            if self.pause_secs % log_pause == 0:
                self.lock_count += 1
                self.lgr.info(f"{self.pause_secs}: Screen is "+("locked." if locked else "minimized or hidden."))
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

    def response_change(self, resp:str):
        self.lgr.debug(f"Response changed to: '{resp}'")
        if resp:
            if resp[-1] == " ":
                pass
                # re-arrange the outer letters when space bar pressed
                # self.scramble_letters()
                # self.message_box.setText("Scramble!")
            self.current_response = get_clean_word(resp)
            # self.response_box.setText(self.current_response)

    def process_response(self):
        """'Enter' key was pressed so take the current response and check if it is a valid word."""
        entry = self.current_response
        if not entry or len(entry) < MIN_WORD_LENGTH:
            return
        self.lgr.debug(f"Current response is: '{entry}'")
        # check if already tried
        if entry in self.ge.good_guesses:
            message_text = f" Already have '{entry}'  ;)"
        elif entry in self.ge.bad_word_guesses or entry in self.ge.bad_letter_guesses:
            message_text = f" Already tried '{entry}'  :("
        # ignore if simple plural
        elif self.ge.check_plurals(entry):
            message_text = PLURALS_MSG
            self.lgr.debug(PLURALS_MSG)
        # have a GOOD response
        elif self.ge.check_guess(entry):
            if entry in self.ge.pangram_guesses:
                # self.pangram_responses = f"{self.pangram_responses}   {entry}"
                message_text = f"'{entry}' is a Pangram! {self.ge.current_points} points!"
            else:
                self.valid_responses.append(entry)
                self.valid_responses.sort()
                message_text = f"{entry} = {self.ge.current_points} point{"s" if len(entry) > MIN_WORD_LENGTH else ""}!"
            if self:
                pass
                # special font settings for Pangrams
            str_resp = (str(self.valid_responses)).replace(" ", "   ")
            self.lgr.debug(f"valid str_resp = <{str_resp}>")
            cleaned_text = str_resp.translate(cleaner)
            self.lgr.debug(f"valid cleaned_text = <{cleaned_text}>")
            # self.lgr.debug(self.valid_response_box.toPlainText())
            if self.ge.point_total == self.ge.maximum_points:
                # END THE GAME:
                # accept no more input
                # self.response_box.setReadOnly(True)
                # special colors
                # self.status_info.setStyleSheet(f"{FONT_BOLD} {FONT_ITALIC} font-size: {SbFontSize.MedLarg}pt; color: green; background: gold")
                # special message
                message_text = "VICTORY!"
        # have a BAD response
        else:
            # self.num_invalid_resp.setText(str(int(self.num_invalid_resp.text())+1))
            if entry in self.ge.bad_letter_guesses:
                self.bad_letter_responses = f"{entry}"
            else:
                self.invalid_responses.append(entry)
                self.invalid_responses.sort()
            if self.bad_letter_responses:
                # italic font for words MISSING THE CENTRAL LETTER or USING UNAVAILABLE LETTERS
                pass
                # self.invalid_response_box.setFontItalic(True)
                # self.invalid_response_box.setPlainText(self.bad_letter_responses)
                # self.invalid_response_box.setFontItalic(False)
            self.lgr.debug(f"previous font weight")
            # self.invalid_response_box.setFontWeight(QFont.Weight.Bold)
            # self.invalid_response_box.append("NOT words:")
            # self.invalid_response_box.setFontWeight(QFont.Weight.Normal)
            str_resp = (str(self.invalid_responses)).replace(" ", "   ")
            cleaned_text = str_resp.translate(cleaner)
            # self.invalid_response_box.append(cleaned_text)
            if SBUI_DEBUG:
                self.lgr.debug(f"invalid responses = <{str_resp}>\n\t\tinvalid responses cleaned text = <{cleaned_text}>"
                               f"\n\t\tinvalid responses to plain text = ")
            if self.ge.required_letter not in entry:
                message_text = f"'{entry}' is MISSING the Central letter!"
            elif self.ge.check_bad_letter(entry):
                message_text = f"'{entry}' uses UNAVAILABLE letter '{self.ge.bad_letter}'  :o"
            else:
                message_text = f"'{entry}' not accepted  :("
        # send a message
        self.lgr.info(message_text)
        # clear the current response
        # self.response_box.setText("")
        # update display of points, count and level
        # self.point_display.setText(str(self.ge.point_total))
        # self.num_valid_display.setText(str(self.ge.num_good_guesses))
        current_level = self.ge.get_current_level()
        if current_level[:4] != "hello":
            self.lgr.info(f"CHANGING level to '{current_level}'")
            # self.status_info.setText(current_level + '!')
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
