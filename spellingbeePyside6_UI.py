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
__updated__ = "2025-09-09"

from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QGroupBox, QDialog, QLabel, QFormLayout,
                               QTextEdit, QHBoxLayout, QFrame, QLineEdit)
import spellingbeeGameEngine
from spellingbeeGameEngine import *

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
        self.left = 320
        self.top  = 120
        self.width  = 520
        self.height = 800
        self.ge = spellingbeeGameEngine.GameEngine()

        self._lgr = log_control.get_logger()
        self._lgr.log(DEFAULT_LOG_LEVEL, f"{self.title} runtime = {get_current_time()}" )

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.selected_loglevel = DEFAULT_LOG_LEVEL
        self.create_group_box()

        self.current_response = ""
        valid_label = QLabel("Valid responses:")
        valid_label.setStyleSheet("font-weight: bold; color: green")
        self.valid_response_box = QTextEdit()
        self.valid_response_box.setReadOnly(True)
        self.valid_response_box.acceptRichText()

        invalid_label = QLabel("INVALID responses:")
        invalid_label.setStyleSheet("font-weight: bold; color: red")
        self.invalid_response_box = QTextEdit()
        self.invalid_response_box.setReadOnly(True)
        self.invalid_response_box.acceptRichText()

        layout = QVBoxLayout()
        layout.addWidget(self.gb_main)
        layout.addWidget(valid_label)
        layout.addWidget(self.valid_response_box)
        layout.addWidget(invalid_label)
        layout.addWidget(self.invalid_response_box)
        self.setLayout(layout)

        self.ge.start_game()
        self.populate_letter_boxes()

    def create_group_box(self):
        self.gb_main = QGroupBox("SpellingBee!")
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
        self.message_box.setStyleSheet("font-size: 24pt")
        gb_layout.addRow(QLabel("Message: "),self.message_box)

        self.point_display = QLabel("000")
        self.point_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: green")
        self.divider = QLabel("/")
        self.divider.setStyleSheet("font-weight: bold; font-size: 28pt")
        self.total_display = QLabel("1000")
        self.total_display.setStyleSheet("font-weight: bold; font-size: 24pt; color: red")
        self.point_label = QLabel("  points                      ")
        self.point_label.setStyleSheet("font-size: 28pt")
        points_row = QHBoxLayout()
        points_row.addWidget(self.point_display)
        points_row.addWidget(self.divider)
        points_row.addWidget(self.total_display)
        points_row.addWidget(self.point_label)
        gb_layout.addRow(points_row)

        self.upper_left_letter = QLabel("U")
        set_letter_label_style(self.upper_left_letter)
        self.upper_right_letter = QLabel("R")
        set_letter_label_style(self.upper_right_letter)
        top_row = QHBoxLayout()
        top_row.addWidget(self.upper_left_letter)
        top_row.addWidget(self.upper_right_letter)
        gb_layout.addRow(top_row)

        self.central_letter = QLabel("X")
        self.central_letter.setStyleSheet("font-weight: bold; color: purple; background: yellow; font-size: 42pt")
        self.central_letter.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.central_letter.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.central_left_letter = QLabel("L")
        set_letter_label_style(self.central_left_letter)
        self.central_right_letter = QLabel("M")
        set_letter_label_style(self.central_right_letter)
        middle_row = QHBoxLayout()
        middle_row.addWidget(self.central_left_letter)
        middle_row.addWidget(self.central_letter)
        middle_row.addWidget(self.central_right_letter)
        gb_layout.addRow(middle_row)

        self.lower_left_letter = QLabel("D")
        set_letter_label_style(self.lower_left_letter)
        self.lower_right_letter = QLabel("A")
        set_letter_label_style(self.lower_right_letter)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.lower_left_letter)
        bottom_row.addWidget(self.lower_right_letter)
        gb_layout.addRow(bottom_row)

        self.gb_main.setLayout(gb_layout)

    def populate_letter_boxes(self):
        """Take the required letter and surround letters and enter into the proper widgets."""
        self.central_letter.setText(self.ge.required_letter)
        self.scramble_letters()

    def scramble_letters(self):
        """Change the placement of the surround letters."""
        self._lgr.info("scramble_letters()")
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
        self._lgr.info(f"Response changed to: '{resp}'")
        if resp:
            if resp[-1] == " ":
                # re-arrange the outer letters when space bar pressed
                self.scramble_letters()
            self.message_box.setText("")
            self.current_response = self.ge.format_response(resp)
            self.response_box.setText(self.current_response)

    def process_response(self):
        """'Enter' key was pressed so take the current response and check if it is a valid word."""
        entry = self.response_box.text()
        if entry and len(entry) >= MIN_WORD_LENGTH:
            self._lgr.info(f"Current response is: '{entry}'")
            # check the word and enter into valid or invalid response box
            if entry in self.ge.good_guesses or entry in self.ge.bad_guesses:
                self.message_box.setText("Already tried :(")
                self.response_box.setText("")
                return
            if self.ge.check_response(entry):
                if entry in self.ge.pangram_guesses:
                    regular_font_weight = self.valid_response_box.fontWeight()
                    self._lgr.info(f"current font weight = {regular_font_weight}")
                    self.valid_response_box.setFontWeight(700)
                    self.valid_response_box.setFontItalic(True)
                    self.valid_response_box.append(entry)
                    self.valid_response_box.setFontWeight(regular_font_weight)
                    self.valid_response_box.setFontItalic(False)
                else:
                    self.valid_response_box.append(entry)
            else:
                self.invalid_response_box.append(entry)
            self.response_box.setText("")
            self.message_box.setText("Pangram!" if entry in self.ge.pangram_guesses else "")
            self.point_display.setText(str(self.ge.point_total))

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
