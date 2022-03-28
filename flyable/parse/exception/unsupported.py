class FlyableUnsupported(BaseException):
    """
    This exception is used to notify the adapter that Flyable will not provide an implementation for that use case
    and must rely on Python bytecode to run the function
    """

    def __init__(self):
        super()
