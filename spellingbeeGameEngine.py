##############################################################################################################################
# coding=utf-8
#
# spellingbeeGameEngine.py
#   -- SpellingBee game engine
#
# Copyright (c) 2025 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-08-18"
__updated__ = "2025-09-09"

import random
from sys import path, argv
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
import pangrams
import all_spellbee_words

TARGET_WORD_FILE = "/home/marksa/git/Python/Games/input/pangrams.json"
REFERENCE_WORD_FILE = "/home/marksa/git/Python/Games/input/all_spellbee_words.json"
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 21

class GameEngine:
    def __init__(self):
        self._lgr = log_control.get_logger()
        self.required_letter = ''
        self.surround_letters = []
        self.current_target = ""
        self.current_guess = ""
        self.all_pangrams = pangrams.pangrams
        self._lgr.info(f"type(self.pangrams) = {type(self.all_pangrams)}")
        self._lgr.info(f"len(self.pangrams) = {len(self.all_pangrams)}")
        self.all_words = all_spellbee_words.all_sb_words
        self._lgr.info(f"type(allwords) = {type(self.all_words)}")
        self._lgr.info(f"len(allwords) = {len(self.all_words)}")
        self.pangram_guesses = []
        self.good_guesses = []
        self.bad_guesses = []
        self.point_total = 0

    def start_game(self):
        self.current_target = self.all_pangrams[random.randrange(0, len(self.all_pangrams))]
        self._lgr.info(f"current target word = {self.current_target}")
        self.required_letter = self.current_target[random.randrange(0, len(self.current_target))]
        self._lgr.info(f"required letter = {self.required_letter}")
        for lett in self.current_target:
            if lett not in self.required_letter and lett not in self.surround_letters:
                self.surround_letters.append(lett)
        self._lgr.info(f"outer letters = {self.surround_letters}")

    def format_response(self, resp:str) -> str:
        # remove non-letters, capitalize and return
        formatted_string = ""
        for c in resp:
            if str.isalpha(c):
                formatted_string += c.upper()
        self.current_guess = formatted_string.rstrip().lstrip()
        return self.current_guess

    def check_response(self, resp:str) -> bool:
        self.format_response(resp)
        self._lgr.info(f"check word '{self.current_guess}'")
        if self.check_letters() and self.check_word():
            self._lgr.info(f"{self.current_guess} is a GOOD guess!")
            self.good_guesses.append(self.current_guess)
            self.point_total += (1 if len(resp) == 4 else len(resp))
            if self.check_pangram():
                self._lgr.info(f"{self.current_guess} is a PANGRAM!")
                self.pangram_guesses.append(self.current_guess)
                self.point_total += 7
            return True
        self._lgr.info(f"{self.current_guess} is a BAD guess!")
        self.bad_guesses.append(self.current_guess)
        return False

    def check_letters(self) -> bool:
        if self.required_letter not in self.current_guess:
            return False
        for lett in self.current_guess:
            if lett != self.required_letter and lett not in self.surround_letters:
                return False
        return True

    def check_word(self) -> bool:
        if self.current_guess in self.all_words:
            return True
        return False

    def check_pangram(self) -> bool:
        if self.required_letter not in self.current_guess:
            return False
        for lett in self.surround_letters:
            if lett not in self.current_guess:
                return False
        return True

    def accept_response(self, resp:str):
        pass
# END class GameEngine


log_control = MhsLogger(GameEngine.__name__, con_level = DEFAULT_LOG_LEVEL)
