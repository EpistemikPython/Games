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
__updated__ = "2026-08-25"

import random
from sys import argv, path
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QAction, QColor, QMouseEvent
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QMainWindow, QMessageBox, QLineEdit, QFrame, QComboBox)
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
path.append("/home/marksa/git/Python/Games/input")
from all_words import all_game_words

WORDLE_DEBUG = 0
# DEBUG_TARGET = "FELIS" # test words = MESSY, LEAFY, SILLY, AFFIX, SLIME, FLESH; Strict = LEAST, FELLA
# DEBUG_TARGET = "PUPPY" # test words = APPLE, PAPER, PLUMP, TAUPE, UPPER, GUPPY; Strict = POPPY, PEPPY
# DEBUG_TARGET = "GUPPY" # test words = PLUMP, PAPER, UPPER, UNDUE, PUPPY, BUGGY
# DEBUG_TARGET = "GENERA" # SAILOR TRACED MANURE BARREN RENEGE VENEER; Strict = REAMED, TEARED, MEANER
DEBUG_TARGET = "ECZEMA" # SAILOR TEAMED MEANER ERMINE ENAMEL EMPATH

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
INPUT_COLOR = "linen" # "rgb(241, 241, 241)"

BOX_FRAME_STYLE = QFrame.Shape.Box | QFrame.Shadow.Raised
GUESS_BASIC_STYLESHEET  = f"{XLARGE_FONT}; color: blue;  background: white"
GUESS_EXACT_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: green; {FONT_BOLD}"
GUESS_OCCUR_STYLESHEET  = f"{XLARGE_FONT}; color: black; background: yellow"
GUESS_ABSENT_STYLESHEET = f"{XLARGE_FONT}; color: white; background: gray"
RESULT_BASIC_STYLESHEET  = f"{FONT_BOLD} {LARGE_FONT} color: black"
RESULT_OCCUR_STYLESHEET  = f"{FONT_BOLD} {LARGE_FONT} color: green"
RESULT_ABSENT_STYLESHEET = f"{FONT_BOLD} {LARGE_FONT} color: red"
INFOBOX_STYLESHEET = f"{MEDIUM_FONT} color:deeppink; background:cyan"
MSGBOX_STYLESHEET  = f"{MEDIUM_FONT} color:purple; background:lemonchiffon"
INPUTBOX_STYLESHEET = f"{SMALL_FONT} color: red; background: white" if WORDLE_DEBUG \
                      else f"{SMALL_FONT} color: {INPUT_COLOR}; background: {INPUT_COLOR}"

