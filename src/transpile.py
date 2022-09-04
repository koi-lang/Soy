from pathlib import Path
from typing import TextIO

import antlr4
from antlr4 import CommonTokenStream

from .gen.KoiLexer import KoiLexer, InputStream
from .gen.KoiParser import KoiParser
from .koi_transpiler import KoiTranspiler


def transpile_file(path: Path, transpile_locally: bool = True, tree: str = "program", text: str = ""):
    lexer = KoiLexer(InputStream(path.read_text()))
    stream = CommonTokenStream(lexer)
    parser = KoiParser(stream)
    # tree = parser.program()
    tree = getattr(parser, tree)()

    listener = KoiTranspiler(path, transpile_locally)
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)
