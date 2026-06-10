##############################################################################################################################
# coding=utf-8
#
# spellingbeePyside6_UI.py
#   -- the UI for the SpellingBee game
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-08-18"
__updated__ = "2026-06-08"

import subprocess
from enum import IntEnum
from sys import argv
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QGroupBox, QLabel, QPushButton, QMainWindow,
                               QMessageBox, QFormLayout, QTextEdit, QHBoxLayout, QFrame, QLineEdit, QWidget)
from spellingbeeGameEngine import *

class SbSize(IntEnum):
    Xsmall  = 12
    Small   = 16
    SmMed   = 20
    Medium  = 24
    MedLarg = 28
    Large   = 32
    Xlarge  = 36


SMALL_FONT  = f"font-size: {SbSize.Small}pt;"
MEDIUM_FONT = f"font-size: {SbSize.Medium}pt;"
LARGE_FONT  = f"font-size: {SbSize.Large}pt;"
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

def set_label_letter_style(qlabel:QLabel, font_size:int = SbSize.Large):
    qlabel.setStyleSheet(f"{FONT_BOLD} color: blue; background: white; font-size: {font_size}pt")
    qlabel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
    qlabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

def set_label_bold(qlabel:QLabel, font_size:int = SbSize.Medium):
    qlabel.setStyleSheet(f"{FONT_BOLD} font-size: {font_size}pt")

def screen_locked(lgr:logging.Logger=None) -> bool:
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


