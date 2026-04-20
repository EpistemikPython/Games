##############################################################################################################################
# coding=utf-8
#
# spellingbeeGameEngine.py
#   -- the SpellingBee game internal data and procedures
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.10+"
__created__ = "2025-08-18"
__updated__ = "2026-04-19"

import random
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
from enum import Enum
path.append("/home/marksa/git/Python/Games/SpellingBee/input")
from spellingbee_words import all_sb_words as sb_words

MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 21
PANGRAM_LENGTH = 7
GE_DEBUG = True

class PointLevel(Enum):
    Beginning   = 0.0
    Fine        = 0.125
    Nice        = 0.25
    Good        = 0.375
    Halfway     = 0.5
    Excellent   = 0.6
    Outstanding = 0.7
    Supreme     = 0.8
    Magnificent = 0.9
    Perfection  = 1.0

# noinspection PyAttributeOutsideInit
class GameEngine:
    """The SpellingBee game internal data and procedures."""
    def __init__(self, p_lgr:MhsLogger):
        self.lgr = p_lgr
        self.lgr.info(f"Initialized Game Engine >> total number of words = {len(sb_words)}")

    def start(self, p_letters:str=""):
        self.current_guess = ""
        self.bad_letter = ''
        self.total_num_answers = 0
        self.num_good_guesses = 0
        self.point_total = 0
        self.maximum_points = 0
        self.current_points = 0
        self.saved = False
        self.current_answer_list = []
        self.pangrams = []
        self.pangram_guesses = []
        self.good_guesses = []
        self.bad_word_guesses = []
        self.bad_letter_guesses = []
        self.surround_letters = []
        if p_letters and len(p_letters) > 0:
            # check and use specified letters
            # first letter = required; remaining 6 letters = outers
            pass
        self.load_pangrams()
        self.lgr.info(f"number of pangrams = {len(self.pangrams)}")
        self.current_target = self.pangrams[random.randrange(0, len(self.pangrams))]
        self.lgr.info(f"current target word = {self.current_target}")
        self.required_letter = self.current_target[random.randrange(0, len(self.current_target))]
        self.lgr.info(f"required letter = {self.required_letter}")
        for lett in self.current_target:
            if lett not in self.required_letter and lett not in self.surround_letters:
                self.surround_letters.append(lett)
        self.lgr.info(f"outer letters = {self.surround_letters}")
        self.find_maximum_points()
        self.lgr.info("Started a Game.")

    def save_record(self):
        # save all important information from this game
        if not self.saved and self.good_guesses:
            self.good_guesses.sort()
            game_record = {"TARGET":self.current_target, "REQUIRED":self.required_letter, "POINT_TOTAL":self.point_total,
                           "MAX_POINTS":self.maximum_points, "PANGRAM_GUESSES":self.pangram_guesses,
                           "GOOD_GUESSES":self.good_guesses, "BAD_LETTER_GUESSES":self.bad_letter_guesses,
                           "BAD_WORD_GUESSES":self.bad_word_guesses, "COMPLETE_ANSWER_LIST":self.current_answer_list}
            grfile = save_to_json(f"GameRecord_{self.required_letter}_{self.current_target}", game_record)
            self.lgr.info(f"Saved game record as: {grfile}")
            self.saved = True

    def check_guess(self, resp:str) -> bool:
        """Check all letters for a good response and also see if a pangram."""
        self.current_guess = get_clean_word(resp)
        self.lgr.info(f"check guess '{self.current_guess}':")
        if self.current_guess in self.current_answer_list:
            self.lgr.info(f"{self.current_guess} is a GOOD guess!")
            self.good_guesses.append(self.current_guess)
            self.current_points = (1 if len(resp) == MIN_WORD_LENGTH else len(resp))
            self.num_good_guesses += 1
            if self.check_pangram():
                self.lgr.info(f"{self.current_guess} is a PANGRAM!")
                self.pangram_guesses.append(self.current_guess)
                self.current_points += len(resp) # PANGRAM BONUS
            self.point_total += self.current_points
            return True

        self.lgr.info(f"{self.current_guess} is a BAD guess!")
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
        if word in sb_words:
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

    def load_pangrams(self):
        for it in sb_words:
            result = []
            item = get_clean_word(it)
            # don't use ING or ED forms
            if item[-3:] == "ING" or item[-2:] == "ED":
                continue
            for lett in item:
                if lett not in result:
                    result.append(lett)
            if len(result) == PANGRAM_LENGTH:
                self.pangrams.append(item)
        if GE_DEBUG:
            fname = save_to_json("pangrams", self.pangrams)
            self.lgr.info(f"Saved file: {fname}.")

    def get_current_level(self) -> str:
        current_point_percent = self.point_total / self.maximum_points
        for item in reversed(PointLevel):
            if current_point_percent >= item.value:
                return item.name
        return PointLevel.Beginning.name

    def find_maximum_points(self) -> int:
        if self.maximum_points > 0:
            return self.maximum_points
        point_total = 0
        for item in sb_words:
            if self.check_letters(item) and self.check_word(item) and not self.check_plurals(item):
                point_total += ( 1 if len(item) == MIN_WORD_LENGTH else len(item) )
                self.current_answer_list.append(item)
                if self.check_pangram(item):
                    point_total += len(item) # PANGRAM BONUS
        self.current_answer_list.sort()
        self.lgr.info(f"Maximum points = {point_total}.")
        self.total_num_answers = len(self.current_answer_list)
        self.lgr.info(f"Total number of acceptable answers for '{self.required_letter}' + {self.surround_letters}"
                       f" = {self.total_num_answers}")
        self.maximum_points = point_total
        if GE_DEBUG:
            fname = save_to_json("current_answer_list", self.current_answer_list)
            self.lgr.info(f"Saved file: {fname}.")
        return point_total

    def check_plurals(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if word not in self.current_answer_list and ((word[-1] == 'S' and word[-2] != 'S' and word[:-1] in sb_words) or
                                                     (word[-2:] == "ES" and word[:-2] in sb_words)):
            return True
        return False
# END class GameEngine
