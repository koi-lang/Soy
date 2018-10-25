from typing import List

from .gen.KoiParser import KoiParser


def koi_to_c(type_: str) -> str:
    # TODO: Finish of the converted types
    if type_.startswith("str"):
        return "char*"

    else:
        return type_.split("[]")[0]


def extract_comparisons(ctx: KoiParser.Compa_listContext, parenthesis: bool = False) -> List[str]:
    comparisons = []

    if parenthesis:
        comparisons.append("(")

    for i, e in enumerate(ctx.comparisons):
        if parenthesis:
            comparisons.append("(")

        comparisons.append(e.getText())

        if parenthesis:
            comparisons.append(")")

        if ctx.settings and len(ctx.settings) > i:
            comparisons.append(ctx.settings[i].text)

    if parenthesis:
        comparisons.append(")")

    return comparisons


def extract_paramaters(ctx: KoiParser.Call_parameter_setContext, parenthesis: bool = False):
    parameters = []

    if parenthesis:
        parameters.append("(")

    # TODO: Resolve the order of parameters
    for v in ctx.paramValues:
        parameters.append(v.getText())

        if len(ctx.paramValues) > 0:
            if ctx.paramValues.index(v) < len(ctx.paramValues) - 1:
                parameters.append(",")

    if parenthesis:
        parameters.append(")")

    return parameters

