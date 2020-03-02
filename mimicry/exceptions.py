

class MimicryError(RuntimeError):
    pass


class NotAFile(MimicryError):
    pass


class NotAFolder(MimicryError):
    pass


class NotUnderRoot(MimicryError):
    """
    The metadata database (say *that* quickly 17 times) should only operate
    on paths found under its root folder.
    """
    pass
