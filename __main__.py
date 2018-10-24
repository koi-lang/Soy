import antlr4

from src.gen.KoiLexer import KoiLexer
from src.gen.KoiParser import KoiParser
from src.koi_transpiler import KoiTranspiler

if __name__ == "__main__":
    lexer = KoiLexer(antlr4.FileStream("examples/src/command_line.koi"))
    stream = antlr4.CommonTokenStream(lexer)
    parser = KoiParser(stream)
    tree = parser.program()

    listener = KoiTranspiler()
    walker = antlr4.ParseTreeWalker()
    walker.walk(listener, tree)
