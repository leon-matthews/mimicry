

class MimicryError(RuntimeError):
    pass


class NotAFolder(MimicryError):
    pass


class NotUnderRoot(MimicryError):
    """
    The metadata database (say *that* quickly 17 times) should only operate
    on paths under its root folder.
    """
    pass
