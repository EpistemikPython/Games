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
__updated__ = "2026-07-14"

import subprocess
import random
from sys import argv, path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QMainWindow, QMessageBox, QLineEdit, QFrame, QComboBox)
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
path.append("/home/marksa/git/Python/Games/Wordle/input")
from all_wordle_words import all_wdl_words as all_words

# DEBUG_TARGET = "FELIS" # test words = MESSY, LEAFY, SILLY, AFFIX, SLIME, FLESH
DEBUG_TARGET = "PUPPY" # test words = APPLE, PAPER, PLUMP, TAUPE, UPPER, GUPPY
# DEBUG_TARGET = "GUPPY" # test words = PLUMP, PAPER, UPPER, UNDUE, PUPPY, BUGGY
WORDLE_DEBUG = False

ORDERED_LETTERS = "AEIOUYLNRSTCDHMPBFGKWJQVXZ"
MIN_WORD_LENGTH = 4
DEFAULT_WORD_LENGTH = 5
MAX_WORD_LENGTH = 13
MIN_NUM_ROWS = 3
DEFAULT_NUM_ROWS = 6
MAX_NUM_ROWS = 10

MEDIUM_FONT_SIZE = 16
SMALL_FONT  = "font-size: 12pt;"
MEDIUM_FONT = f"font-size: {MEDIUM_FONT_SIZE}pt;"
LARGE_FONT = "font-size: 24pt;"
XLARGE_FONT = "font-size: 36pt;"
FONT_BOLD   = "font-weight: bold;"
INPUT_COLOR = "gray" # "rgb(241, 241, 241)"

