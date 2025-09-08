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
__updated__ = "2025-09-08"

import random
from sys import path, argv
from abc import ABC, abstractmethod
from argparse import ArgumentParser
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
        self.last_guess = ""
        self.pangrams = pangrams.pangrams
        self._lgr.info(f"type(self.pangrams) = {type(self.pangrams)}")
        self._lgr.info(f"len(self.pangrams) = {len(self.pangrams)}")
        self.allwords = all_spellbee_words.all_sb_words
        self._lgr.info(f"type(allwords) = {type(self.allwords)}")
        self._lgr.info(f"len(allwords) = {len(self.allwords)}")

    def start_game(self):
        self.current_target = self.pangrams[random.randrange(0,len(self.pangrams))]
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
        self.last_guess = formatted_string.rstrip().lstrip()
        return self.last_guess

    def check_response(self, resp:str):
        pass

    def accept_response(self, resp:str):
        pass
# END class GameEngine


log_control = MhsLogger(GameEngine.__name__, con_level = DEFAULT_LOG_LEVEL)
