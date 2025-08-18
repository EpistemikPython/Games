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
__updated__ = "2025-08-18"

from PySide6 import QtCore
from PySide6.QtWidgets import (QApplication, QComboBox, QVBoxLayout, QGroupBox, QDialog, QLabel, QCheckBox,
                               QPushButton, QFormLayout, QDialogButtonBox, QTextEdit, QMessageBox, QHBoxLayout, QFrame)
from functools import partial
from spellingbeeGameEngine import *

UI_DEFAULT_LOG_LEVEL:int = logging.INFO

def set_label_style(qlabel:QLabel):
    qlabel.setStyleSheet("font-weight: bold; font-size: 36pt")
    qlabel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
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
        self.gnc_file = ""

        self._lgr = log_control.get_logger()
        self._lgr.log(UI_DEFAULT_LOG_LEVEL, f"{self.title} runtime = {get_current_time()}" )

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.selected_loglevel = UI_DEFAULT_LOG_LEVEL
        self.create_group_box()

        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.acceptRichText()
        self.response_box.setText("Hello there!")

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.gb_main)
        layout.addWidget(self.response_box)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def create_group_box(self):
        self.gb_main = QGroupBox("Parameters:")
        gb_layout = QFormLayout()

        self.cb_response_box = QComboBox()
        self.cb_response_box.setEditable(True)
        self.cb_response_box.setFrame(True)
        self.cb_response_box.setItemText(0,"Response")
        gb_layout.addRow(QLabel("Response: "), self.cb_response_box)

        self.upper_left_letter = QLabel("UL")
        set_label_style(self.upper_left_letter)
        self.upper_right_letter = QLabel("UR")
        set_label_style(self.upper_right_letter)
        top_row = QHBoxLayout()
        top_row.addWidget(self.upper_left_letter)
        top_row.addWidget(self.upper_right_letter)
        gb_layout.addRow(top_row)

        self.centre_letter = QLabel("!*!")
        set_label_style(self.centre_letter)
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

    # ? 'partial' always passes the index of the chosen label as an extra param...!
    def selection_change(self, cb:QComboBox, label:str, indx:int):
        self._lgr.debug(f"ComboBox '{label}' selection changed to: {cb.currentText()} [{indx}].")
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
