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
__updated__ = "2026-05-11"

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
SBGE_DEBUG = True

class PointLevel(Enum):
    Beginning   = 0.0
    Fine        = 0.125
    Nice        = 0.25
    Good        = 0.375
    Halfway     = 0.5
    Great       = 0.6
    Excellent   = 0.7
    Outstanding = 0.8
    Magnificent = 0.9
    Perfection  = 1.0

# noinspection PyAttributeOutsideInit
class GameEngine:
    """The SpellingBee game internal data and procedures."""
    def __init__(self, p_lgr:MhsLogger, p_letters:str=""):
        self.lgr = p_lgr
        # TODO: check and use specified letters
        if p_letters and len(p_letters) == PANGRAM_LENGTH:
            # first letter = required; remaining 6 letters = outers
            pass
        self.lgr.info(f"Initialized Game Engine >> total number of words = {len(sb_words)}")

    def start(self):
        self.current_guess = ""
        self.bad_letter = ''
        self.total_num_answers = 0
        self.num_good_guesses = 0
        self.point_total = 0
        self.maximum_points = 0
        self.current_points = 0
        self.saved = False
        self.answer_list = []
        self.pangrams = []
        self.pangram_guesses = []
        self.good_guesses = []
        self.bad_word_guesses = []
        self.bad_letter_guesses = []
        self.surround_letters = []
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
        self.make_answer_list()
        self.get_max_points()
        self.lgr.info("Started a Game.")

    def save_record(self):
        # save all important information from this game
        if not self.saved and self.good_guesses:
            self.good_guesses.sort()
            game_record = {"TARGET WORD":self.current_target, "REQUIRED LETTER":self.required_letter, "POINTS EARNED":self.point_total,
                           "MAX POSSIBLE POINTS":self.maximum_points, "FINAL RATING":self.get_current_level(),
                           "PANGRAM GUESSES":self.pangram_guesses, "GOOD GUESSES":self.good_guesses,
                           "MISSED ANSWERS":self.missed_answers(), "BAD LETTER GUESSES":self.bad_letter_guesses,
                           "BAD WORD GUESSES":self.bad_word_guesses, "COMPLETE ANSWER LIST":self.answer_list}
            grfile = save_to_json(f"GameRecord_{self.required_letter}_{self.current_target}", game_record)
            self.lgr.info(f"Saved game record as: {grfile}")
            self.saved = True

    def check_guess(self, resp:str) -> bool:
        """Check all letters for a good response and also see if a pangram."""
        self.lgr.debug(f"check response '{resp}':")
        self.current_guess = get_clean_word(resp)
        if self.current_guess in self.answer_list:
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
        if SBGE_DEBUG:
            fname = save_to_json("pangrams", self.pangrams)
            self.lgr.info(f"Saved file: {fname}.")

    def get_current_level(self) -> str:
        current_point_percent = self.point_total / self.maximum_points
        for item in reversed(PointLevel):
            if current_point_percent >= item.value:
                return item.name
        return PointLevel.Beginning.name

    def make_answer_list(self):
        if not sb_words:
            self.lgr.warning("Trying to find answers but NO word list!")
            return
        for item in sb_words:
            if self.check_letters(item) and self.check_word(item):
                self.answer_list.append(item)
        self.answer_list.sort()
        self.total_num_answers = len(self.answer_list)
        self.lgr.info(f"Total number of acceptable answers for '{self.required_letter}' + {self.surround_letters}"
                       f" = {self.total_num_answers}")
        if SBGE_DEBUG:
            fname = save_to_json("current_answer_list", self.answer_list)
            self.lgr.info(f"Saved file: {fname}.")

    def get_max_points(self) -> int:
        if not self.answer_list:
            self.lgr.warning("Trying to get max points but NO answer list!")
            return 0
        if self.maximum_points > 0:
            return self.maximum_points
        point_total = 0
        for item in self.answer_list:
            point_total += ( 1 if len(item) == MIN_WORD_LENGTH else len(item) )
            if self.check_pangram(item):
                point_total += len(item) # PANGRAM BONUS
        self.maximum_points = point_total
        self.lgr.info(f"Maximum points = {self.maximum_points}.")
        return point_total

    def check_plurals(self, word:str = "") -> bool:
        if not word:
            word = self.current_guess
        if word in self.answer_list:
            return False
        if (word[-1] == 'S' and word[-2] != 'S' and word[:-1] in sb_words) or (word[-2:] == "ES" and word[:-2] in sb_words):
            return True
        return False

    def missed_answers(self) -> list:
        results = []
        for word in self.answer_list:
            if word not in self.good_guesses:
                results.append(word)
        return results
# END class GameEngine


if __name__ == "__main__":
    print(f">> Load from a UI.")
    exit(0)
