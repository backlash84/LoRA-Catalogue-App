# main_menu.py
import customtkinter as ctk

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.label = ctk.CTkLabel(self, text="LoRA Organizer Main Menu", font=("Arial", 24))
        self.label.pack(pady=20)

        self.character_catalogue_button = ctk.CTkButton(
            self, text="LoRA Catalogue", width=200,
            command=lambda: controller.show_frame("CharacterCatalogue")
        )
        self.character_catalogue_button.pack(pady=10)

        self.add_edit_character_button = ctk.CTkButton(
            self, text="Add/Edit LoRA", width=200,
            command=lambda: controller.show_frame("AddEditCharacter")
        )
        self.add_edit_character_button.pack(pady=10)