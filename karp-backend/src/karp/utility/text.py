def noswedish(s: str) -> str:
    result = ""
    for c in s:
        if c == "å":
            result += "aa"
        elif c == "ä":
            result += "ae"
        elif c == "ö":
            result += "oe"
        elif c == "Å":
            result += "Aa"
        elif c == "Ä":
            result += "Ae"
        elif c == "Ö":
            result += "Oe"
        else:
            result += c

    return result
