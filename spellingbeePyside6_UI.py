##############################################################################################################################
# coding=utf-8
#
# spellingbee-pyside6-UI.py
#   -- launch the UI to play the SpellingBee game
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-08-18"
__updated__ = "2025-09-23"

from sys import argv
from PySide6 import QtCore
from PySide6.QtGui import Qt, QFont
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QGroupBox, QDialog, QLabel, QPushButton,
                               QMessageBox, QFormLayout, QTextEdit, QHBoxLayout, QFrame, QLineEdit)
from spellingbeeGameEngine import *

GUI_WIDTH  = 572
GUI_HEIGHT = 960
LETTERS_WIDTH = int(GUI_WIDTH / 11)
INFO_TEXT = (" How to Play the Game:\n"
             "------------------------------------------\n"
             "1) Enter a word (at least 4 letters) in the 'Try' box.\n\n"
             "2) Any number of each displayed letter is allowed, "
                 "but the Central letter MUST be present in the word.\n\n"
             "3) Press ENTER to evaluate your guess.\n\n"
             "4) FYI, most simple plurals are just ignored... \n\n"
             "5) You can press the space bar to scramble the placement of the outer letters.\n\n"
             "6) Your Valid or Invalid guesses are displayed in the appropriate boxes.\n\n"
             "7) Pangrams are words that use ALL seven letters (and earn DOUBLE points!)   :)\n\n"
             "8) Exit the game when you are ready and your game information will be saved.")

def display_info():
    infobox = QMessageBox()
    infobox.setIcon(QMessageBox.Icon.Information)
    infobox.setStyleSheet("font-size: 12pt")
    infobox.setText(INFO_TEXT)
    infobox.exec()
    return

def confirm_exit():
    confirm_box = QMessageBox()
    confirm_box.setIcon(QMessageBox.Icon.Question)
    confirm_box.setStyleSheet("font-size: 18pt")
    confirm_box.setText(" Are you SURE you want to EXIT the game? ")
    cancel_button = confirm_box.addButton(" Continue the game     :)", QMessageBox.ButtonRole.ActionRole)
    cancel_button.setStyleSheet("background-color: chartreuse")
    proceed_button = confirm_box.addButton(">> PROCEED to Exit!     :o", QMessageBox.ButtonRole.ActionRole)
    proceed_button.setStyleSheet("color: yellow; background-color: MediumVioletRed")
    confirm_box.setDefaultButton(cancel_button)
    return confirm_box, proceed_button, cancel_button