GUESS_BASIC_STYLESHEET  = f"{XLARGE_FONT}; color: blue;  background: white"
GUESS_EXACT_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: green; {FONT_BOLD}"
GUESS_OCCUR_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: yellow"
GUESS_ABSENT_STYLESHEET = f"{XLARGE_FONT}; color: white; background: gray"
RESULT_BASIC_STYLESHEET  = f"{FONT_BOLD} {LARGE_FONT} color: black"
RESULT_OCCUR_STYLESHEET  = f"{FONT_BOLD} {LARGE_FONT} color: green"
RESULT_ABSENT_STYLESHEET = f"{FONT_BOLD} {LARGE_FONT} color: red"
INPUTBOX_STYLESHEET = f"{SMALL_FONT} color: red; background: white" if WORDLE_DEBUG \
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
    def __init__(self, p_len:int=DEFAULT_WORD_LENGTH, p_rows:int=DEFAULT_NUM_ROWS):
        super().__init__()
        self.setWindowTitle("My Wordle Game")
        # pixels: dx from left, dy from top, width, height
        self.setGeometry(600, 100, 640, 760)

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.windowTitle()} start time = {get_current_time()}"
                                        f"\n\t\t\t\t\t\t >> p_len = {p_len}; p_rows = {p_rows}")

        self.ge = WordleGameEngine(self.lgr, p_len, p_rows)

        self.create_menu()
        self.container_widget = None
        self.main_layout = QVBoxLayout()
        self.reset()
        self.show()

    def reset(self):
        """Reset all the items needed to start a new game."""
        self.ge.save_word_record()
        self.lgr.info("Starting a NEW Game!")
        self.ge.start()
        self.active = True
        self.current_guess = ''
        self.active_row = 0
        self.button_hover = False
        # game clock
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

        # remove the old container widget from the main layout
        if self.container_widget:
            self.main_layout.removeWidget(self.container_widget)
            self.container_widget.deleteLater()
        # build a brand new container widget
        self.container_widget = QWidget()
        self.dynamic_layout = QVBoxLayout(self.container_widget)
        # add elements to the dynamic layout
        self.dynamic_layout.addLayout(self.create_top_section())
        self.input_box.clear()
        self.clock.setText("00")
        self.dynamic_layout.addLayout(self.create_guess_section())
        self.reset_guesses()
        self.dynamic_layout.addWidget(self.create_msg_box())
        self.dynamic_layout.addLayout(self.create_result_section())
        self.reset_results()
        self.dynamic_layout.addLayout(self.create_button_section())
        # attach the container back to the main layout
        self.main_layout.addWidget(self.container_widget)
        # set the central widget
        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)
        self.infobox.setText("Regular Mode")
        self.input_box.setFocus()

    def close(self, /):
        self.ge.save_word_record()
        super().close()

    def create_menu(self):
        menu_bar = self.menuBar()
        game_menu = menu_bar.addMenu("&Game")
        settings_menu = menu_bar.addMenu("&Settings")
        info_menu = menu_bar.addMenu("&Info")

        new_action = QAction("&New Word", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Start a new game with a NEW word")
        new_action.triggered.connect(self.new_word_inquiry)
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.setStatusTip("Quit the application")
        quit_action.triggered.connect(self.exit_inquiry)
        game_menu.addAction(new_action)
        game_menu.addSeparator()
        game_menu.addAction(quit_action)

        instr_action = QAction("&Instructions", self)
        instr_action.setShortcut("Ctrl+I")
        instr_action.setStatusTip("How to play Wordle")
        instr_action.triggered.connect(self.display_instructions)
        copyrite_action = QAction("Copy&right", self)
        copyrite_action.setShortcut("Ctrl+R")
        copyrite_action.setStatusTip("Display Copyright notice")
        copyrite_action.triggered.connect(self.copyrite)
        info_menu.addAction(instr_action)
        info_menu.addAction(copyrite_action)

        mode_action = QAction("Choose &Mode", self)
        mode_action.setShortcut("Ctrl+M")
        mode_action.setStatusTip("Choose STRICT or REGULAR mode")
        mode_action.triggered.connect(self.strict_mode_inquiry)
        settings_menu.addAction(mode_action)

        # to see status tips
        self.statusBar()

    def copyrite(self):
        QMessageBox.information(self, "Copyright", "Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>")

    def create_top_section(self):
        """Input, info box, combo boxes, clock section of the UI."""
        self.input_box = QLineEdit()
        self.input_box.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.input_box.setFrame(False)
        self.input_box.setReadOnly(False)
        # restrict acceptable input to WORD_LENGTH uppercase letters
        self.input_box.setInputMask(">" + "A"*self.ge.word_length)
        self.input_box.setStyleSheet(INPUTBOX_STYLESHEET)
        self.input_box.textEdited.connect(self.response_change)
        self.input_box.returnPressed.connect(self.process_response)

        self.infobox = QLabel()
        self.infobox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infobox.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.infobox.setStyleSheet(f"{MEDIUM_FONT} color:red")

        self.wordlen_combobox = QComboBox(self)
        self.wordlen_combobox.insertItems(0, [str(t) for t in range(MIN_WORD_LENGTH, MAX_WORD_LENGTH+1)])
        self.wordlen_combobox.setCurrentText(str(self.ge.word_length))
        self.wordlen_combobox.setFrame(True)
        self.wordlen_combobox.setEditable(False)
        self.wordlen_combobox.activated.connect(self.set_word_length)

        self.numrows_combobox = QComboBox(self)
        self.numrows_combobox.insertItems(0, [str(t) for t in range(MIN_NUM_ROWS, MAX_NUM_ROWS+1)])
        self.numrows_combobox.setCurrentText(str(self.ge.num_rows))
        self.numrows_combobox.setFrame(True)
        self.numrows_combobox.setEditable(False)
        self.numrows_combobox.activated.connect(self.set_num_rows)

        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_seconds = 1
        cfont = self.font()
        cfont.setPointSize(MEDIUM_FONT_SIZE)
        self.clock.setFont(cfont)
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(self.update_seconds * 1000) # update interval

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.input_box)
        qhb_layout.setStretchFactor(self.input_box, 6 if WORDLE_DEBUG else 1)
        qhb_layout.addWidget(self.infobox)
        qhb_layout.setStretchFactor(self.infobox, 4)
        qhb_layout.addWidget(QLabel("word length:"))
        qhb_layout.addWidget(self.wordlen_combobox)
        qhb_layout.setStretchFactor(self.wordlen_combobox, 2)
        qhb_layout.addWidget(QLabel("number of rows:"))
        qhb_layout.addWidget(self.numrows_combobox)
        qhb_layout.setStretchFactor(self.numrows_combobox, 2)
        right_spacer = QLabel()
        qhb_layout.addWidget(right_spacer)
        qhb_layout.setStretchFactor(right_spacer, 1)
        qhb_layout.addWidget(self.clock)
        qhb_layout.setStretchFactor(self.clock, 2)
        return qhb_layout

    def set_word_length(self):
        new_word_len = int(self.wordlen_combobox.currentText())
        self.lgr.info(f"Setting word length to {new_word_len}.")
        self.ge.word_length = new_word_len
        self.reset()

    def set_num_rows(self):
        new_num_rows = int(self.numrows_combobox.currentText())
        self.lgr.info(f"Setting number of rows to {new_num_rows}.")
        self.ge.num_rows = new_num_rows
        self.reset()

    def create_msg_box(self):
        self.msgbox = QLineEdit()
        self.msgbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msgbox.setFrame(True)
        self.msgbox.setReadOnly(True)
        self.msgbox.setStyleSheet(f"{MEDIUM_FONT} color:red")
        return self.msgbox

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
        self.guess_boxes = [[self.create_guess_box() for _ in range(row_len)] for _ in range(num_rows)]

        layout_rows = []
        for j in range(num_rows):
            self.lgr.debug(f"Setting guess row #{j}")
            layout_rows.append(QHBoxLayout())
            left_spacer = QLabel()
            layout_rows[j].addWidget(left_spacer)
            layout_rows[j].setStretchFactor(left_spacer, 2)
            for k in range(row_len):
                self.lgr.debug(f"Setting guess box #{j}-{k}")
                self.guess_boxes[j][k].setText('')
                layout_rows[j].addWidget(self.guess_boxes[j][k])
                layout_rows[j].setStretchFactor(self.guess_boxes[j][k], 1)
            right_spacer = QLabel()
            layout_rows[j].addWidget(right_spacer)
            layout_rows[j].setStretchFactor(right_spacer, 2)
            qvb_layout.addItem(layout_rows[j])
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
        self.lgr.debug(f"Have {len(self.result_boxes)} result boxes.")

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
        self.info_btn.clicked.connect(self.display_instructions)

        self.new_word_btn = QPushButton("New Word?")
        self.new_word_btn.installEventFilter(self)
        self.new_word_btn.setStyleSheet(f"{MEDIUM_FONT} color: green; background: orange")
        self.new_word_btn.setAutoDefault(False)
        self.new_word_btn.setDefault(False)
        self.new_word_btn.clicked.connect(self.new_word_inquiry)

        self.exit_btn = QPushButton("Quit App?")
        self.exit_btn.installEventFilter(self)
        self.exit_btn.setStyleSheet(f"{MEDIUM_FONT} color: red; background: yellow")
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.setDefault(False)
        self.exit_btn.clicked.connect(self.exit_inquiry)

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.info_btn)
        qhb_layout.addWidget(self.new_word_btn)
        qhb_layout.addWidget(self.exit_btn)
        qvb_layout = QVBoxLayout()
        qvb_layout.addWidget(QLabel("\t\t\t\t"))
        qvb_layout.addLayout(qhb_layout)
        return qvb_layout

    def response_change(self, resp:str):
        """Parse the current response and place the appropriate letters in the proper guess boxes."""
        if not self.active:
            return
        self.lgr.info(f"Response changed to '{resp}'; Input box text = {self.input_box.text()}")
        self.clear_guess_row(self.active_row)
        self.msgbox.setText(f"Row {self.active_row+1} is active. Text = '{resp}'")
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
        if self.ge.check_guess(entry, self.active_row):
            self.lgr.info(f"'{entry}' is a valid word.")
            self.mark_current_guess()
            self.active_row += 1
            self.current_guess = ''
            self.input_box.clear()
            if self.active and self.active_row == self.ge.num_rows:
                self.failure()
        else:
            mesg = self.ge.info_mesg if self.ge.info_mesg else f"'{entry}' is NOT a valid word... :("
            self.lgr.info(mesg)
            self.msgbox.setText(mesg)
        self.ge.info_mesg = ""

    def clear_guess_row(self, row_num:int):
        for i in range(self.ge.word_length):
            self.guess_boxes[row_num][i].setText('')

    def mark_current_guess(self):
        """Mark the current guess boxes as green, yellow or grey & the result letters as green or red."""
        # mark guess boxes
        guess_idx = [ _ for _ in range(len(self.current_guess)) ]
        self.lgr.info(f"guess index list = {guess_idx}.")
        targ = self.ge.current_target
        for i in range(self.ge.word_length):
            # EXACT match of letter position in guess and target
            if self.current_guess[i] == self.ge.current_target[i]:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_EXACT_STYLESHEET)
                guess_idx.remove(i)
                if i not in self.ge.green_index:
                    self.ge.green_index.append(i)
                    self.ge.green_index.sort()
                    self.lgr.info(f"self.ge.green_index = {self.ge.green_index}")
                idx = targ.index(self.ge.current_target[i])
                targ = targ[:idx] + targ[idx+1:]
                self.lgr.info(f"Exact[{i}] > guess = '{guess_idx}'; targ = '{targ}'; current_target = '{self.ge.current_target}'")
            # guessed letter is ABSENT from target
            elif self.current_guess[i] not in self.ge.current_target:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_ABSENT_STYLESHEET)
                guess_idx.remove(i)
                self.lgr.info(f"Absent[{i}] > guess = '{guess_idx}' and targ = '{targ}'")
            else:
                self.lgr.info(f"No exact or absent at index[{i}]")
        self.lgr.info(f"guess = '{guess_idx}' and targ = '{targ}'")
        # find target letters present in the guess but at a different position
        for j in guess_idx:
            if self.current_guess[j] in targ:
                self.guess_boxes[self.active_row][j].setStyleSheet(GUESS_OCCUR_STYLESHEET)
                self.lgr.info(f"Index[{j}]: Mark occurrence of '{self.current_guess[j]}'")
                if self.current_guess[j] not in self.ge.yellow_list:
                    self.ge.yellow_list.append(self.current_guess[j])
                    self.lgr.info(f"self.ge.yellow_list = {self.ge.yellow_list}")
                idx = targ.index(self.current_guess[j])
                targ = targ[:idx] + targ[idx+1:]
                self.lgr.info(f"Occurrence[{j}] > guess = '{guess_idx}' and targ = '{targ}'")
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
        self.msgbox.setText("Victory!")
        self.infobox.setText("Victory :)")
        self.lgr.info("Victory!\n\n\n======================================\n")
        self.active = False

    def failure(self):
        self.msgbox.setText(f"Fail... :(  The secret word was '{self.ge.current_target}'.")
        self.infobox.setText("Failure :(")
        self.lgr.info("Failure.\n\n\n======================================\n")
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

    def strict_mode_inquiry(self):
        """Ask if the user wants to set strict or regular mode."""
        confirm_box, strict_button, regular_button = self.confirm_mode()
        confirm_box.exec()
        if confirm_box.clickedButton() == strict_button:
            self.ge.strict_mode = True
            self.infobox.setText("Strict Mode")
            self.lgr.info("SET strict mode.")
        elif confirm_box.clickedButton() == regular_button:
            self.ge.strict_mode = False
            self.infobox.setText("Regular Mode")
            self.lgr.info("SET regular mode.")

    def exit_inquiry(self):
        """Ask if the user wants to exit the app."""
        confirm_box, continue_button, quit_button = self.confirm_exit()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing the game.")
        elif confirm_box.clickedButton() == quit_button:
            self.lgr.info("Quit the app.")
            self.close()

    def new_word_inquiry(self):
        """Ask if the user wants a NEW secret word."""
        confirm_box, continue_button, new_word_button = self.confirm_new_word()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing this game.")
        elif confirm_box.clickedButton() == new_word_button:
            self.lgr.info("Starting over with a new word.")
            self.reset()

    def display_instructions(self):
        """Display 'How to play Wordle'."""
        infobox = QMessageBox()
        infobox.setIcon(QMessageBox.Icon.Information)
        infobox.setStyleSheet(SMALL_FONT)
        infobox.setText(self.ge.instructions)
        infobox.setMinimumWidth(720) # DOES NOTHING... ?!
        infobox.exec()

    @staticmethod
    def confirm_mode():
        """Check if the user wants to use strict or regular mode."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("In 'strict' mode any previous green or yellow letter guesses MUST be used in subsequent guesses.")
        strict_button = confirm_box.addButton("Set STRICT mode.", QMessageBox.ButtonRole.ActionRole)
        strict_button.setStyleSheet("background: violet")
        regular_button = confirm_box.addButton("Set REGULAR mode.", QMessageBox.ButtonRole.ActionRole)
        regular_button.setStyleSheet("background: yellow")
        confirm_box.setDefaultButton(regular_button)
        return confirm_box, strict_button, regular_button

    @staticmethod
    def confirm_exit():
        """Confirm that the user wants to exit the app."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("Are you SURE you want to QUIT the app?")
        continue_button = confirm_box.addButton("No! >> Continue this game...", QMessageBox.ButtonRole.ActionRole)
        continue_button.setStyleSheet("background: chartreuse")
        quit_button = confirm_box.addButton("Yes >> QUIT the app.", QMessageBox.ButtonRole.ActionRole)
        quit_button.setStyleSheet("color: yellow; background: purple")
        confirm_box.setDefaultButton(continue_button)
        return confirm_box, continue_button, quit_button

    @staticmethod
    def confirm_new_word():
        """Confirm that the user wants a NEW secret word."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("Are you SURE you want to END this game and get a NEW word?")
        continue_button = confirm_box.addButton("No! >> Continue with this word...", QMessageBox.ButtonRole.ActionRole)
        continue_button.setStyleSheet("background: chartreuse")
        new_word_button = confirm_box.addButton("Yes >> Get a NEW word!", QMessageBox.ButtonRole.ActionRole)
        new_word_button.setStyleSheet("color: green; background: MediumVioletRed")
        confirm_box.setDefaultButton(continue_button)
        return confirm_box, continue_button, new_word_button
# END class WordleUI

# noinspection PyAttributeOutsideInit
class WordleGameEngine:
    """The Wordle game internal data and procedures."""
    def __init__(self, p_lgr:logging.Logger, p_len:int=DEFAULT_WORD_LENGTH, p_rows:int=DEFAULT_NUM_ROWS):
        self.lgr = p_lgr
        # TODO: set different lengths and number of rows from main.py
        if MIN_WORD_LENGTH <= p_len <= MAX_WORD_LENGTH:
            self.word_length = p_len
        if MIN_NUM_ROWS <= p_rows <= MAX_NUM_ROWS:
            self.num_rows = p_rows
        self.instructions = ("\tHow to Play Wordle:\n"
                        "---------------------------------------------------------------------------------\n"
                        f"1) Try to guess the secret {self.word_length}-letter word.\n\n"
                        f"2) Type a {self.word_length}-letter word and press ENTER to evaluate it. "
                        f" Your entry will be accepted if it is a VALID Wordle word.\n\n"
                        "3) A letter in the correct position will shade GREEN.\n\n"
                        "4) A letter present in the secret word but in the wrong position in your guess will shade YELLOW.\n\n"
                        "5) A letter NOT present in the secret word will shade GREY.\n\n"
                        "6) In STRICT mode any 'green' and 'yellow' letters found in a guess MUST be used in subsequent guesses.\n\n"
                        f"7) You have {self.num_rows} attempts to find the secret word.\n\n"
                        "8) If you Quit the app (Ctrl-Q) or start a New word (Ctrl-N) your current game results will be saved to a file.")
        self.good_guesses = None
        self.lgr.info(f"Initialized Game Engine >> Word length = {self.word_length}; Number of rows = {self.num_rows}.")

    def start(self):
        self.previous_guess = ""
        self.num_guesses = 0
        self.good_guesses = []
        self.bad_guesses = []
        self.green_index = []
        self.yellow_list = []
        self.info_mesg = ""
        self.strict_mode = False
        self.saved = False
        self.get_current_words()
        self.current_target = DEBUG_TARGET if WORDLE_DEBUG else self.current_words[random.randrange(0, len(self.current_words))]
        self.lgr.info(f"current target word = {self.current_target}; total number of words = {len(self.current_words)}")

    def get_current_words(self):
        """Get all words that match the current word length."""
        self.current_words = []
        for wd in all_words:
            if len(wd) == self.word_length:
                self.current_words.append(wd)

    def check_guess(self, resp:str, p_current_row:int) -> bool:
        """Check for a valid response."""
        self.lgr.debug(f"check response '{resp}'.")
        if resp == self.current_target:
            result = True
        elif resp not in self.current_words:
            result = False
        elif p_current_row > 0 and self.strict_mode:
            result = self.checkguess_strict_mode(resp)
        else:
            result = True
        if result:
            self.previous_guess = resp
            self.num_guesses += 1
            self.good_guesses.append(resp)
            return True
        else:
            self.bad_guesses.append(resp)
            return False

    def checkguess_strict_mode(self, resp:str) -> bool:
        """Make sure that previous green and yellow responses are carried over."""
        self.lgr.debug(f"check response '{resp}' in STRICT mode.")
        for gi in self.green_index:
            if resp[gi] != self.current_target[gi]:
                self.info_mesg = f"Missing green letter at position {gi+1} in '{resp}'."
                return False
        for yl in self.yellow_list:
            if yl not in resp:
                self.info_mesg = f"Missing yellow letter '{yl}'."
                return False
        return True

    def save_word_record(self):
        # save all important information from this game
        if self.good_guesses and not self.saved:
            game_record = {"TARGET WORD":self.current_target, "GOOD GUESSES":self.good_guesses, "BAD GUESSES":self.bad_guesses}
            grfile = save_to_json(f"WordleGameRecord_{self.current_target}", game_record)
            self.saved = True
            self.lgr.info(f"Saved game record as: {grfile}")
# END class WordleGameEngine


log_control = MhsLogger(WordleUI.__name__, con_level = DEFAULT_LOG_LEVEL)

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
