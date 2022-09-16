import os
from pathlib import Path

from .gen.grammar.KoiListener import KoiListener
from .gen.grammar.KoiParser import KoiParser
from .sanitize import type_to_c, extract_name, extract_comparisons, extract_paramaters


def has_ifndef(ctx):
    return type(ctx) in [
        KoiParser.Class_blockContext,
        KoiParser.Function_blockContext,
        KoiParser.Procedure_blockContext,
        KoiParser.Enum_blockContext,
        KoiParser.Struct_blockContext,
    ]


class KoiTranspiler(KoiListener):
    def __init__(self, path: Path = None, transpile_locally: bool = True):
        # TODO: Create an associating header
        Path("out").mkdir(exist_ok=True)
        self.file = Path(f"out/{path.stem}.c")

        self.transpile_locally = transpile_locally

        self.file_contents = []

        self.current_line = []
        self.current_name = ""
        self.secondary_name = ""
        self.current_class = []

        self.variable_dict = {}
        self.class_vars = []

        self.all_names = []
        self.define_name = ""

        self.imports = []

        self.in_class = False
        self.class_id = 0
        self.class_name = None

        self.in_class_init = False
        self.init_place = None

        self.quit_function = False

        self.points = []

        self.loop_name = "index"
        self.instance_name = "instance"

    def exitProgram(self, ctx: KoiParser.ProgramContext):
        with self.file.open("w") as f:
            for core in ["stdio.h", "limits.h", "stdbool.h", "stddef.h"]:
                f.write(f"#include <{core}>\n")

            # for name in self.all_names:
            #     self.file.write(f"#undef {name}\n")

            for import_ in self.imports:
                f.write(import_)

            if self.define_name != "":
                self.define_name = ""

            f.write(" ".join(" ".join(line) for line in self.file_contents))

    def exitLine(self, ctx: KoiParser.LineContext):
        # self.file.write(" ".join(self.current_line))

        self.file_contents.append(self.current_line)
        self.current_line = []

    def enterName(self, ctx: KoiParser.NameContext):
        if ctx.getText() not in self.all_names:
            if has_ifndef(ctx.parentCtx):
                self.define_name = ctx.getText().upper() + "_EXISTS"
                self.current_line.insert(0, f"\n#ifndef {self.define_name}\n")
                self.current_line.insert(1, f"#define {self.define_name}\n")
                self.all_names.append(ctx.getText())

        if ctx.THIS():
            self.current_name = "*" + self.instance_name

        else:
            self.current_name = ctx.getText()

    def enterBlock(self, ctx: KoiParser.BlockContext):
        if type(ctx.parentCtx) is not KoiParser.Class_blockContext and type(
                ctx.parentCtx) is not KoiParser.Init_blockContext:
            self.current_line.append("{")

        if type(ctx.parentCtx) is KoiParser.For_blockContext:
            self.current_line.append(self.secondary_name)
            self.current_line.append("=")
            self.current_line.append(self.current_name)
            self.current_line.append("[")
            self.current_line.append(self.loop_name)
            self.current_line.append("]")
            self.current_line.append(";")

    def exitBlock(self, ctx: KoiParser.BlockContext):
        if type(ctx.parentCtx) is not KoiParser.Class_blockContext and type(
                ctx.parentCtx) is not KoiParser.Init_blockContext:
            self.current_line.append("}")

        if has_ifndef(ctx.parentCtx):
            self.current_line.append(f"\n#endif\n")

    def enterImport_stmt(self, ctx: KoiParser.Import_stmtContext):
        # TODO: Transpile imported Koi files and store the output in a temporary location then link to that instead
        path = os.getcwd() + "/libs"  # os.environ.get("SOY_LIB")

        if ctx.CORE():
            path += "/core"

        elif ctx.STANDARD():
            path += "/std"

        for d in ctx.package_name().folders:
            path += "/" + d.text

        last_path = path + "/" + ctx.package_name().last.text

        if os.path.isdir(last_path):
            pass
            # for f in os.listdir(last_path):
            #     if f.endswith("c"):
            #         # TODO: Package/namespace imports
            #         self.current_line.append("#include")
            #         self.current_line.append("\"{}\"\n".format((last_path + "/" + f).replace("/", "//")))

        elif os.path.isfile(last_path + ".koi"):
            # A file for C exists with the same name, must be a native thing ¯\_(ツ)_/¯
            # TODO: Change this to acknowledge a native function if there is one, and have that point to the C file
            if os.path.isfile(last_path + ".c"):
                path += "/" + ctx.package_name().last.text + ".c"

            # There's no C file, it must be a Koi file
            else:
                path += "/" + ctx.package_name().last.text + ".koi"

                from .transpile import transpile_file
                transpile_file(Path(path))

                path = ctx.package_name().last.text + ".c"

            import_path = "#include "

            # self.current_line.append("#include")

            if self.transpile_locally:
                # self.current_line.append("\"{}\"\n".format(path.replace("/", "//")))
                import_path += "\"{}\"\n".format(path.replace("/", "//"))

            else:
                # self.current_line.append("\"{}\"\n".format("".join(path.split("/")[1:])))
                import_path += "\"{}\"\n".format("".join(path.split("/")[1:]))

            self.imports.append(import_path)

    def enterFunction_block(self, ctx: KoiParser.Function_blockContext):
        self.current_line.append(ctx.returnType.getText())

        self.current_name = ctx.name().getText()
        if self.in_class:
            self.current_name = self.secondary_name + "_" + self.current_name

        self.current_line.append(self.current_name)

    def enterProcedure_block(self, ctx: KoiParser.Procedure_blockContext):
        self.current_line.append("void")

        self.current_name = ctx.name().getText()
        if self.in_class:
            self.current_name = self.secondary_name + "_" + self.current_name

        self.current_line.append(self.current_name)

    def enterParameter_set(self, ctx: KoiParser.Parameter_setContext):
        self.current_line.append("(")

        params = []

        for i in ctx.parameter():
            params.append(i.name().getText())

        if self.in_class:
            self.current_line.append("const")
            self.current_line.append(self.secondary_name)
            self.current_line.append("*")
            self.current_line.append(self.instance_name)

            if len(params) > 0:
                self.current_line.append(",")

        for p in ctx.parameter():
            self.current_line.append(type_to_c(p.type_().getText()))
            self.current_line.append(p.name().getText())

            if "[]" in p.type_().getText():
                self.current_line.append("[]")

            if params.index(p.name().getText()) < len(params) - 1:
                self.current_line.append(",")

    def exitParameter_set(self, ctx: KoiParser.Parameter_setContext):
        self.current_line.append(")")

    def enterReturn_stmt(self, ctx: KoiParser.Return_stmtContext):
        self.current_line.append("return")

        if ctx.true_value().value().getText() == "this":
            self.current_line.append("*" + self.instance_name)

        else:
            self.current_line.append(ctx.true_value().getText())

        self.current_line.append(";")

    def enterFunction_call(self, ctx: KoiParser.Function_callContext):
        # print(ctx.getText(), self.variable_dict)
        # if ctx.funcName.getText() in ["print", "println"]:
        #     self.current_line.append("printf")

        # else:
        #     self.current_line.append(ctx.funcName.getText())

        class_call = False

        if self.quit_function:
            self.quit_function = False
            return

        if type(ctx.parentCtx) is KoiParser.ValueContext:
            return

        for c in ctx.method_call():
            name = c.funcName.getText()

            if self.variable_dict.get(name.split(".")[0]):
                class_call = True

            if class_call:
                split = name.split(".")
                class_name = split[0]
                name = self.variable_dict[class_name] + "_" + name.split(".")[-1]

            self.current_line.append(name)

            params = extract_paramaters(c.call_parameter_set(), True)

            if class_call:
                params.insert(1, " ".join(["&" + class_name, ","]))

            for p in params:
                self.current_line.append(p)

            self.current_line.append(";")

        # if ctx.funcName.getText() == "println":
        #     self.current_line.append("printf")
        #     self.current_line.append("(")
        #     self.current_line.append("\"/n\"")
        #     self.current_line.append(")")
        #     self.current_line.append(";")

    def enterFor_block(self, ctx: KoiParser.For_blockContext):
        if ctx.with_length() is None:
            size = ctx.name()[1].getText()

        else:
            size = ctx.with_length().getText()

        # FIXME: Fix in-line lists
        self.current_name = ctx.name()[0].getText()
        self.current_line.append("int")
        self.current_line.append(self.loop_name)
        self.current_line.append(";")

        self.current_line.append(
            f"size_t length = (&{size})[1] - {size};"
        )

        self.current_line.append(type_to_c(ctx.type_().getText()))
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
        self.current_line.append("length")

        self.secondary_name = ctx.name()[0].getText()

        self.current_line.append(";")
        self.current_line.append(self.loop_name)
        self.current_line.append("++")
        self.current_line.append(")")

    def enterLocal_asstmt(self, ctx: KoiParser.Local_asstmtContext):
        assignment = []

        my_type = ""

        if ctx.type_():
            assignment.append(type_to_c(ctx.type_().getText()))
            self.variable_dict[ctx.name().getText()] = type_to_c(ctx.type_().getText())

            my_type = ctx.type_().getText()

        assignment.append(extract_name(ctx.name().getText(), my_type, self.instance_name))

        if ctx.true_value():
            if ctx.true_value().value().function_call():
                self.quit_function = True

            if ctx.true_value().value().class_new():
                self.class_name = ctx.name().getText()

                assignment.append(";")

            else:
                if ctx.type_() and "[]" in ctx.type_().getText():
                    assignment.append("[]")

                    assignment.append("=")

            # if ctx.true_value().value().function_call():
            #     assignment.append("=")
            #     assignment.append(ctx.true_value().getText().replace("this.", self.instance_name + "->"))

            if ctx.true_value().getText().startswith("["):
                assignment.append("{")
                assignment.append(extract_name(ctx.true_value().getText()[1:-1], my_type))
                assignment.append("}")

            else:
                if not ctx.true_value().value().class_new():
                    assignment.append("=")
                    assignment.append(extract_name(ctx.true_value().getText(), my_type))
                    assignment.append(";")

        if self.in_class_init:
            assignment.append(";")
            self.class_vars.append(" ".join(assignment))
            self.current_class.insert(self.init_place, " ".join(assignment).split("=")[0] + ";")

        else:
            self.current_line.append(" ".join(assignment))

    def exitLocal_asstmt(self, ctx: KoiParser.Local_asstmtContext):
        if not self.in_class_init:
            self.current_line.append(";")

    def enterIf_block(self, ctx: KoiParser.If_blockContext):
        self.current_line.append("if")
        # self.current_line.append("(")

        for i in extract_comparisons(ctx.compa_list(), True):
            self.current_line.append(i)

        # self.current_line.append(")")

    def enterElf_block(self, ctx: KoiParser.Elf_blockContext):
        self.current_line.append("else")
        self.current_line.append("if")
        # self.current_line.append("(")

        for i in extract_comparisons(ctx.compa_list(), True):
            self.current_line.append(i)

        # self.current_line.append(")")

    def enterElse_block(self, ctx: KoiParser.Else_blockContext):
        self.current_line.append("else")

    def enterClass_block(self, ctx: KoiParser.Class_blockContext):
        self.current_class.append("typedef")
        self.current_class.append("struct")
        self.current_class.append("{")

        self.init_place = len(self.current_class)

        self.current_class.append("}")
        self.current_class.append(ctx.name().getText())
        self.current_class.append(";")

        self.secondary_name = ctx.name().getText()
        self.in_class = True

    def exitClass_block(self, ctx: KoiParser.Class_blockContext):
        self.in_class = False

    def enterConstructor_block(self, ctx: KoiParser.Constructor_blockContext):
        self.current_line.append("void")
        self.current_line.append(self.secondary_name + "_new")

    def enterClass_new(self, ctx: KoiParser.Class_newContext):
        # TODO: Pass returned information to the next chained method
        if self.class_name:
            instance_name = self.class_name

        else:
            self.current_line.append(ctx.className.getText())
            instance_name = "c" + str(self.class_id)
            self.current_line.append("c" + str(self.class_id))
            self.current_line.append(";")

            self.class_id += 1

        self.current_line.append(ctx.className.getText() + "_init" + "(&" + instance_name + ")")
        self.current_line.append(";")
        self.current_line.append(ctx.className.getText() + "_new" + "(&" + instance_name + ")")
        self.current_line.append(";")

        for c in ctx.method_call():
            self.current_line.append(
                ctx.className.getText() + "_" + c.getText().split("(")[0] + "(&" + instance_name + "," + "".join(
                    extract_paramaters(c.call_parameter_set(), False)) + ")")
            self.current_line.append(";")

    def enterInit_block(self, ctx: KoiParser.Init_blockContext):
        self.in_class_init = True

    def exitInit_block(self, ctx: KoiParser.Init_blockContext):
        self.current_line.append(" ".join(self.current_class))

        self.current_line.append("void")
        self.current_line.append(self.secondary_name + "_init")
        self.current_line.append("(")
        self.current_line.append(self.secondary_name)
        self.current_line.append("*")
        self.current_line.append(self.instance_name)
        self.current_line.append(")")
        self.current_line.append("{")

        new_vars = []
        for i in self.class_vars:
            split = i.replace("*", "").split(" ")
            new_vars.append(self.instance_name)
            new_vars.append("->")
            new_vars.append(" ".join(split[1:-1]))
            new_vars.append(";")

        self.current_line.append(" ".join(new_vars))
        self.current_line.append("}")

        self.current_class = []
        self.in_class_init = False

    def enterWhen_block(self, ctx: KoiParser.When_blockContext):
        self.current_line.append("switch")
        self.current_line.append("(")
        self.current_line.append(ctx.true_value().getText())
        self.current_line.append(")")
        self.current_line.append("{")

    def exitWhen_block(self, ctx: KoiParser.When_blockContext):
        self.current_line.append("}")

    def enterIs_block(self, ctx: KoiParser.Is_blockContext):
        self.current_line.append("case")

        if ctx.half_compa():
            if ctx.half_compa().comp.text == "<" or ctx.half_compa().comp.text == "<=":
                self.current_line.append("INT_MIN")
                self.current_line.append("...")
                self.current_line.append(ctx.half_compa().getText().replace("<", "").replace("=", ""))

                if "=" not in ctx.half_compa().comp.text:
                    self.current_line.append("-")
                    self.current_line.append("1")

            elif ctx.half_compa().comp.text == ">" or ctx.half_compa().comp.text == ">=":
                self.current_line.append(ctx.half_compa().getText().replace(">", "").replace("=", ""))

                if "=" not in ctx.half_compa().comp.text:
                    self.current_line.append("+")
                    self.current_line.append("1")

                self.current_line.append("...")
                self.current_line.append("INT_MAX")

        else:
            self.current_line.append(ctx.true_value().getText())

        self.current_line.append(":")

    def exitIs_block(self, ctx: KoiParser.Is_blockContext):
        self.current_line.append("break")
        self.current_line.append(";")

    def enterWhen_else(self, ctx: KoiParser.When_elseContext):
        self.current_line.append("default")
        self.current_line.append(":")

    def exitWhen_else(self, ctx: KoiParser.When_elseContext):
        self.current_line.append("break")
        self.current_line.append(";")

    def enterEnum_block(self, ctx: KoiParser.Enum_blockContext):
        # TODO: Move enum values to their own "scope"
        self.current_line.append("typedef")
        self.current_line.append("enum")
        self.current_line.append(ctx.name().getText())
        self.current_line.append("{")

        for i in ctx.ID():
            if i.getText() not in self.all_names:
                self.all_names.append(i.getText())

            self.current_line.append(i.getText())
            self.current_line.append(",")

        self.current_line.append("}")
        self.current_line.append(ctx.name().getText())
        self.current_line.append(";")

    def exitEnum_block(self, ctx:KoiParser.Enum_blockContext):
        self.current_line.append(f"\n#endif\n")

    def enterStruct_block(self, ctx: KoiParser.Struct_blockContext):
        self.current_line.append("typedef")
        self.current_line.append("struct")
        self.current_line.append(ctx.name().getText())
        self.current_line.append("{")

        for i in ctx.struct_set():
            self.current_line.append(type_to_c(i.type_().getText()))
            self.current_line.append(i.name().getText())
            self.current_line.append(";")

        self.current_line.append("}")
        self.current_line.append(ctx.name().getText())
        self.current_line.append(";")

    def exitStruct_block(self, ctx:KoiParser.Struct_blockContext):
        self.current_line.append(f"\n#endif\n")