# noinspection PyAttributeOutsideInit
class SpellingBeeUI(QMainWindow):
    """UI to play the SpellingBee game."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My SpellingBee Game")
        # pixels: left, top, width, height
        self.setGeometry(500, 50, 640, 960)

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.windowTitle()} runtime = {get_current_time()}")

        self.ge = GameEngine(self.lgr)

        self.status_info = QLabel()
        self.status_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_info.setStyleSheet(f"{FONT_BOLD} {FONT_ITALIC} font-size: {SbSize.MedLarg}pt; color: goldenrod; background: cyan")

        self.pangram_responses = "Pangrams:"
        valid_label = QLabel("Valid responses:")
        valid_label.setStyleSheet(f"{FONT_BOLD} color: green")
        self.valid_response_box = QTextEdit()
        self.valid_response_box.setReadOnly(True)
        self.vrb_reg_font_weight = self.valid_response_box.fontWeight()
        self.lgr.debug(f"current valid response box font weight = {self.vrb_reg_font_weight}")

        self.bad_letter_responses = "Bad/Missing letter:"
        invalid_label = QLabel("INVALID responses:")
        invalid_label.setStyleSheet(f"{FONT_BOLD} color: red")
        self.num_invalid_resp = QLabel()
        self.num_invalid_resp.setStyleSheet(f"{SMALL_FONT} color: red")
        self.num_invalid_resp.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.num_invalid_resp.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        nir_space = QLabel()
        self.invalid_response_box = QTextEdit()
        self.invalid_response_box.setReadOnly(True)

        # buttons: instructions, timer, exit/new game
        info_btn = QPushButton("Game Instructions")
        info_btn.setStyleSheet(f"{MEDIUM_FONT} color: yellow; background: blue")
        info_btn.setAutoDefault(False)
        info_btn.setDefault(False)
        info_btn.clicked.connect(display_info)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.update_seconds = 1
        cfont = valid_label.font()
        cfont.setPointSize(SbSize.Medium)
        self.clock.setFont(cfont)
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(self.update_seconds * 1000) # update interval

        newgame_exit_btn = QPushButton("Exit Game?")
        newgame_exit_btn.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: red; background: yellow")
        newgame_exit_btn.setAutoDefault(False)
        newgame_exit_btn.setDefault(False)
        newgame_exit_btn.clicked.connect(self.exit_inquiry)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(info_btn)
        bottom_row.addWidget(self.clock)
        bottom_row.addWidget(newgame_exit_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.status_info)
        main_layout.addWidget(self.create_game_box())
        main_layout.addWidget(valid_label)
        main_layout.addWidget(self.valid_response_box)
        invalid_row = QHBoxLayout()
        invalid_row.addWidget(invalid_label)
        invalid_row.addWidget(self.num_invalid_resp)
        invalid_row.addWidget(nir_space)
        invalid_row.setStretchFactor(invalid_label, 1)
        invalid_row.setStretchFactor(self.num_invalid_resp, 1)
        invalid_row.setStretchFactor(nir_space, 4)
        main_layout.addLayout(invalid_row)
        main_layout.addWidget(self.invalid_response_box)
        main_layout.addLayout(bottom_row)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.reset()
        self.show()

    def reset(self):
        self.lgr.info("\n\nStarting a NEW Game!")
        self.ge.start()
        self.status_info.setText(PointLevel.Beginning.name + "  :)")
        self.clock.setText("00")
        self.valid_responses = []
        self.num_invalid_resp.setText("00")
        self.invalid_responses = []
        self.point_display.setText("000")
        self.ptotal_display.setText(str(self.ge.maximum_points))
        self.num_valid_display.setText("00")
        self.num_total_display.setText(str(self.ge.total_num_answers))
        self.response_box.setText("")
        self.message_box.setText("")
        self.valid_response_box.setText("")
        self.invalid_response_box.setText("")
        # place the target word letters
        self.central_letter.setText(self.ge.required_letter)
        self.scramble_letters()
        # game clock
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

    def close(self, /):
        self.ge.save_record()
        super().close()

    def create_game_box(self):
        grp_box = QGroupBox()
        gb_layout = QFormLayout()

        self.response_box = QLineEdit()
        self.response_box.setFrame(True)
        self.response_box.setStyleSheet(f"{FONT_ITALIC} {MEDIUM_FONT}")
        self.response_box.setMaxLength(MAX_WORD_LENGTH)
        self.response_box.textEdited.connect(self.response_change)
        self.response_box.returnPressed.connect(self.process_response)
        gb_layout.addRow(QLabel("Try: "), self.response_box)

        self.message_box = QLineEdit()
        self.message_box.setFrame(True)
        self.message_box.setReadOnly(True)
        self.message_box.setStyleSheet(f"{SMALL_FONT} color:red")
        gb_layout.addRow(QLabel("Message: "), self.message_box)

        # number of points
        self.point_display = QLabel()
        self.point_display.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: green")
        pdiv = QLabel("  /")
        set_label_bold(pdiv, SbSize.SmMed)
        self.ptotal_display = QLabel()
        self.ptotal_display.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: purple")
        point_label = QLabel(" points")
        point_label.setStyleSheet(f"font-size: {SbSize.SmMed}pt")
        pspacer = QLabel(" "*(self.width()//25))
        set_label_bold(pspacer, SbSize.MedLarg)
        # word count
        self.num_valid_display = QLabel()
        self.num_valid_display.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: green")
        cdiv = QLabel(" /")
        set_label_bold(cdiv, SbSize.SmMed)
        self.num_total_display = QLabel()
        self.num_total_display.setStyleSheet(f"{FONT_BOLD} {MEDIUM_FONT} color: purple")
        count_label = QLabel(" words")
        count_label.setStyleSheet(f"font-size: {SbSize.SmMed}pt")
        # status row
        points_row = QHBoxLayout()
        points_row.addWidget(self.point_display)
        points_row.addWidget(pdiv)
        points_row.addWidget(self.ptotal_display)
        points_row.addWidget(point_label)
        points_row.addWidget(pspacer)
        points_row.addWidget(self.num_valid_display)
        points_row.addWidget(cdiv)
        points_row.addWidget(self.num_total_display)
        points_row.addWidget(count_label)
        gb_layout.addRow(points_row)

        ulspacer = QLabel("")
        set_label_bold(ulspacer)
        self.upper_left_letter = QLabel("UL")
        set_label_letter_style(self.upper_left_letter)
        self.upper_right_letter = QLabel("UR")
        set_label_letter_style(self.upper_right_letter)
        urspacer = QLabel("")
        set_label_bold(urspacer)
        top_row = QHBoxLayout()
        top_row.addWidget(ulspacer)
        top_row.addWidget(self.upper_left_letter)
        top_row.addWidget(self.upper_right_letter)
        top_row.addWidget(urspacer)
        top_row.setStretchFactor(ulspacer, 3)
        top_row.setStretchFactor(self.upper_left_letter, 2)
        top_row.setStretchFactor(self.upper_right_letter, 2)
        top_row.setStretchFactor(urspacer, 3)
        gb_layout.addRow(top_row)

        clspacer = QLabel("")
        self.centre_left_letter = QLabel("CL")
        set_label_letter_style(self.centre_left_letter)
        self.central_letter = QLabel("X")
        self.central_letter.setStyleSheet(f"{FONT_BOLD} {LARGE_FONT} color: purple; background: yellow")
        self.central_letter.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.central_letter.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        crspacer = QLabel("")
        self.centre_right_letter = QLabel("CR")
        set_label_letter_style(self.centre_right_letter)
        middle_row = QHBoxLayout()
        middle_row.addWidget(clspacer)
        middle_row.addWidget(self.centre_left_letter)
        middle_row.addWidget(self.central_letter)
        middle_row.addWidget(self.centre_right_letter)
        middle_row.addWidget(crspacer)
        middle_row.setStretchFactor(clspacer, 2)
        middle_row.setStretchFactor(self.centre_left_letter, 2)
        middle_row.setStretchFactor(self.central_letter, 3)
        middle_row.setStretchFactor(self.centre_right_letter, 2)
        middle_row.setStretchFactor(crspacer, 2)
        gb_layout.addRow(middle_row)

        llspacer = QLabel("")
        set_label_bold(llspacer)
        self.lower_left_letter = QLabel("LL")
        set_label_letter_style(self.lower_left_letter)
        self.lower_right_letter = QLabel("LR")
        set_label_letter_style(self.lower_right_letter)
        lrspacer = QLabel("")
        set_label_bold(lrspacer)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(llspacer)
        bottom_row.addWidget(self.lower_left_letter)
        bottom_row.addWidget(self.lower_right_letter)
        bottom_row.addWidget(lrspacer)
        bottom_row.setStretchFactor(llspacer, 3)
        bottom_row.setStretchFactor(self.lower_left_letter, 2)
        bottom_row.setStretchFactor(self.lower_right_letter, 2)
        bottom_row.setStretchFactor(lrspacer, 3)
        gb_layout.addRow(bottom_row)

        grp_box.setLayout(gb_layout)
        return grp_box

    def update_clock(self):
        log_pause = 600 if self.lock_count > 10 else 60
        locked = screen_locked(self.lgr) # pause when the screen is locked
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

    def scramble_letters(self):
        """Change the placement of the surround letters."""
        self.lgr.debug("scramble_letters()")
        picked = self.ge.surround_letters.copy()
        next_lett = picked[random.randrange(0,6)]
        self.upper_left_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,5)]
        self.upper_right_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,4)]
        self.centre_left_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,3)]
        self.centre_right_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[0]
        self.lower_left_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[0]
        self.lower_right_letter.setText(next_lett)

    def response_change(self, resp:str):
        self.lgr.debug(f"Response changed to: '{resp}'")
        if resp:
            if resp[-1] == " ":
                # re-arrange the outer letters when space bar pressed
                self.scramble_letters()
                self.message_box.setText("Scramble!")
            self.current_response = get_clean_word(resp)
            self.response_box.setText(self.current_response)

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
                self.pangram_responses = f"{self.pangram_responses}   {entry}"
                message_text = f"'{entry}' is a Pangram! {self.ge.current_points} points!"
            else:
                self.valid_responses.append(entry)
                self.valid_responses.sort()
                message_text = f"{entry} = {self.ge.current_points} point{"s" if len(entry) > MIN_WORD_LENGTH else ""}!"
            if self.pangram_responses:
                # special font settings for Pangrams
                self.valid_response_box.setFontWeight(QFont.Weight.Bold)
                self.valid_response_box.setFontItalic(True)
                self.valid_response_box.setPlainText(self.pangram_responses)
                self.valid_response_box.setFontWeight(self.vrb_reg_font_weight)
                self.valid_response_box.setFontItalic(False)
            self.valid_response_box.setFontItalic(True)
            self.valid_response_box.append("Regular:")
            self.valid_response_box.setFontItalic(False)
            str_resp = (str(self.valid_responses)).replace(" ", "   ")
            self.lgr.debug(f"valid str_resp = <{str_resp}>")
            cleaned_text = str_resp.translate(cleaner)
            self.lgr.debug(f"valid cleaned_text = <{cleaned_text}>")
            self.valid_response_box.append(cleaned_text)
            self.lgr.debug(self.valid_response_box.toPlainText())
            if self.ge.point_total == self.ge.maximum_points:
                # END THE GAME:
                # accept no more input
                self.response_box.setReadOnly(True)
                # special colors
                self.status_info.setStyleSheet(f"{FONT_BOLD} {FONT_ITALIC} font-size: {SbSize.MedLarg}pt; color: green; background: gold")
                # special message
                message_text = "VICTORY!"
        # have a BAD response
        else:
            self.num_invalid_resp.setText(str(int(self.num_invalid_resp.text())+1))
            if entry in self.ge.bad_letter_guesses:
                self.bad_letter_responses = f"{self.bad_letter_responses}   {entry}"
            else:
                self.invalid_responses.append(entry)
                self.invalid_responses.sort()
            if self.bad_letter_responses:
                # italic font for words MISSING THE CENTRAL LETTER or USING UNAVAILABLE LETTERS
                self.invalid_response_box.setFontItalic(True)
                self.invalid_response_box.setPlainText(self.bad_letter_responses)
                self.invalid_response_box.setFontItalic(False)
            self.lgr.debug(f"previous font weight = {self.invalid_response_box.fontWeight()}")
            self.invalid_response_box.setFontWeight(QFont.Weight.Bold)
            self.invalid_response_box.append("NOT words:")
            self.invalid_response_box.setFontWeight(QFont.Weight.Normal)
            str_resp = (str(self.invalid_responses)).replace(" ", "   ")
            cleaned_text = str_resp.translate(cleaner)
            self.invalid_response_box.append(cleaned_text)
            if SBUI_DEBUG:
                self.lgr.debug(f"invalid responses = <{str_resp}>\n\t\tinvalid responses cleaned text = <{cleaned_text}>"
                               f"\n\t\tinvalid responses to plain text = {self.invalid_response_box.toPlainText()}")
            if self.ge.required_letter not in entry:
                message_text = f"'{entry}' is MISSING the Central letter!"
            elif self.ge.check_bad_letter(entry):
                message_text = f"'{entry}' uses UNAVAILABLE letter '{self.ge.bad_letter}'  :o"
            else:
                message_text = f"'{entry}' not accepted  :("
        # send a message
        self.message_box.setText(message_text)
        # clear the current response
        self.response_box.setText("")
        # update display of points, count and level
        self.point_display.setText(str(self.ge.point_total))
        self.num_valid_display.setText(str(self.ge.num_good_guesses))
        current_level = self.ge.get_current_level()
        if current_level[:4] != self.status_info.text().lstrip()[:4]:
            self.lgr.info(f"CHANGING level to '{current_level}'")
            self.status_info.setText(current_level + '!')
# END class SpellingBeeUI


log_control = MhsLogger(SpellingBeeUI.__name__, con_level = DEFAULT_LOG_LEVEL)

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
        dialog = SpellingBeeUI()
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
