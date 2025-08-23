# main.py
import customtkinter as ctk
import sys

from main_menu import MainMenu
from character_catalogue import CharacterCatalogue
from add_edit_character import AddEditCharacter

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Stable Diffusion LoRA Organizer")
        self.geometry("800x600")

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (MainMenu, CharacterCatalogue, AddEditCharacter):
            frame_name = F.__name__
            frame = F(parent=self.container, controller=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[frame_name] = frame

        self.show_frame("MainMenu")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

        # Auto-refresh catalogue on entry
        if frame_name == "CharacterCatalogue" and hasattr(frame, "refresh_list"):
            # If the dropdown handler sets theme/dir, you can also reapply it here if needed
            frame.refresh_list()

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")  # or "Light"
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()