from typing import Optional, Dict, Any, List
import re
from loguru import logger
import ciphey
from ciphey.iface import registry


@registry.register
class MorseCode(ciphey.iface.Decoder[str, str]):
    # A priority list for char/word boundaries
    BOUNDARIES = {" ": 1, "/": 2, "\n": 3, ".": -1, "-": -1}
    MAX_PRIORITY = 3
    ALLOWED = {".", "-", " ", "/", "\n"}
    MORSE_CODE_DICT: Dict[str, str]
    MORSE_CODE_DICT_INV: Dict[str, str]

    @staticmethod
    def getTarget() -> str:
        return "morse"

    def decode(self, text: str) -> Optional[str]:
        # Trim end
        while text[-1] in self.BOUNDARIES:
            text = text[:-1]

        logger.trace("Attempting morse code")

        char_boundary = word_boundary = None

        char_boundary = word_boundary = None
        char_priority = word_priority = 0
        # Custom loop allows early break
        for i in text:
            i_priority = self.BOUNDARIES.get(i)
            if i_priority is None:
                logger.trace(f"Non-morse char '{i}' found")
                return None

            if i_priority <= char_priority or i == char_boundary or i == word_boundary:
                continue
            # Default to having a char boundary over a word boundary
            if (
                i_priority > word_priority
                and word_boundary is None
                and char_boundary is not None
            ):
                word_priority = i_priority
                word_boundary = i
                continue
            char_priority = i_priority
            char_boundary = i

        logger.trace(
            f"'Char boundary is '{char_boundary}', and word boundary is '{word_boundary}'"
        )

        result = ""

        for word in text.split(word_boundary) if word_boundary else [text]:
            logger.trace(f"Attempting to decode word {word}")
            for char in word.split(char_boundary):
                try:
                    m = self.MORSE_CODE_DICT_INV[char]
                except KeyError:
                    logger.trace(f"Invalid codeword '{word}' found")
                    return None
                result = result + m
            # after every word add a space
            result = result + " "
        if len(result) == 0:
            logger.trace(f"Morse code failed to match")
            return None
        # Remove trailing space
        result = result[:-1]
        logger.debug(f"Morse code successful, returning {result}")
        return result.strip().upper()

    @staticmethod
    def getParams() -> Optional[Dict[str, ciphey.iface.ParamSpec]]:
        return {
            "dict": ciphey.iface.ParamSpec(
                desc="The morse code dictionary to use",
                req=False,
                default="cipheydists::translate::morse",
            )
        }

    @staticmethod
    def getName() -> str:
        return "morse"

    @staticmethod
    def priority() -> float:
        return 0.05

    def __init__(self, config: ciphey.iface.Config):
        super().__init__(config)
        self.MORSE_CODE_DICT = config.get_resource(
            self._params()["dict"], ciphey.iface.WordList
        )
        self.MORSE_CODE_DICT_INV = {v: k for k, v in self.MORSE_CODE_DICT.items()}
