import pathlib
import os

from .gen.KoiParser import KoiParser
from .gen.KoiListener import KoiListener

from .types import koi_to_c, extract_comparisons


class KoiTranspiler(KoiListener):
    def __init__(self):
        pathlib.Path("out").mkdir(exist_ok=True)
        # TODO: Change to use the Koi file name
        # TODO: Create an associating header
        self.file = open("out/main.c", "w")

        # Enviroment variables
        # SOY_HOME = A folder named "Soy". This is used to house the Soy install.
        # SOY_LIB = A folder in SOY_HOME, called "lib". This is used to house the core and standard libraries for Soy/Koi.

        self.current_line = ["#include <stdio.h>\n"]
        self.current_name = ""
        self.secondary_name = ""

        self.loop_name = "index"

    def exitLine(self, ctx:KoiParser.LineContext):
        self.file.write(" ".join(self.current_line))
        self.current_line = []

    def enterBlock(self, ctx:KoiParser.BlockContext):
        self.current_line.append("{")

        if type(ctx.parentCtx) is KoiParser.For_blockContext:
            self.current_line.append(self.secondary_name)
            self.current_line.append("=")
            self.current_line.append(self.current_name)
            self.current_line.append("[")
            self.current_line.append(self.loop_name)
            self.current_line.append("]")
            self.current_line.append(";")

    def exitBlock(self, ctx:KoiParser.BlockContext):
        self.current_line.append("}")

    def enterImport_stmt(self, ctx:KoiParser.Import_stmtContext):
        # TODO: Transpile imported Koi files and store the output in a temporary location then link to that instead
        path = os.environ.get("SOY_LIB")

        if ctx.CORE():
            path += "\\core"

        elif ctx.STANDARD():
            path += "\\std"

        for d in ctx.package_name().folders:
            path += "\\" + d.text

        last_path = path + "\\" + ctx.package_name().last.text
        if os.path.isdir(last_path):
            for f in os.listdir(last_path):
                if f.endswith("c"):
                    # TODO: Package/namespace imports
                    pass
                    # self.current_line.append("#include")
                    # self.current_line.append("\"{}\"\n".format((last_path + "\\" + f).replace("\\", "\\\\")))

        elif os.path.isfile(last_path + ".koi"):
            if os.path.isfile(last_path + ".c"):
                path += "\\" + ctx.package_name().last.text + ".c"

            self.current_line.append("#include")
            self.current_line.append("\"{}\"\n".format(path.replace("\\", "\\\\")))

    def enterFunction_block(self, ctx:KoiParser.Function_blockContext):
        self.current_line.append(ctx.returnType.getText())
        self.current_line.append(ctx.name().getText())

    def enterProcedure_block(self, ctx:KoiParser.Procedure_blockContext):
        self.current_line.append("void")
        self.current_line.append(ctx.name().getText())

    def enterParameter_set(self, ctx:KoiParser.Parameter_setContext):
        self.current_line.append("(")

        params = []

        for i in ctx.parameter():
            params.append(i.name().getText())

        for p in ctx.parameter():
            self.current_line.append(koi_to_c(p.type_().getText()))
            self.current_line.append(p.name().getText())

            if "[]" in p.type_().getText():
                self.current_line.append("[]")

            if params.index(p.name().getText()) < len(params) - 1:
                self.current_line.append(",")

    def exitParameter_set(self, ctx:KoiParser.Parameter_setContext):
        self.current_line.append(")")

    def enterName(self, ctx:KoiParser.NameContext):
        self.current_name = ctx.getText()

    def enterReturn_stmt(self, ctx:KoiParser.Return_stmtContext):
        self.current_line.append("return")
        self.current_line.append(ctx.true_value().getText())
        self.current_line.append(";")

    def enterFunction_call(self, ctx:KoiParser.Function_callContext):
        # TODO: Write the console library and add imports
        # if ctx.funcName.getText() in ["print", "println"]:
        #     self.current_line.append("printf")

        # else:
        #     self.current_line.append(ctx.funcName.getText())

        self.current_line.append(ctx.funcName.getText())

        self.current_line.append("(")

        # TODO: Resolve the order of parameters
        for v in ctx.paramValues:
            self.current_line.append(v.getText())

            if len(ctx.paramValues) > 0:
                if ctx.paramValues.index(v) < len(ctx.paramValues) - 1:
                    self.current_line.append(",")

        self.current_line.append(")")
        self.current_line.append(";")

        # if ctx.funcName.getText() == "println":
        #     self.current_line.append("printf")
        #     self.current_line.append("(")
        #     self.current_line.append("\"\\n\"")
        #     self.current_line.append(")")
        #     self.current_line.append(";")

    def enterFor_block(self, ctx:KoiParser.For_blockContext):
        # FIXME: Fix in-line lists
        self.current_name = ctx.name()[0].getText()
        self.current_line.append("int")
        self.current_line.append(self.loop_name)
        self.current_line.append(";")

        self.current_line.append(koi_to_c(ctx.type_().getText()))
        self.current_line.append(self.current_name)
        self.current_line.append(";")

        self.current_line.append("for")
        self.current_line.append("(")
        self.current_line.append(self.loop_name)
        self.current_line.append("=")
        self.current_line.append("0")

        self.current_line.append(";")

        self.current_line.append(self.loop_name)
        self.current_line.append("<")
        self.current_line.append("sizeof")
        self.current_line.append("(")

        if ctx.with_length() is None:
            size = ctx.name()[1].getText()

        else:
            size = ctx.with_length().getText()
        self.current_line.append(size)

        self.secondary_name = ctx.name()[0].getText()

        self.current_line.append(")")

        self.current_line.append("/")

        self.current_line.append("sizeof")
        self.current_line.append("*")
        self.current_line.append("(")
        self.current_line.append(size)
        self.current_line.append(")")

        self.current_line.append(";")
        self.current_line.append(self.loop_name)
        self.current_line.append("++")
        self.current_line.append(")")

    def enterLocal_asstmt(self, ctx:KoiParser.Local_asstmtContext):
        self.current_line.append(koi_to_c(ctx.type_().getText()))
        self.current_line.append(ctx.name().getText())

        if "[]" in ctx.type_().getText():
            self.current_line.append("[]")

        self.current_line.append("=")

        if ctx.true_value().getText().startswith("["):
            self.current_line.append("{")
            self.current_line.append(ctx.true_value().getText()[1:-1])
            self.current_line.append("}")

        else:
            self.current_line.append(ctx.true_value().getText())

    def exitLocal_asstmt(self, ctx:KoiParser.Local_asstmtContext):
        self.current_line.append(";")

    def enterIf_block(self, ctx:KoiParser.If_blockContext):
        self.current_line.append("if")
        # self.current_line.append("(")

        for i in extract_comparisons(ctx.compa_list(), True):
            self.current_line.append(i)

        # self.current_line.append(")")

    def enterElf_block(self, ctx:KoiParser.Elf_blockContext):
        self.current_line.append("else")
        self.current_line.append("if")
        # self.current_line.append("(")

        for i in extract_comparisons(ctx.compa_list(), True):
            self.current_line.append(i)

        # self.current_line.append(")")

    def enterElse_block(self, ctx:KoiParser.Else_blockContext):
        self.current_line.append("else")
