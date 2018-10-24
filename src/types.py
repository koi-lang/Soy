def koi_to_c(type_: str) -> str:
    # TODO: Finish of the converted types
    if type_.startswith("str"):
        return "char*"

    else:
        return type_.split("[]")[0]
