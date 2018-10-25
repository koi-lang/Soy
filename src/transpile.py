from typing import TextIO

import antlr4

from src.gen.KoiLexer import KoiLexer
from src.gen.KoiParser import KoiParser
from src.koi_transpiler import KoiTranspiler


def transpile_file(input_: str, file: TextIO = None):
    lexer = KoiLexer(antlr4.FileStream(input_))
    stream = antlr4.CommonTokenStream(lexer)
    parser = KoiParser(stream)
    tree = parser.program()

    listener = KoiTranspiler(file)
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)