def centred_string(p:str):
    return (" " * ((LETTERS_WIDTH-len(p)) // 2)) + p

def set_letter_label_style(qlabel:QLabel):
    qlabel.setStyleSheet("font-weight: bold; color: blue; background: white; font-size: 32pt")
    qlabel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
    qlabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)


# noinspection PyAttributeOutsideInit
class SpellingBeeUI(QDialog):
    """UI to play the SpellingBee game."""
    def __init__(self):
        super().__init__()
        self.title = "SpellingBee UI"
        self.left = 240
        self.top  = 80
        self.width  = GUI_WIDTH
        self.height = GUI_HEIGHT
        self.ge = GameEngine()

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.title} runtime = {get_current_time()}")

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.ge.start_game()

        self.status_info = QLabel(centred_string(Level.Beginning.name + "  :)"))
        self.status_info.setStyleSheet("font-weight: bold; font-style: italic; font-size: 28pt; color: goldenrod; background: cyan")

        self.current_response = ""
        self.valid_responses = []
        self.pangram_responses = "Pangrams:"
        valid_label = QLabel("Valid responses:")
        valid_label.setStyleSheet("font-weight: bold; color: green")
        self.valid_response_box = QTextEdit()
        self.valid_response_box.setReadOnly(True)

        self.invalid_responses = []
        self.bad_letter_responses = "Bad/Missing letter:"
        invalid_label = QLabel("INVALID responses:")
        invalid_label.setStyleSheet("font-weight: bold; color: red")
        self.invalid_response_box = QTextEdit()
        self.invalid_response_box.setReadOnly(True)

        # buttons: instructions, exit
        info_btn = QPushButton("Game Instructions")
        info_btn.setStyleSheet("font-size: 24pt; color: yellow; background-color: blue")
        info_btn.setAutoDefault(False)
        info_btn.setDefault(False)
        info_btn.clicked.connect(display_info)
        exit_btn = QPushButton("Exit Game?")
        exit_btn.setStyleSheet("font-size: 24pt; font-weight: bold; color: red; background-color: yellow")
        exit_btn.setAutoDefault(False)
        exit_btn.setDefault(False)
        exit_btn.clicked.connect(self.exit_inquiry)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(info_btn, alignment = Qt.AlignmentFlag.AlignLeft)
        bottom_row.addWidget(exit_btn, alignment = Qt.AlignmentFlag.AlignRight)

        self.create_game_box()
        layout = QVBoxLayout()
        layout.addWidget(self.status_info)
        layout.addWidget(self.gb_main)
        layout.addWidget(valid_label)
        layout.addWidget(self.valid_response_box)
        layout.addWidget(invalid_label)
        layout.addWidget(self.invalid_response_box)
        layout.addLayout(bottom_row)
        self.setLayout(layout)

    def close(self, /):
        self.ge.end_game()
        super().close()

    def create_game_box(self):
        self.gb_main = QGroupBox()
        gb_layout = QFormLayout()

        self.response_box = QLineEdit()
        self.response_box.setFrame(True)
        self.response_box.setStyleSheet("font-style: italic; font-size: 24pt")
        self.response_box.setMaxLength(MAX_WORD_LENGTH)
        self.response_box.textEdited.connect(self.response_change)
        self.response_box.returnPressed.connect(self.process_response)
        gb_layout.addRow(QLabel("Try: "), self.response_box)

        self.message_box = QLineEdit()
        self.message_box.setFrame(True)
        self.message_box.setReadOnly(True)
        self.message_box.setStyleSheet("font-size: 14pt; font-family: italic; color:red")
        # ?? TIMER
        gb_layout.addRow(QLabel("Message: "),self.message_box)

        # number of points
        self.point_display = QLabel("000")
        self.point_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: green")
        pdivider = QLabel("/")
        pdivider.setStyleSheet("font-weight: bold; font-size: 20pt")
        ptotal_display = QLabel(str(self.ge.maximum_points))
        ptotal_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: purple")
        point_label = QLabel("   points")
        point_label.setStyleSheet("font-size: 18pt")
        pspacer = QLabel("      ")
        pspacer.setStyleSheet("font-weight: bold; font-size: 28pt")
        # word count
        self.count_display = QLabel("000")
        self.count_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: green")
        cdivider = QLabel("/")
        cdivider.setStyleSheet("font-weight: bold; font-size: 20pt")
        ctotal_display = QLabel(str(self.ge.total_num_answers))
        ctotal_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: purple")
        count_label = QLabel(" words")
        count_label.setStyleSheet("font-size: 18pt")
        # status button
        points_row = QHBoxLayout()
        points_row.addWidget(self.point_display)
        points_row.addWidget(pdivider)
        points_row.addWidget(ptotal_display)
        points_row.addWidget(point_label)
        points_row.addWidget(pspacer)
        points_row.addWidget(self.count_display)
        points_row.addWidget(cdivider)
        points_row.addWidget(ctotal_display)
        points_row.addWidget(count_label)
        gb_layout.addRow(points_row)

        ulspacer = QLabel("")
        ulspacer.setStyleSheet("font-weight: bold; font-size: 24pt")
        self.upper_left_letter = QLabel("UL")
        set_letter_label_style(self.upper_left_letter)
        self.upper_right_letter = QLabel("UR")
        set_letter_label_style(self.upper_right_letter)
        urspacer = QLabel("")
        urspacer.setStyleSheet("font-weight: bold; font-size: 24pt")
        top_row = QHBoxLayout()
        top_row.addWidget(ulspacer)
        top_row.addWidget(self.upper_left_letter)
        top_row.addWidget(self.upper_right_letter)
        top_row.addWidget(urspacer)
        top_row.setStretchFactor(ulspacer, 1)
        top_row.setStretchFactor(self.upper_left_letter, 2)
        top_row.setStretchFactor(self.upper_right_letter, 2)
        top_row.setStretchFactor(urspacer, 1)
        gb_layout.addRow(top_row)

        self.central_letter = QLabel("X")
        self.central_letter.setStyleSheet("font-weight: bold; color: purple; background: yellow; font-size: 32pt")
        self.central_letter.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.central_letter.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.central_left_letter = QLabel("CL")
        set_letter_label_style(self.central_left_letter)
        self.central_right_letter = QLabel("CR")
        set_letter_label_style(self.central_right_letter)
        middle_row = QHBoxLayout()
        middle_row.addWidget(self.central_left_letter)
        middle_row.addWidget(self.central_letter)
        middle_row.addWidget(self.central_right_letter)
        gb_layout.addRow(middle_row)

        llspacer = QLabel("")
        llspacer.setStyleSheet("font-weight: bold; font-size: 24pt")
        self.lower_left_letter = QLabel("LL")
        set_letter_label_style(self.lower_left_letter)
        self.lower_right_letter = QLabel("LR")
        set_letter_label_style(self.lower_right_letter)
        lrspacer = QLabel("")
        lrspacer.setStyleSheet("font-weight: bold; font-size: 24pt")
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(llspacer)
        bottom_row.addWidget(self.lower_left_letter)
        bottom_row.addWidget(self.lower_right_letter)
        bottom_row.addWidget(lrspacer)
        bottom_row.setStretchFactor(llspacer, 1)
        bottom_row.setStretchFactor(self.lower_left_letter, 2)
        bottom_row.setStretchFactor(self.lower_right_letter, 2)
        bottom_row.setStretchFactor(lrspacer, 1)
        gb_layout.addRow(bottom_row)

        self.gb_main.setLayout(gb_layout)
        self.populate_letter_boxes()

    def populate_letter_boxes(self):
        """Take the required letter and surround letters and enter into the proper widgets."""
        self.central_letter.setText(self.ge.required_letter)
        self.scramble_letters()

    def exit_inquiry(self):
        confirm_box, initiate_exit_button, continue_game_button = confirm_exit()
        confirm_box.exec()
        if confirm_box.clickedButton() == initiate_exit_button:
            self.lgr.info("Proceed to EXIT!")
            self.close()
        elif confirm_box.clickedButton() == continue_game_button:
            self.lgr.info("Continue the game...")

    def scramble_letters(self):
        """Change the placement of the surround letters."""
        self.lgr.info("scramble_letters()")
        picked = self.ge.surround_letters.copy()
        next_lett = picked[random.randrange(0,6)]
        self.upper_left_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,5)]
        self.upper_right_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,4)]
        self.central_left_letter.setText(next_lett)
        picked.remove(next_lett)
        next_lett = picked[random.randrange(0,3)]
        self.central_right_letter.setText(next_lett)
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
            self.message_box.setText("")
            self.current_response = self.ge.format_guess(resp)
            self.response_box.setText(self.current_response)

    def process_response(self):
        """'Enter' key was pressed so take the current response and check if it is a valid word."""
        entry = self.response_box.text()
        if entry and len(entry) >= MIN_WORD_LENGTH:
            self.lgr.info(f"Current response is: '{entry}'")
            # check if already tried
            if entry in self.ge.good_guesses or entry in self.ge.bad_word_guesses or entry in self.ge.bad_letter_guesses:
                self.message_box.setText(f" Already tried '{entry}' ;)")
                self.response_box.setText("")
                return
            # ignore if simple plural or past
            if self.ge.check_plurals(entry):
                plurals_msg = "Most simple PLURALS are IGNORED :("
                self.message_box.setText(plurals_msg)
                self.lgr.info(plurals_msg)
                self.response_box.setText("")
                return
            # check the word and enter into VALID or INVALID response box
            if self.ge.check_guess(entry):
                if entry in self.ge.pangram_guesses:
                    self.pangram_responses = f"{self.pangram_responses}   {entry}"
                    self.message_box.setText(f"Pangram! {self.ge.current_points} points.")
                else:
                    self.valid_responses.append(entry)
                    self.valid_responses.sort()
                    self.message_box.setText(f"{self.ge.current_points} point{"s" if len(entry) > MIN_WORD_LENGTH else ""}!")
                if self.pangram_responses:
                    # special font settings for Pangrams
                    regular_font_weight = self.valid_response_box.fontWeight()
                    self.lgr.debug(f"current font weight = {regular_font_weight}")
                    self.valid_response_box.setFontWeight(QFont.Weight.Bold)
                    self.valid_response_box.setFontItalic(True)
                    self.valid_response_box.setPlainText(self.pangram_responses)
                    self.valid_response_box.setFontWeight(regular_font_weight)
                    self.valid_response_box.setFontItalic(False)
                self.valid_response_box.append("Regular:")
                str_resp = (str(self.valid_responses)).replace(" ", "  ")
                self.lgr.debug(f"valid str_resp = <{str_resp}>")
                cleaned_text = str_resp.translate(cleaner)
                self.lgr.debug(f"valid cleaned_text = <{cleaned_text}>")
                self.valid_response_box.append(cleaned_text)
                self.lgr.debug(self.valid_response_box.toPlainText())
            else:
                if entry in self.ge.bad_letter_guesses:
                    self.bad_letter_responses = f"{self.bad_letter_responses}   {entry}"
                else:
                    self.invalid_responses.append(entry)
                    self.invalid_responses.sort()
                if self.bad_letter_responses:
                    # special font settings for bad/missing letters
                    regular_font_weight = self.invalid_response_box.fontWeight()
                    self.lgr.debug(f"current font weight = {regular_font_weight}")
                    self.invalid_response_box.setFontItalic(True)
                    self.invalid_response_box.setPlainText(self.bad_letter_responses)
                    self.invalid_response_box.setFontItalic(False)
                self.invalid_response_box.append("Other:")
                str_resp = (str(self.invalid_responses)).replace(" ", "  ")
                self.lgr.debug(f"invalid str_resp = <{str_resp}>")
                cleaned_text = str_resp.translate(cleaner)
                self.lgr.debug(f"invalid cleaned_text = <{cleaned_text}>")
                self.invalid_response_box.append(cleaned_text)
                self.lgr.debug(self.invalid_response_box.toPlainText())
                self.message_box.setText(" :(")
            # clear the current response
            self.response_box.setText("")
            # send a message if necessary
            # self.message_box.setText(" Pangram!" if entry in self.ge.pangram_guesses else "")
            if self.ge.required_letter not in entry:
                self.message_box.setText(" Missing Centre letter!")
            if self.ge.check_bad_letter(entry):
                self.message_box.setText(f" BAD letter '{self.ge.bad_letter}'!")
            # update points, count and level
            self.point_display.setText(str(self.ge.point_total))
            self.count_display.setText(str(self.ge.num_good_guesses))
            current_level = self.ge.get_current_level()
            if current_level[:4] != self.status_info.text().lstrip()[:4]:
                self.lgr.info(f"CHANGE level to '{current_level}'")
                self.status_info.setText(centred_string(current_level+'!'))

# END class SpellingBeeUI


if __name__ == "__main__":
    log_control = MhsLogger(SpellingBeeUI.__name__, con_level = DEFAULT_LOG_LEVEL)
    dialog = None
    app = None
    code = 0
    try:
        app = QApplication(argv)
        dialog = SpellingBeeUI()
        dialog.show()
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
        if dialog:
            dialog.close()
        if app:
            app.exit(code)
    exit(code)
