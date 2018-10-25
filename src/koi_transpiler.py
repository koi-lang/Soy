import pathlib
import os
from typing import TextIO

from .gen.KoiParser import KoiParser
from .gen.KoiListener import KoiListener

from .types import koi_to_c, extract_comparisons


class KoiTranspiler(KoiListener):
    def __init__(self, file: TextIO = None, transpile_locally: bool = True):
        # TODO: Change to use the Koi file name
        # TODO: Create an associating header
        if not file:
            pathlib.Path("out").mkdir(exist_ok=True)
            self.file = open("out/main.c", "w")

        else:
            self.file = file

        self.transpile_locally = transpile_locally

        # Enviroment variables
        # SOY_HOME = A folder named "Soy". This is used to house the Soy install.
        # SOY_LIB = A folder in SOY_HOME, called "lib". This is used to house the core and standard libraries for Soy/Koi.

        self.current_line = ["#include <stdio.h>\n"]
        self.current_name = ""
        self.secondary_name = ""

        self.in_class = False
        self.class_id = 0

        self.loop_name = "index"

    def exitProgram(self, ctx:KoiParser.ProgramContext):
        self.file.close()

    def exitLine(self, ctx:KoiParser.LineContext):
        self.file.write(" ".join(self.current_line))
        self.current_line = []

    def enterBlock(self, ctx:KoiParser.BlockContext):
        if type(ctx.parentCtx) is not KoiParser.Class_blockContext:
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
        if type(ctx.parentCtx) is not KoiParser.Class_blockContext:
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
            pass
            # for f in os.listdir(last_path):
            #     if f.endswith("c"):
            #         # TODO: Package/namespace imports
            #         self.current_line.append("#include")
            #         self.current_line.append("\"{}\"\n".format((last_path + "\\" + f).replace("\\", "\\\\")))

        elif os.path.isfile(last_path + ".koi"):
            # A file for C exists with the same name, must be a native thing ¯\_(ツ)_/¯
            # TODO: Change this to acknowledge a native function if there is one, and have that point to the C file
            if os.path.isfile(last_path + ".c"):
                path += "\\" + ctx.package_name().last.text + ".c"

            # There's no C file, it must be a Koi file
            else:
                if self.transpile_locally:
                    new_path = "\\".join(path.split("\\")[0:-1]) + "\\" + path.split("\\")[-1] + "\\_compiled"
                    pathlib.Path(new_path).mkdir(exist_ok=True)

                else:
                    new_path = "out"

                with open(new_path + "\\" + ctx.package_name().last.text + ".c", "w") as comp_file:
                    from .transpile import transpile_file

                    transpile_file(path + "\\" + ctx.package_name().last.text + ".koi", comp_file)

                    path = comp_file.name

            self.current_line.append("#include")

            if self.transpile_locally:
                self.current_line.append("\"{}\"\n".format(path.replace("\\", "\\\\")))

            else:
                self.current_line.append("\"{}\"\n".format("".join(path.split("\\")[1:])))

    def enterFunction_block(self, ctx:KoiParser.Function_blockContext):
        self.current_line.append(ctx.returnType.getText())
        self.current_line.append(ctx.name().getText())

    def enterProcedure_block(self, ctx:KoiParser.Procedure_blockContext):
        self.current_line.append("void")

        self.current_name = ctx.name().getText()
        if self.in_class:
            self.current_name = self.secondary_name + "_" + self.current_name

        self.current_line.append(self.current_name)

    def enterParameter_set(self, ctx:KoiParser.Parameter_setContext):
        self.current_line.append("(")

        params = []

        for i in ctx.parameter():
            params.append(i.name().getText())

        if self.in_class:
            self.current_line.append("const")
            self.current_line.append(self.secondary_name)
            self.current_line.append("*")
            self.current_line.append("shape")

            if len(params) > 0:
                self.current_line.append(",")

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

        self.current_line.append(ctx.method_call().funcName.getText())

        self.current_line.append("(")

        # TODO: Resolve the order of parameters
        for v in ctx.method_call().call_parameter_set().paramValues:
            self.current_line.append(v.getText())

            if len(ctx.method_call().call_parameter_set().paramValues) > 0:
                if ctx.method_call().call_parameter_set().paramValues.index(v) < len(ctx.method_call().call_parameter_set().paramValues) - 1:
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

        if ctx.true_value().value().function_call():
            return

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

    def enterClass_block(self, ctx:KoiParser.Class_blockContext):
        self.current_line.append("typedef")
        self.current_line.append("struct")
        self.current_line.append("{")

        self.current_line.append("}")
        self.current_line.append(ctx.name().getText())
        self.current_line.append(";")

        self.secondary_name = ctx.name().getText()
        self.in_class = True

    def exitClass_block(self, ctx:KoiParser.Class_blockContext):
        self.in_class = False

    def enterConstructor_block(self, ctx:KoiParser.Constructor_blockContext):
        self.current_line.append("void")
        self.current_line.append(self.current_name + "_new")

    def enterClass_new(self, ctx:KoiParser.Class_newContext):
        # TODO: Allow classes to be bound to variables
        # TODO: Pass through the parameters
        # TODO: Allow chaining method calls
        self.current_line.append(ctx.className.getText())
        instance_name = "c" + str(self.class_id)
        self.current_line.append("c" + str(self.class_id))
        self.current_line.append(";")

        self.current_line.append(ctx.className.getText() + "_new" + "(&" + instance_name + ")")
        self.current_line.append(";")


