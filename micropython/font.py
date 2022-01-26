
class Font:
    name = ""
    color = (0, 0, 0)
    index = None

    def __init__(self, name, color, index) -> None:
        self.name = name
        self.color = color
        self.index = index
