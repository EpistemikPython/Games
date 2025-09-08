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
__updated__ = "2025-08-20"

from sys import path, argv
from abc import ABC, abstractmethod
from argparse import ArgumentParser
path.append("/home/marksa/git/Python/utils")
from mhsUtils import *
from mhsLogging import *

TARGET_WORD_FILE = "/home/marksa/Documents/Words/input/pangrams.py"
REFERENCE_WORD_FILE = "/home/marksa/Documents/Words/input/spellbee_words.json"
MIN_WORD_LENGTH = 4
MAX_WORD_LENGTH = 21


class GameEngine:
    def __init__(self):
        self.required_letter = ''
        self.surround_letters = ""
        self.current_target = ""
        self.last_guess = ""

    def get_target_word(self):
        pass
    
    def format_response(self, resp:str) -> str:
        # remove non-letters, capitalize and return
        formatted_string = ""
        for c in resp:
            if str.isalpha(c):
                formatted_string += c.upper()
        self.last_guess = formatted_string
        return formatted_string.rstrip().lstrip()

    def check_response(self, resp:str):
        pass

    def accept_response(self, resp:str):
        pass

# END class GameEngine
