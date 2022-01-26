import os
from font import Font


class ConfigController:

    def __init__(self) -> None:
        self.read_all_profiles_into_memory()
        self.read_current_font()
        pass

    def read_all_profiles_into_memory(self):
        print('SD Card contains:{}'.format(os.listdir()))
        os.chdir("fonts")
        self.fonts = []
        for i, font in enumerate(os.listdir()):
            os.chdir(font)
            with open(self.color_filename, "r") as color_file:
                color_bytes = eval(color_file.read())
                self.fonts.append(Font(font, color_bytes, i))
            os.chdir("..")
        print(self.fonts)

    def get_filename(self, filename):
        return self.base_dir + "/" + self.current_font.name + "/" + filename

    base_dir = "/fonts"
    color_filename = "color.txt"
    font_filename = "font.wav"
    open_filename = "open.wav"
    idle_filename = "idle.wav"
    close_filename = "close.wav"
    hit_filename = "hit.wav"
    lock_filename = "lock.wav"
    unlock_filename = "unlock.wav"
    move_filename = "move.wav"

    current_font_index = 0
    current_font = None
    fonts = []

    def set_next_font(self):
        self.current_font_index = (
            self.current_font_index+1
        ) % len(self.fonts)
        self.current_font = self.fonts[self.current_font_index]
        pass

    def set_previous_font(self):
        color_count = len(self.fonts)
        self.current_font_index = (
            self.current_font_index+color_count-1
        ) % color_count
        self.current_font = self.fonts[self.current_font_index]
        pass

    def read_current_font(self):
        self.current_font = self.fonts[self.current_font_index]
        pass
