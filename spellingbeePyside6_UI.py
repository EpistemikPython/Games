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
__updated__ = "2025-08-19"

from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QVBoxLayout, QGroupBox, QDialog, QLabel, QFormLayout,
                               QTextEdit, QHBoxLayout, QFrame, QLineEdit)
from spellingbeeGameEngine import *

UI_DEFAULT_LOG_LEVEL:int = logging.INFO

def set_label_style(qlabel:QLabel):
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
        self.width  = 480
        self.height = 800

        self._lgr = log_control.get_logger()
        self._lgr.log(UI_DEFAULT_LOG_LEVEL, f"{self.title} runtime = {get_current_time()}" )

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.selected_loglevel = UI_DEFAULT_LOG_LEVEL
        self.create_group_box()

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
        # self.invalid_response_box.setText(" responses:")

        # button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        # button_box.accepted.connect(self.accept)
        # button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.gb_main)
        layout.addWidget(valid_label)
        layout.addWidget(self.valid_response_box)
        layout.addWidget(invalid_label)
        layout.addWidget(self.invalid_response_box)
        # layout.addWidget(button_box)
        self.setLayout(layout)

    def create_group_box(self):
        self.gb_main = QGroupBox("SpellingBee!")
        gb_layout = QFormLayout()

        self.le_response_box = QLineEdit()
        self.le_response_box.setFrame(True)
        self.le_response_box.setStyleSheet("font-style: italic; font-size: 24pt")
        self.le_response_box.setInputMask(">AAAAAAA")
        self.le_response_box.setMaxLength(7)
        self.le_response_box.textEdited.connect(self.response_change)
        self.le_response_box.returnPressed.connect(self.accept_response)
        gb_layout.addRow(QLabel("Try: "), self.le_response_box)

        self.le_message_box = QLineEdit()
        self.le_message_box.setFrame(True)
        self.le_message_box.setReadOnly(True)
        self.le_message_box.setStyleSheet("font-size: 24pt")
        gb_layout.addRow(QLabel("Message: "), self.le_message_box)

        self.upper_left_letter = QLabel("UL")
        set_label_style(self.upper_left_letter)
        self.upper_right_letter = QLabel("UR")
        set_label_style(self.upper_right_letter)
        top_row = QHBoxLayout()
        top_row.addWidget(self.upper_left_letter)
        top_row.addWidget(self.upper_right_letter)
        gb_layout.addRow(top_row)

        self.centre_letter = QLabel("X")
        self.centre_letter.setStyleSheet("font-weight: bold; color: purple; background: yellow; font-size: 42pt")
        self.centre_letter.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.centre_letter.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.central_left_letter = QLabel("CL")
        set_label_style(self.central_left_letter)
        self.central_right_letter = QLabel("CR")
        set_label_style(self.central_right_letter)
        middle_row = QHBoxLayout()
        middle_row.addWidget(self.central_left_letter)
        middle_row.addWidget(self.centre_letter)
        middle_row.addWidget(self.central_right_letter)
        gb_layout.addRow(middle_row)

        self.lower_left_letter = QLabel("LL")
        set_label_style(self.lower_left_letter)
        self.lower_right_letter = QLabel("LR")
        set_label_style(self.lower_right_letter)
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.lower_left_letter)
        bottom_row.addWidget(self.lower_right_letter)
        gb_layout.addRow(bottom_row)

        self.gb_main.setLayout(gb_layout)

    def response_change(self, resp:str):
        self._lgr.info(f"Response changed to: '{resp}'")

    def accept_response(self):
        self._lgr.info(f"Current response is: '{self.le_response_box.text()}'")

# END class SpellingBeeUI


if __name__ == "__main__":
    log_control = MhsLogger(SpellingBeeUI.__name__, con_level = UI_DEFAULT_LOG_LEVEL)
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
