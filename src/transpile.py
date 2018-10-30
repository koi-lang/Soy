from typing import TextIO

import antlr4

from src.gen.KoiLexer import KoiLexer, InputStream
from src.gen.KoiParser import KoiParser
from src.koi_transpiler import KoiTranspiler


def transpile_file(file_name: str, file: TextIO = None, transpile_locally: bool = True, tree: str = "program", text: str = ""):
    if file_name is not None:
        lexer = KoiLexer(antlr4.FileStream(file_name))

    else:
        lexer = KoiLexer(InputStream(text))

    stream = antlr4.CommonTokenStream(lexer)
    parser = KoiParser(stream)
    # tree = parser.program()
    tree = getattr(parser, tree)()

    listener = KoiTranspiler(file, transpile_locally)
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)
