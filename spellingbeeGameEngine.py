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
__updated__ = "2025-09-18"

import random
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
from enum import Enum
import pangrams
import all_words

TARGET_WORD_FILE = "/home/marksa/git/Python/Games/input/pangrams.json"
REFERENCE_WORD_FILE = "/home/marksa/git/Python/Games/input/all_spellbee_words.json"
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 21
PANGRAM_BONUS = 7

class Level(Enum):
    Beginning = 0.0
    Fine      = 0.1
    Nice      = 0.2
    Good      = 0.4
    Excellent = 0.6
    Supreme   = 0.8
    Perfect   = 1.0

class GameEngine:
    def __init__(self):
        self._lgr = log_control.get_logger()
        self.required_letter = ''
        self.surround_letters = []
        self.current_target = ""
        self.current_guess = ""
        self.current_answer_list = []
        self.total_num_answers = 0
        self.all_pangrams = pangrams.pangrams
        self._lgr.info(f"number of pangrams = {len(self.all_pangrams)}")
        self.all_words = all_words.all_sb_words
        self._lgr.info(f"total number of words = {len(self.all_words)}")
        self.pangram_guesses = []
        self.good_guesses = []
        self.num_good_guesses = 0
        self.bad_letter = ""
        self.bad_word_guesses = []
        self.bad_letter_guesses = []
        self.point_total = 0
        self.maximum_points = 0
        self.saved = False
        # self.check_lists()

    def start_game(self):
        self.current_target = self.all_pangrams[random.randrange(0, len(self.all_pangrams))]
        self._lgr.info(f"current target word = {self.current_target}")
        self.required_letter = self.current_target[random.randrange(0, len(self.current_target))]
        self._lgr.info(f"required letter = {self.required_letter}")
        for lett in self.current_target:
            if lett not in self.required_letter and lett not in self.surround_letters:
                self.surround_letters.append(lett)
        self._lgr.info(f"outer letters = {self.surround_letters}")
        self.find_maximum_points()

    def end_game(self):
        # save game record
        if not self.saved and self.good_guesses:
            self.good_guesses.sort()
            game_record = {"TARGET":self.current_target, "REQUIRED":self.required_letter, "POINT_TOTAL":self.point_total,
                           "MAX_POINTS":self.maximum_points, "PANGRAM_GUESSES":self.pangram_guesses,
                           "GOOD_GUESSES":self.good_guesses, "BAD_LETTER_GUESSES":self.bad_letter_guesses,
                           "BAD_WORD_GUESSES":self.bad_word_guesses, "COMPLETE_ANSWER_LIST":self.current_answer_list}
            grfile = save_to_json(f"GameRecord_{self.required_letter}_{self.current_target}", game_record)
            self._lgr.info(f"Saved game record as: {grfile}")
            self.saved = True

    def format_guess(self, resp:str) -> str:
        """Remove non-letters, capitalize and remove extra space left and right."""
        formatted_string = ""
        for c in resp:
            if str.isalpha(c):
                formatted_string += c.upper()
        self.current_guess = formatted_string.rstrip().lstrip()
        return self.current_guess

    def check_guess(self, resp:str) -> bool:
        """Check all letters for a good response and also see if a Pangram."""
        self.format_guess(resp)
        self._lgr.info(f"check word '{self.current_guess}'")
        if self.current_guess in self.current_answer_list:
            self._lgr.info(f"{self.current_guess} is a GOOD guess!")
            self.good_guesses.append(self.current_guess)
            self.point_total += (1 if len(resp) == 4 else len(resp))
            self.num_good_guesses += 1
            if self.check_pangram():
                self._lgr.info(f"{self.current_guess} is a PANGRAM!")
                self.pangram_guesses.append(self.current_guess)
                self.point_total += PANGRAM_BONUS
            return True
        self._lgr.info(f"{self.current_guess} is a BAD guess!")
        if not self.check_letters():
            self.bad_letter_guesses.append(self.current_guess)
            return False
        self.bad_word_guesses.append(self.current_guess)
        return False

    def check_bad_letter(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        for lett in word:
            if lett != self.required_letter and lett not in self.surround_letters:
                self.bad_letter = lett
                return True
        self.bad_letter = ""
        return False

    def check_letters(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if self.required_letter not in word:
            return False
        if self.check_bad_letter(word):
            return False
        return True

    def check_word(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if word in self.all_words:
            return True
        return False

    def check_pangram(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if self.required_letter not in word:
            return False
        for lett in self.surround_letters:
            if lett not in word:
                return False
        return True

    def get_current_level(self) -> str:
        current_point_percent = self.point_total / self.maximum_points
        if current_point_percent >= Level.Perfect.value:
            return Level.Perfect.name
        if current_point_percent >= Level.Supreme.value:
            return Level.Supreme.name
        if current_point_percent >= Level.Excellent.value:
            return Level.Excellent.name
        if current_point_percent >= Level.Good.value:
            return Level.Good.name
        if current_point_percent >= Level.Nice.value:
            return Level.Nice.name
        if current_point_percent >= Level.Fine.value:
            return Level.Fine.name
        return Level.Beginning.name

    def find_maximum_points(self) -> int:
        if self.maximum_points > 0:
            return self.maximum_points
        total = 0
        for item in self.all_words:
            if self.check_letters(item) and self.check_word(item) and not self.check_plurals(item):
                total += ( 1 if len(item) == 4 else len(item) )
                self.current_answer_list.append(item)
                if self.check_pangram(item):
                    total += PANGRAM_BONUS
        self.current_answer_list.sort()
        self._lgr.info(f"Maximum points = {total}.")
        self.total_num_answers = len(self.current_answer_list)
        self._lgr.info(f"Total number of acceptable answers for '{self.required_letter}' + {self.surround_letters}"
                       f" = {self.total_num_answers}")
        save_to_json(f"{self.required_letter}_{self.current_target}", self.current_answer_list)
        self.maximum_points = total
        return total

    def check_plurals(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if word not in self.current_answer_list and ( (word[-1] == 'S' and word[:-1] in self.all_words) or
                (word[-2:] == "ES" and word[:-2] in self.all_words) ):
            return True
        return False

    def check_lists(self):
        check = []
        for item in self.all_pangrams:
            if item not in self.all_words:
                check.append(item)
        if check:
            save_to_json("check_pangrams", check)
        else:
            self._lgr.info("All pangrams in word list!")

# END class GameEngine


log_control = MhsLogger(GameEngine.__name__, con_level = DEFAULT_LOG_LEVEL, con_format = FILE_FORMAT)
