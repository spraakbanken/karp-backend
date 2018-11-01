
def cool_case(s):
    new_s = ""
    for i, c in enumerate(s):
        if i % 2 == 0:
            new_s += c.upper()
        else:
            new_s += c.lower()
    return new_s