# noinspection PyAttributeOutsideInit
class WordleUI(QMainWindow):
    """UI to play the Wordle game."""
    def __init__(self, p_len:int=DEFAULT_WORD_LENGTH, p_rows:int=DEFAULT_NUM_ROWS):
        super().__init__()
        self.setWindowTitle("My Wordle App")
        # pixels: dx from left, dy from top, width, height
        self.setGeometry(600, 110, 720, 840)

        word_len = len(DEBUG_TARGET) if WORDLE_DEBUG else p_len
        num_rows = MAX_NUM_ROWS if WORDLE_DEBUG else p_rows

        self.lgr = log_control.get_logger()
        self.lgr.log(DEFAULT_LOG_LEVEL, f"{self.windowTitle()} start time = {get_current_time()}"
                                        f"\n\t\t\t\t\t\t >> word len = {word_len}; num rows = {num_rows}")

        self.ge = WordleGameEngine(self.lgr, word_len, num_rows)

        if WORDLE_DEBUG > 1:
            wcolors = QColor.colorNames()
            self.lgr.info("Available colors:")
            for c in wcolors:
                self.lgr.info(f"{c}")

        self.run_secs = 0
        wtimer = QTimer(self)
        wtimer.start(1000) # in msec = 1 second
        wtimer.timeout.connect(self.update_clock)

        self.create_menu()
        self.container = None
        self.reset()
        self.show()

    def reset(self, p_strict:bool=False):
        """Reset all the fields needed to start a new game."""
        self.ge.save_record(self.run_secs)
        self.lgr.info("Starting a NEW Game!")
        self.ge.start(p_strict)
        self.active = True
        self.current_guess = ""
        self.active_row = 0
        self.button_hover = False
        # allow words not in the constructed list
        self.override = False
        # game clock
        self.run_secs = 0
        self.pause_secs = 0
        self.lock_count = 0

        # remove the old container widget
        if self.container:
            self.container.deleteLater()
        # build a new container
        self.container = QWidget()
        main_layout = QVBoxLayout(self.container)
        # add elements to the layout
        main_layout.addLayout(self.create_top_section())
        self.input_box.clear()
        self.clock.setText("00:00")
        main_layout.addLayout(self.create_guess_section())
        self.reset_guesses()
        main_layout.addWidget(self.create_msg_box())
        main_layout.addLayout(self.create_result_section())
        self.reset_results()
        main_layout.addLayout(self.create_button_section())
        # set the central widget
        self.setCentralWidget(self.container)
        self.info_box.setText(("Strict" if p_strict else "Regular") + " Mode")
        self.msg_box.setText(f"Have  {(len(self.ge.current_words)):,}  {self.ge.word_length}-letter  words.")
        self.input_box.setFocus()

    def close(self, /):
        self.ge.save_record(self.run_secs)
        super().close()

    def create_menu(self):
        menu_bar = self.menuBar()
        game_menu = menu_bar.addMenu("&Game")
        settings_menu = menu_bar.addMenu("&Settings")
        info_menu = menu_bar.addMenu("&Info")

        new_action = QAction("&New Word", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Start a NEW game with a NEW word")
        new_action.triggered.connect(self.new_word_inquiry)
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.setStatusTip("Quit the application")
        quit_action.triggered.connect(self.exit_inquiry)
        game_menu.addAction(new_action)
        game_menu.addAction(quit_action)

        mode_action = QAction("Choose &Mode", self)
        mode_action.setShortcut("Ctrl+M")
        mode_action.setStatusTip("Choose STRICT or REGULAR mode")
        mode_action.triggered.connect(self.mode_inquiry)
        settings_menu.addAction(mode_action)

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

        # see status tips at the bottom of the window
        self.statusBar()

    def copyrite(self):
        QMessageBox.information(self, "Copyright", "Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>")

    def override_handler(self, p_event:QMouseEvent):
        """Set or unset the override property."""
        self.lgr.debug(f"QMouseEvent: {p_event}.")
        if self.override:
            self.override = False
            self.lgr.info("Override unset!")
            return
        self.override = True
        self.lgr.info("Override is set!")
        # call standard behavior if needed

    def create_top_section(self):
        """Input, info box, combo boxes, clock section of the UI."""
        self.input_box = QLineEdit()
        self.input_box.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.input_box.setFrame(False)
        self.input_box.setReadOnly(False)
        # restrict acceptable input to {ge.word_length} UPPERCASE letters
        self.input_box.setInputMask(">" + "A"*self.ge.word_length)
        self.input_box.setStyleSheet(INPUTBOX_STYLESHEET)
        self.input_box.textEdited.connect(self.response_change)
        self.input_box.returnPressed.connect(self.process_response)

        self.info_box = QLabel()
        # bind info_box.mousePressEvent function to WordleUI custom method
        self.info_box.mousePressEvent = self.override_handler
        self.info_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_box.setFrameStyle(BOX_FRAME_STYLE)
        self.info_box.setStyleSheet(INFOBOX_STYLESHEET)

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
        cfont = self.font()
        cfont.setPointSize(MEDIUM_FONT_SIZE)
        self.clock.setFont(cfont)

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.input_box)
        qhb_layout.setStretchFactor(self.input_box, 8 if WORDLE_DEBUG else 1)
        qhb_layout.addWidget(self.info_box)
        qhb_layout.setStretchFactor(self.info_box, 8)
        qhb_layout.addWidget(QLabel("word length:"))
        qhb_layout.addWidget(self.wordlen_combobox)
        qhb_layout.setStretchFactor(self.wordlen_combobox, 4)
        qhb_layout.addWidget(QLabel("number of rows:"))
        qhb_layout.addWidget(self.numrows_combobox)
        qhb_layout.setStretchFactor(self.numrows_combobox, 4)
        right_spacer = QLabel()
        qhb_layout.addWidget(right_spacer)
        qhb_layout.setStretchFactor(right_spacer, 2)
        qhb_layout.addWidget(self.clock)
        qhb_layout.setStretchFactor(self.clock, 4)
        return qhb_layout

    def set_word_length(self):
        new_word_len = int(self.wordlen_combobox.currentText())
        if new_word_len != self.ge.word_length:
            self.lgr.info(f"Setting word length to {new_word_len}.")
            self.ge.word_length = new_word_len
            self.reset(self.ge.strict_mode)

    def set_num_rows(self):
        new_num_rows = int(self.numrows_combobox.currentText())
        if new_num_rows != self.ge.num_rows:
            self.lgr.info(f"Setting number of rows to {new_num_rows}.")
            self.ge.num_rows = new_num_rows
            self.reset(self.ge.strict_mode)

    @staticmethod
    def create_guess_box(p_sidelen:int):
        guess_box = QLabel()
        guess_box.resize(p_sidelen, p_sidelen)
        guess_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        guess_box.setFrameStyle(BOX_FRAME_STYLE)
        return guess_box

    def create_guess_section(self):
        qvb_layout = QVBoxLayout()
        self.guess_boxes = [[self.create_guess_box(75) for _ in range(self.ge.word_length)] for _ in range(self.ge.num_rows)]

        layout_rows = []
        for j in range(self.ge.num_rows):
            if WORDLE_DEBUG > 1:
                self.lgr.debug(f"Setting guess row #{j}")
            layout_rows.append(QHBoxLayout())
            left_spacer = QLabel()
            layout_rows[j].addWidget(left_spacer)
            layout_rows[j].setStretchFactor(left_spacer, 2)
            for k in range(self.ge.word_length):
                if WORDLE_DEBUG > 1:
                    self.lgr.debug(f"Setting guess box #{j}-{k}")
                layout_rows[j].addWidget(self.guess_boxes[j][k])
                layout_rows[j].setStretchFactor(self.guess_boxes[j][k], 1)
            right_spacer = QLabel()
            layout_rows[j].addWidget(right_spacer)
            layout_rows[j].setStretchFactor(right_spacer, 2)
            qvb_layout.addItem(layout_rows[j])
        return qvb_layout

    def reset_guesses(self, p_style:str=GUESS_BASIC_STYLESHEET):
        for i in range(self.ge.num_rows):
            self.clear_guess_row(i)
            for j in range(self.ge.word_length):
                self.guess_boxes[i][j].setStyleSheet(p_style)

    def clear_guess_row(self, p_row:int):
        for i in range(self.ge.word_length):
            self.guess_boxes[p_row][i].clear()

    def create_msg_box(self, p_style:str=MSGBOX_STYLESHEET):
        self.msg_box = QLabel()
        self.msg_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_box.setFrameStyle(BOX_FRAME_STYLE)
        self.msg_box.setStyleSheet(p_style)
        return self.msg_box

    @staticmethod
    def create_result_box(p_letter:str):
        result_box = QLabel()
        result_box.setText(p_letter)
        result_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return result_box

    def create_result_section(self, p_letters:list=ORDERED_LETTERS):
        qvb_layout = QVBoxLayout()
        self.result_boxes = []
        for i in range(len(p_letters)):
            self.result_boxes.append(self.create_result_box(p_letters[i]))
        self.lgr.debug(f"Have {len(self.result_boxes)} result boxes.")

        vowel_row = QHBoxLayout()
        for j in range(6):
            vowel_row.addWidget(self.result_boxes[j])
        qvb_layout.addItem(vowel_row)

        consonant_rows = []
        for k in range(4):
            consonant_rows.append(QHBoxLayout())
            for l in range(1,6):
                consonant_rows[k].addWidget(self.result_boxes[5*(k+1)+l])
            qvb_layout.addItem(consonant_rows[k])
        return qvb_layout

    def reset_results(self):
        for i in range(len(ORDERED_LETTERS)):
            self.result_boxes[i].setStyleSheet(RESULT_BASIC_STYLESHEET)

    def eventFilter(self, p_obj, p_event):
        """Override eventFilter to catch QEvent.Type.Enter/Leave."""
        if p_obj == self.instr_btn or p_obj == self.new_word_btn or p_obj == self.exit_btn:
            # prevent input box from stealing focus when cursor over a button
            if p_event.type() == QEvent.Type.Enter:
                self.lgr.debug("Button hover.")
                self.button_hover = True
            if p_event.type() == QEvent.Type.Leave:
                self.lgr.debug("Button leave.")
                self.button_hover = False
        return super().eventFilter(p_obj, p_event)

    def create_button_section(self):
        """The instructions, exit and new game buttons of the UI."""
        self.instr_btn = QPushButton("Instructions")
        self.instr_btn.installEventFilter(self)
        self.instr_btn.setStyleSheet(f"{MEDIUM_FONT} color: yellow; background: blue")
        self.instr_btn.setAutoDefault(False)
        self.instr_btn.setDefault(False)
        self.instr_btn.clicked.connect(self.display_instructions)

        self.new_word_btn = QPushButton("New Word?")
        self.new_word_btn.installEventFilter(self)
        self.new_word_btn.setStyleSheet(f"{MEDIUM_FONT} color: green; background: orange")
        self.new_word_btn.setAutoDefault(False)
        self.new_word_btn.setDefault(False)
        self.new_word_btn.clicked.connect(self.new_word_inquiry)

        self.exit_btn = QPushButton("Quit App?")
        self.exit_btn.installEventFilter(self)
        self.exit_btn.setStyleSheet(f"{MEDIUM_FONT} color: darkred; background: yellow")
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.setDefault(False)
        self.exit_btn.clicked.connect(self.exit_inquiry)

        qhb_layout = QHBoxLayout()
        qhb_layout.addWidget(self.instr_btn)
        qhb_layout.addWidget(self.new_word_btn)
        qhb_layout.addWidget(self.exit_btn)
        qvb_layout = QVBoxLayout()
        qvb_layout.addWidget(QLabel("\t\t\t\t")) # spacer
        qvb_layout.addLayout(qhb_layout)
        return qvb_layout

    def response_change(self, p_resp:str):
        """Place the response letters in the guess boxes of the current row."""
        if not self.active:
            return
        self.lgr.debug(f"Response changed to '{p_resp}'; Input box text = {self.input_box.text()}")
        self.clear_guess_row(self.active_row)
        self.msg_box.setText(f"Row {self.active_row+1} is active. Text = '{p_resp}'")
        if p_resp:
            self.current_guess = get_clean_word(p_resp)
            current_box = 0
            for letter in self.current_guess:
                self.guess_boxes[self.active_row][current_box].setText(letter)
                current_box += 1

    def process_response(self):
        """'Enter' key was pressed so check if the current response is a valid word then mark the guess and result boxes."""
        if not self.active:
            return
        self.lgr.info(f"{"Strict" if self.ge.strict_mode else "Regular"} mode >> process response '{self.current_guess}'.")
        if not self.current_guess:
            self.lgr.info(">> NOT a valid response.")
            return
        if self.override: # use then unset
            self.ge.current_words.append(self.current_guess)
            self.lgr.info(f"Added '{self.current_guess}' to acceptable words.")
            self.override = False
        if self.ge.check_guess(self.current_guess, self.active_row):
            self.mark_current_guess()
            self.active_row += 1
            self.current_guess = ""
            self.input_box.clear()
            if self.active and self.active_row == self.ge.num_rows:
                self.success(False)
        else:
            mesg = self.ge.info_mesg if self.ge.info_mesg else f"'{self.current_guess}' is NOT a valid word... :("
            self.lgr.info(mesg)
            self.msg_box.setText(mesg)
        self.ge.info_mesg = ""

    def mark_current_guess(self):
        """Mark the current guess boxes as green, yellow or grey & the result letters as green or red."""
        # GUESS boxes
        guess_idx = [ _ for _ in range(len(self.current_guess)) ]
        newtarget = self.ge.current_target
        self.lgr.info(f">> current target = '{self.ge.current_target}'; current guess = '{self.current_guess}'")
        for i in range(self.ge.word_length):
            # EXACT MATCH of letter position in guess and target
            if self.current_guess[i] == self.ge.current_target[i]:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_EXACT_STYLESHEET)
                guess_idx.remove(i)
                if i not in self.ge.green_index:
                    self.ge.green_index.append(i)
                    self.ge.green_index.sort() # required
                    self.lgr.debug(f"green index = {self.ge.green_index}")
                self.lgr.info(f"Exact @ [{i}] > '{self.current_guess[i]}'; new target = '{newtarget}'; ")
                newtarget = newtarget.replace(self.ge.current_target[i], '', 1)
            # guessed letter is ABSENT from target
            elif self.current_guess[i] not in self.ge.current_target:
                self.guess_boxes[self.active_row][i].setStyleSheet(GUESS_ABSENT_STYLESHEET)
                guess_idx.remove(i)
                self.lgr.info(f"Absent @ [{i}] > '{self.current_guess[i]}'")
            else:
                self.lgr.debug(f"Check occurrence of '{self.current_guess[i]}' at [{i}].")
        self.lgr.info(f"guess index = '{guess_idx}'; new target = '{newtarget}'; green index = {self.ge.green_index}")
        # find target letters PRESENT in the guess but at a DIFFERENT POSITION
        self.ge.yellow_list.clear()
        for j in guess_idx:
            if self.current_guess[j] in newtarget:
                self.guess_boxes[self.active_row][j].setStyleSheet(GUESS_OCCUR_STYLESHEET)
                self.ge.yellow_list.append(self.current_guess[j])
                self.lgr.debug(f"yellow list = {self.ge.yellow_list}")
                self.lgr.info(f"Occurrence @ [{j}] > '{self.current_guess[j]}'; new target = '{newtarget}'")
                newtarget = newtarget.replace(self.current_guess[j], '', 1)
            else:
                self.guess_boxes[self.active_row][j].setStyleSheet(GUESS_ABSENT_STYLESHEET)
                self.lgr.info(f"Absent @ [{j}] > '{self.current_guess[j]}'; new target = '{newtarget}'")
        self.lgr.info(f"yellow list = {self.ge.yellow_list}")
        # RESULT boxes
        for k in range(len(self.result_boxes)):
            check_letter = self.result_boxes[k].text()
            if check_letter in self.current_guess:
                if check_letter in self.ge.current_target:
                    self.result_boxes[k].setStyleSheet(RESULT_OCCUR_STYLESHEET)
                else:
                    self.result_boxes[k].setStyleSheet(RESULT_ABSENT_STYLESHEET)
        if self.current_guess == self.ge.current_target:
            self.success(True)

    def success(self, p_victory:bool):
        self.ge.outcome = "Victory!" if p_victory else "Failure."
        self.msg_box.setText(f"{self.ge.outcome}  :)" if p_victory
                             else f"{self.ge.outcome}..  :(  The secret word was '{self.ge.current_target}'.")
        self.info_box.setText(self.ge.outcome)
        self.lgr.info(self.ge.outcome)
        self.active = False

    def update_clock(self):
        """Update the game clock when the game is active."""
        log_pause = 600 if self.lock_count > 10 else 60
        locked = check_screen_locked(self.lgr, WORDLE_DEBUG) # pause when the screen is locked
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
        # make sure keystrokes get to the input box
        if not self.button_hover:
            if WORDLE_DEBUG > 1:
                self.lgr.debug(f"set focus to input box at {self.run_secs}")
            self.input_box.setFocus()

    def new_word_inquiry(self):
        """Evaluate if the user wants a new secret word."""
        confirm_box, continue_button, new_word_button = self.create_new_word_msgbox()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing this game.")
        elif confirm_box.clickedButton() == new_word_button:
            self.lgr.info("Starting over with a new word.")
            self.reset(self.ge.strict_mode)

    def exit_inquiry(self):
        """Evaluate if the user wants to exit the app."""
        confirm_box, continue_button, quit_button = self.create_exit_msgbox()
        confirm_box.exec()
        if confirm_box.clickedButton() == continue_button:
            self.lgr.info("Continuing the game.")
        elif confirm_box.clickedButton() == quit_button:
            self.lgr.info("Quit the app.")
            self.close()

    def mode_inquiry(self):
        """Evaluate if the user wants strict or regular mode."""
        confirm_box, strict_button, regular_button = self.create_mode_msgbox()
        confirm_box.exec()
        if confirm_box.clickedButton() == strict_button:
            self.ge.strict_mode = True
            self.info_box.setText("Strict Mode")
            self.lgr.info("SET strict mode.")
        elif confirm_box.clickedButton() == regular_button:
            self.ge.strict_mode = False
            self.info_box.setText("Regular Mode")
            self.lgr.info("SET regular mode.")

    def display_instructions(self):
        """Display 'How to play Wordle'."""
        infobox = QMessageBox()
        infobox.setIcon(QMessageBox.Icon.Information)
        infobox.setStyleSheet(SMALL_FONT)
        infobox.setText(self.ge.get_instructions())
        infobox.setMinimumWidth(720) # DOES NOTHING... ?!
        infobox.exec()

    def create_new_word_msgbox(self):
        """Create a QMessageBox to ask about getting a new secret word."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("Are you SURE you want to END this game and get a NEW word?")
        continue_button = confirm_box.addButton("No! >> Continue with this word...", QMessageBox.ButtonRole.ActionRole)
        continue_button.setStyleSheet("QPushButton:focus {background: chartreuse}")
        new_word_button = confirm_box.addButton("Yes >> Get a NEW word!", QMessageBox.ButtonRole.ActionRole)
        new_word_button.setStyleSheet("QPushButton:focus {background: MediumVioletRed}")
        confirm_box.setDefaultButton(continue_button if self.active else new_word_button)
        return confirm_box, continue_button, new_word_button

    def create_exit_msgbox(self):
        """Create a QMessageBox to ask about exiting the app."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("Are you SURE you want to QUIT the app?")
        continue_button = confirm_box.addButton("No! >> Continue this game...", QMessageBox.ButtonRole.ActionRole)
        continue_button.setStyleSheet("QPushButton:focus {background: chartreuse}")
        quit_button = confirm_box.addButton("Yes >> QUIT the app.", QMessageBox.ButtonRole.ActionRole)
        quit_button.setStyleSheet("QPushButton:focus {background: red}")
        confirm_box.setDefaultButton(continue_button if self.active else quit_button)
        return confirm_box, continue_button, quit_button

    def create_mode_msgbox(self):
        """Create a QMessageBox to ask about using strict or regular mode."""
        confirm_box = QMessageBox()
        confirm_box.setIcon(QMessageBox.Icon.Question)
        confirm_box.setStyleSheet(MEDIUM_FONT)
        confirm_box.setText("In 'strict' mode any previous green or yellow letter guesses MUST be used in subsequent guesses.")
        strict_button = confirm_box.addButton("Set STRICT mode.", QMessageBox.ButtonRole.ActionRole)
        strict_button.setStyleSheet("QPushButton:focus {background: violet}") # does NOT work if try to set !focus too...
        regular_button = confirm_box.addButton("Set REGULAR mode.", QMessageBox.ButtonRole.ActionRole)
        regular_button.setStyleSheet("QPushButton:focus {background: paleturquoise}")
        confirm_box.setDefaultButton(strict_button if self.ge.strict_mode else regular_button)
        return confirm_box, strict_button, regular_button
