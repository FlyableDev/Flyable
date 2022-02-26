def make_choice(msg: str, choices: tuple[str, ...], case_sensitive=False) -> str:
    """Ask to make a choice until a valid one in entered, then return the choice"""
    if not case_sensitive:
        choices = *map(lambda c: c.lower(), choices),
    while choice := input(msg):
        if choice in choices or (not case_sensitive and choice.lower() in choices):
            return choice
        else:
            print(f"The value {choice!r} is invalid, valid values are {choices!r}. Retry")
    raise  # unreachable
