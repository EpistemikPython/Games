##############################################################################################################################
# coding=utf-8
#
# wordleGameEngine.py
#   -- the Wordle game internal data and procedures
#
# Copyright (c) 2026 Mark Sattolo <epistemik@gmail.com>

__author_name__    = "Mark Sattolo"
__author_email__   = "epistemik@gmail.com"
__python_version__ = "3.11+"
__created__ = "2026-03-05"
__updated__ = "2026-07-05"

import random
from sys import path
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *
path.append("/home/marksa/git/Python/Games/Wordle/input")
from wordle_words import all_wordle_words as all_words

MIN_WORD_LENGTH = 5
MAX_WORD_LENGTH = 9
DEFAULT_NUM_ROWS = 6
WDGE_DEBUG = True

# noinspection PyAttributeOutsideInit
class GameEngine:
    """The SpellingBee game internal data and procedures."""
    def __init__(self, p_lgr:MhsLogger, p_len:int=5):
        self.lgr = p_lgr
        # TODO: check and use specified word length
        if p_len <= MAX_WORD_LENGTH:
            pass
        self.lgr.info(f"Initialized Game Engine >> total number of words = {len(all_words)}")
        self.word_length = MIN_WORD_LENGTH
        self.num_rows = DEFAULT_NUM_ROWS

    def start(self):
        self.current_guess = ""
        self.num_guesses = 0
        self.saved = False
        self.good_guesses = []
        self.current_target = all_words[random.randrange(0, len(all_words))]
        self.lgr.info(f"current target word = {self.current_target}")

    def save_record(self):
        # save all important information from this game
        if not self.saved and self.good_guesses:
            self.good_guesses.sort()
            game_record = {"TARGET WORD":self.current_target, "GOOD GUESSES":self.good_guesses}
            grfile = save_to_json(f"WordleGameRecord_{self.current_target}", game_record)
            self.lgr.info(f"Saved game record as: {grfile}")
            self.saved = True

    def check_guess(self, resp:str) -> bool:
        """Check for a good response."""
        self.lgr.debug(f"check response '{resp}':")
        self.current_guess = get_clean_word(resp)
        if self.current_guess == self.current_target:
            self.lgr.info(f"'{resp}' is the answer!")
            return True
        if self.current_guess in all_words:
            self.lgr.info(f"{self.current_guess} is a GOOD guess!")
            self.good_guesses.append(self.current_guess)
            self.num_guesses += 1
        return False
# END class GameEngine


if __name__ == "__main__":
    print(f">> Load from a UI.")
    exit(0)