# END class WordleUI

# noinspection PyAttributeOutsideInit
class WordleGameEngine:
    """The Wordle game internal data and procedures."""
    def __init__(self, p_lgr:logging.Logger, p_len:int=DEFAULT_WORD_LENGTH, p_rows:int=DEFAULT_NUM_ROWS):
        self.lgr = p_lgr
        if MIN_WORD_LENGTH <= p_len <= MAX_WORD_LENGTH:
            self.word_length = p_len
        if MIN_NUM_ROWS <= p_rows <= MAX_NUM_ROWS:
            self.num_rows = p_rows
        self.good_guesses = None
        self.lgr.info(f"Initialized Game Engine >> Word length = {self.word_length}; Number of rows = {self.num_rows}.")

    def start(self, p_strict:bool=False):
        """Set starting values for a new game."""
        self.good_guesses = []
        self.bad_guesses = []
        self.green_index = []
        self.yellow_list = []
        self.info_mesg = ""
        self.strict_mode = p_strict
        self.saved = False
        self.outcome = ""
        self.get_current_words()
        self.current_target = DEBUG_TARGET if WORDLE_DEBUG and len(DEBUG_TARGET) == self.word_length\
                                else self.current_words[random.randrange(0, len(self.current_words))]
        self.lgr.info(f"current target word = {self.current_target}; total number of words = {len(self.current_words)}")

    def get_instructions(self) -> str:
        """Need as a function so word_length and num_rows get updated."""
        return ("\tHow to Play Wordle:\n"
                "---------------------------------------------------------------------------------\n"
                f"1) Try to guess the secret {self.word_length}-letter word.\n\n"
                f"2) Type a {self.word_length}-letter word and press ENTER to evaluate it. "
                f" Your entry will be accepted if it is a VALID Wordle word.\n\n"
                "3) Each letter in the correct position will shade GREEN.\n\n"
                "4) Letters present in the secret word but in the WRONG POSITION in your guess will shade YELLOW.\n\n"
                "5) Any letter NOT present in the secret word will shade GREY.\n\n"
                "6) In STRICT mode any 'green' and 'yellow' letters found in a guess MUST be used in subsequent guesses.\n\n"
                f"7) You have {self.num_rows} attempts to find the secret word.\n\n"
                "8) >> Resetting the word length or number of rows will start a BRAND NEW game.\n\n"
                "9) If you Quit the app (Ctrl-Q) or start a New word (Ctrl-N) your current game results will be saved to a file.")

    def get_current_words(self):
        """Get all words that match the current word length."""
        self.current_words = []
        for wd in all_game_words:
            if len(wd) == self.word_length:
                self.current_words.append(get_clean_word(wd))

    def check_guess(self, p_resp:str, p_row:int) -> bool:
        """Check for a valid response."""
        self.lgr.debug(f"check response '{p_resp}'.")
        if p_resp == self.current_target:
            self.lgr.info("Found the target word!")
            result = True
        elif p_resp not in self.current_words:
            result = False
        elif p_row > 0 and self.strict_mode:
            result = self.checkguess_strict(p_resp)
        else:
            self.lgr.info(f"'{p_resp}' is a valid word.")
            result = True
        if result:
            self.good_guesses.append(p_resp)
            return True
        self.bad_guesses.append(p_resp)
        if check_plural(p_resp, self.current_words):
            self.info_mesg = "Most simple plurals are just IGNORED..."
        return False

    def checkguess_strict(self, p_resp:str) -> bool:
        """Make sure that previous green and yellow responses are carried over."""
        self.lgr.debug(f"response = '{p_resp}'; green index = {self.green_index}")
        yl_resp = p_resp
        for gi in self.green_index:
            if p_resp[gi] != self.current_target[gi]:
                self.info_mesg = f"Missing green '{self.current_target[gi]}' at position {gi+1}."
                self.lgr.info(self.info_mesg)
                return False
            yl_resp = yl_resp.replace(p_resp[gi], '', 1)
        self.lgr.debug(f"yellow list = {self.yellow_list}")
        for yl in self.yellow_list:
            if yl not in yl_resp:
                self.info_mesg = f"Missing yellow '{yl}'."
                self.lgr.info(self.info_mesg)
                return False
            yl_resp = yl_resp.replace(yl, '', 1)
        return True

    def save_record(self, p_secs:int) -> str:
        """Save all important information from the current game."""
        if self.good_guesses and not self.saved:
            game_record = {"Result":self.outcome, "Mode":("Strict" if self.strict_mode else "Regular"),
                           "Time":p_secs, "Number of Rows":self.num_rows, "Target Word":self.current_target,
                           "Good Guesses":self.good_guesses, "Bad Guesses":self.bad_guesses}
            grfile = save_to_json(f"WordleRecord_{self.current_target}", game_record)
            self.saved = True
            self.lgr.info(f"Saved game record as: {grfile}\n\n\n======================================\n")
            return grfile
        return "No good guesses."
# END class WordleGameEngine


wordle_log_level = logging.DEBUG if WORDLE_DEBUG else logging.INFO
log_control = MhsLogger(WordleUI.__name__, con_level = wordle_log_level)
log_control.debug(f"WORDLE_DEBUG = {WORDLE_DEBUG}")

def wordle_main():
    usage_text = f"Usage: python3 {get_filename(argv[0])} [word_length:int] [num_rows:int]\n"
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
                raise ValueError("Invalid arguments.")
            window = WordleUI(int(argv[1]), int(argv[2]))
            log_control.info(f"argv[1]: {argv[1]}, argv[2]: {argv[2]}")
        elif len(argv) > 1:
            if not argv[1].isdigit():
                print(usage_text)
                log_control.debug("Invalid argument.")
                raise ValueError("Invalid argument.")
            window = WordleUI(int(argv[1]))
            log_control.info(f"argv[1]: {argv[1]}, p_rows = {DEFAULT_NUM_ROWS}")
        else:
            window = WordleUI()
            log_control.debug("No command line arguments.")
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


if __name__ == "__main__":
    wordle_main()
