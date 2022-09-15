from pathlib import Path

import antlr4
from antlr4 import CommonTokenStream

from .gen.grammar.KoiLexer import KoiLexer, InputStream
from .gen.grammar.KoiParser import KoiParser
from .koi_transpiler import KoiTranspiler


def transpile_file(path: Path, transpile_locally: bool = True, tree: str = "program"):
    lexer = KoiLexer(InputStream(path.read_text()))
    stream = CommonTokenStream(lexer)
    parser = KoiParser(stream)
    # tree = parser.program()
    tree = getattr(parser, tree)()

    listener = KoiTranspiler(path, transpile_locally)
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)
