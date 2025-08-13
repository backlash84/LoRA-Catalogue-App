import customtkinter as ctk
import os
import json
import re
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw 


CATEGORY_FOLDERS = {
    "Characters": "Character JSONs",
    "Styles": "Style JSONs",
    "Misc": "Misc JSONs",
}

COLOUR_MAP = {
    "Characters": "#343334",  # default dark
    "Styles":     "#551111",  # dark red
    "Misc":       "#113311",  # dark green
}

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")

def _load_last_category(default_value: str = "Characters") -> str:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_category", default_value)
    except Exception:
        return default_value

def _save_last_category(category: str) -> None:
    try:
        data = {"last_category": category}
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Settings] Failed to save last_category: {e}")

class AddEditCharacter(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # FIX: allow layout_container to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.layout_container = ctk.CTkFrame(self)
        self.layout_container.grid(row=0, column=0, sticky="nsew")

        self.layout_container.grid_rowconfigure(0, weight=0)  # category bar (fixed)
        self.layout_container.grid_rowconfigure(1, weight=1)  # scroll_frame (expands)
        self.layout_container.grid_rowconfigure(2, weight=0)  # bottom buttons (fixed)
        self.layout_container.grid_columnconfigure(0, weight=1)

        self.scroll_frame = ctk.CTkScrollableFrame(self.layout_container)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # ===== Internal State =====
        self.image_path = None
        self.tag_entries = []
        self.character_data = {}
        self.extra_image_rows = []  # list of tuples: (title_entry, path_var, row_frame)

        # ===== UI Layout =====
        # --- Image Display ---
        self.image_label = ctk.CTkLabel(self.scroll_frame, text="No image selected")
        self.image_label.grid(row=0, column=0, pady=(20, 10))

        self.select_image_button = ctk.CTkButton(self.scroll_frame, text="Select Image", command=self.select_image)
        self.select_image_button.grid(row=1, column=0, pady=(0, 20))

        # --- Basic Info ---
        self.name_entry = self._make_labeled_entry(self.scroll_frame, "Name", 2)
        self.file_entry = self._make_labeled_entry(self.scroll_frame, "File Name", 3)
        self.source_entry = self._make_labeled_entry(self.scroll_frame, "Source", 4)

        # --- Model Type Dropdown ---
        ctk.CTkLabel(self.scroll_frame, text="Model Type:").grid(row=5, column=0, sticky="w", padx=40)
        self.model_type_option = ctk.CTkOptionMenu(self.scroll_frame, values=["Illustrious", "SD 1.5", "SD 2.0", "SD 2.1", "SD 3.0", "SD 3.5 Medium", "SD 3.5 Large", "Pony", "SDXL", "Other"])
        self.model_type_option.set("Illustrious")
        self.model_type_option.grid(row=6, column=0, sticky="we", padx=40, pady=(0, 10))

        # --- Tags Section ---
        ctk.CTkLabel(self.scroll_frame, text="Tags:").grid(row=7, column=0, sticky="w", padx=40)
        self.tags_frame = ctk.CTkFrame(self.scroll_frame)
        self.tags_frame.grid(row=8, column=0, padx=40, pady=(0, 10), sticky="we")
        self.tags_frame.grid_remove()  # hide when empty

        self.add_tag_button = ctk.CTkButton(self.scroll_frame, text="+ Add Tag", command=self.add_tag_entry)
        self.add_tag_button.grid(row=9, column=0, padx=40, pady=(0, 20), sticky="w")

        # --- Notes ---
        ctk.CTkLabel(self.scroll_frame, text="Notes:").grid(row=10, column=0, sticky="w", padx=40)
        self.notes_box = ctk.CTkTextbox(self.scroll_frame, height=100)
        self.notes_box.grid(row=11, column=0, padx=40, pady=(0, 20), sticky="we")

        # --- Additional Images ---
        ctk.CTkLabel(self.scroll_frame, text="Additional Images:").grid(row=12, column=0, sticky="w", padx=40, pady=(10, 0))

        self.extra_images_frame = ctk.CTkFrame(self.scroll_frame)
        self.extra_images_frame.grid(row=13, column=0, sticky="we", padx=40, pady=(4, 10))
        self.extra_images_frame.grid_columnconfigure(1, weight=1)
        self.extra_images_frame.grid_remove()  # hide when empty

        self.add_extra_img_btn = ctk.CTkButton(self.scroll_frame, text="+ Add Image", command=self.add_extra_image_row)
        self.add_extra_img_btn.grid(row=14, column=0, sticky="w", padx=40, pady=(0, 20))

        # --- Bottom Buttons (stay fixed) ---
        self.button_frame = ctk.CTkFrame(self.layout_container)
        self.button_frame.grid(row=2, column=0, pady=10)

        self.new_button = ctk.CTkButton(self.button_frame, text="New", command=self.clear_form)
        self.new_button.grid(row=0, column=0, padx=10)

        self.load_button = ctk.CTkButton(self.button_frame, text="Load", command=self.load_character)
        self.load_button.grid(row=0, column=1, padx=10)

        self.save_button = ctk.CTkButton(self.button_frame, text="Save", command=self.save_character)
        self.save_button.grid(row=0, column=2, padx=10)

        self.back_button = ctk.CTkButton(self.button_frame, text="Back", command=lambda: controller.show_frame("MainMenu"))
        self.back_button.grid(row=0, column=3, padx=10)

        # --- Category dropdown (controls save/load folder) ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        last_cat = _load_last_category("Characters")
        self.category_var = ctk.StringVar(value=last_cat)

        def _set_category(cat):
            folder = CATEGORY_FOLDERS.get(cat, "Character JSONs")
            self.save_dir = os.path.join(self.base_dir, folder)
            os.makedirs(self.save_dir, exist_ok=True)
            _save_last_category(cat)  # persist on change
            self._apply_category_theme(cat)  # <— add this

        cat_row = ctk.CTkFrame(self.layout_container, fg_color="transparent")
        cat_row.grid(row=0, column=0, sticky="we", padx=10, pady=(8, 0))
        cat_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cat_row, text="Category:").grid(row=0, column=0, padx=(0,8))
        ctk.CTkOptionMenu(cat_row, values=list(CATEGORY_FOLDERS.keys()),
                          variable=self.category_var, command=_set_category).grid(row=0, column=1, sticky="w")

        # initialise folder
        _set_category(self.category_var.get())

        # --- Placeholder for when no image / load fails ---
        ph_w, ph_h = 300, 200
        ph = Image.new("RGBA", (ph_w, ph_h), (50, 50, 50, 255))
        draw = ImageDraw.Draw(ph)
        txt = "No image selected"
        try:
            bbox = draw.textbbox((0, 0), txt)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (ph_w - tw) // 2
            y = (ph_h - th) // 2
        except Exception:
            x, y = ph_w // 6, ph_h // 2 - 10
        draw.text((x, y), txt, fill=(220, 220, 220, 255))

        self.no_image = ctk.CTkImage(light_image=ph, dark_image=ph, size=(ph_w, ph_h))
        self.preview_image = self.no_image
        self.image_label.configure(image=self.preview_image, text="")
        self.image_label.image = self.preview_image  # strong ref on the widget

    def _apply_category_theme(self, cat: str):
        colour = COLOUR_MAP.get(cat, "#1a1a1a")
        # Colour the root
        self.configure(fg_color=colour)
        # Let inner containers be transparent so the root colour shows through
        try:
            self.layout_container.configure(fg_color="transparent")
            self.scroll_frame.configure(fg_color="transparent")
        except Exception:
            pass

    # ===== Helpers =====

    def _make_labeled_entry(self, parent, label_text, row):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, sticky="we", padx=40, pady=(0, 10))
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(container, text=f"{label_text}:").pack(anchor="w")
        entry = ctk.CTkEntry(container, placeholder_text=f"Enter {label_text}")
        entry.pack(fill="x")
        return entry

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")])
        if file_path:
            self.image_path = file_path
            self._load_preview_image(self.image_path)

    def add_tag_entry(self, default_value_text: str = "", default_label_text: str = ""):
        if not self.tag_entries:
            self.tags_frame.grid()  # show now that we’ll have content
        entry_frame = ctk.CTkFrame(self.tags_frame)
        entry_frame.pack(pady=6, fill="x")

        # Label (what it's for) — optional
        label_entry = ctk.CTkEntry(entry_frame, placeholder_text="Label (optional) - e.g., Camo Outfit")
        if default_label_text:
            label_entry.insert(0, default_label_text)
        label_entry.pack(fill="x")

        # Tag value
        value_entry = ctk.CTkEntry(entry_frame, placeholder_text="Tag value - text that will be copied/used")
        if default_value_text:
            value_entry.insert(0, default_value_text)
        value_entry.pack(fill="x", pady=(4, 0))

        remove_btn = ctk.CTkButton(entry_frame, text="Remove", width=80,
                                   command=lambda f=entry_frame: self._remove_tag_entry(f))
        remove_btn.pack(anchor="e", pady=(4, 0))

        self.tag_entries.append((label_entry, value_entry, entry_frame))

    def _remove_tag_entry(self, frame):
        # Remove matching tuple from self.tag_entries
        self.tag_entries = [t for t in self.tag_entries if t[2] is not frame]
        for w in frame.winfo_children():
            w.destroy()
        frame.destroy()
        if not self.tag_entries:
            self.tags_frame.grid_remove() 

    def clear_form(self):
        # Jump scroll bar to top
        try:
            self.scroll_frame._parent_canvas.yview_moveto(0)
        except Exception as e:
            print(f"[Scroll Reset] Could not reset scroll: {e}")
        self._clear_preview()
        self.image_path = None
        self.name_entry.delete(0, "end")
        self.file_entry.delete(0, "end")
        self.source_entry.delete(0, "end")
        self.model_type_option.set("Illustrious")
        self.notes_box.delete("1.0", "end")
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        self.tag_entries.clear()
        self.tags_frame.grid_remove()  # keep collapsed
        for (_, _, row) in self.extra_image_rows:
            for w in row.winfo_children():
                w.destroy()
            row.destroy()
        self.extra_image_rows.clear()
        self.extra_images_frame.grid_remove()

    def save_character(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a Name before saving.")
            return

        # Create a Windows-safe filename from Name
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "", name).strip()
        if not safe:
            messagebox.showwarning("Invalid Name", "The Name contains no valid characters for a file name.")
            return
        filename = f"{safe}.json"
        file_path = os.path.join(self.save_dir, filename)

        data = {
            "name": name,
            "file_name": self.file_entry.get(),
            "source": self.source_entry.get(),
            "model_type": self.model_type_option.get(),
            "tags": [
                {"label": le.get().strip(), "value": ve.get().strip()}
                for (le, ve, _) in self.tag_entries
                if ve.get().strip()
            ],
            "notes": self.notes_box.get("1.0", "end").strip(),
            "extra_images": [
                {"title": te.get().strip(), "image_path": pv.get().strip()}
                for (te, pv, _) in self.extra_image_rows
                if pv.get().strip()
            ],
            "image_path": self.image_path or ""
        }

        # Overwrite prompt if file exists
        if os.path.exists(file_path):
            ok = messagebox.askyesno(
                "Overwrite file?",
                f"A file named '{filename}' already exists in\n{self.save_dir}\n\nDo you want to overwrite it?"
            )
            if not ok:
                return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"[Saved] {file_path}")
            messagebox.showinfo("Saved", f"Saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save file:\n{e}")

    def load_character(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.save_dir,
            filetypes=[("JSON", "*.json")]
        )
        if not file_path:
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.clear_form()
        self.name_entry.insert(0, data.get("name", ""))
        self.file_entry.insert(0, data.get("file_name", ""))
        self.source_entry.insert(0, data.get("source", ""))
        self.model_type_option.set(data.get("model_type", "1.5"))
        self.notes_box.insert("1.0", data.get("notes", ""))

        for tag in data.get("tags", []):
            if isinstance(tag, dict):
                self.add_tag_entry(default_value_text=tag.get("value", ""), default_label_text=tag.get("label", ""))
            else:
                # fallback if any older files end up with plain strings
                self.add_tag_entry(default_value_text=str(tag), default_label_text="")

        # Extra images
        for (te, pv, row) in list(self.extra_image_rows):
            # clear any pre-existing rows (in case load after edits)
            for w in row.winfo_children():
                w.destroy()
            row.destroy()
        self.extra_image_rows.clear()

        for item in data.get("extra_images", []):
            title = item.get("title", "")
            path = item.get("image_path", "")
            self.add_extra_image_row(title_default=title, path_default=path)

        # Tags
        if data.get("tags"):
            self.tags_frame.grid()      # show if there are rows
        else:
            self.tags_frame.grid_remove()

        # Extra images
        if data.get("extra_images"):
            self.extra_images_frame.grid()
        else:
            self.extra_images_frame.grid_remove()

        # Load preview from *image_path* in JSON, not from the JSON file itself
        self.image_path = data.get("image_path", "") or None
        self._load_preview_image(self.image_path)
     
    def _load_preview_image(self, image_path: str):
        """Open image at path, scale shortest side to 300px keeping aspect, and set on label."""
        if not image_path or not os.path.exists(image_path):
            self._clear_preview()
            # clear preview if missing/invalid
            self.image_label.configure(image=None, text="No image selected")
            self.image_label.image = None
            return

        try:
            img = Image.open(image_path).convert("RGBA")
            orig_w, orig_h = img.size
            # scale so the *shortest* side is 300
            if orig_w <= orig_h:
                scale = 300 / orig_w
            else:
                scale = 300 / orig_h
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)

            self.preview_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
            self.image_label.configure(image=self.preview_image, text="")
            self.image_label.image = self.preview_image  # keep strong ref
        except Exception as e:
            # If anything goes wrong, just clear the preview gracefully
            print(f"[Preview] Failed to load image '{image_path}': {e}")
            self.image_label.configure(image=None, text="No image selected")
            self.image_label.image = None

    def add_extra_image_row(self, title_default: str = "", path_default: str = ""):
        if not self.extra_image_rows:
            self.extra_images_frame.grid()  # show now that we’ll have content
        row = ctk.CTkFrame(self.extra_images_frame)
        row.pack(fill="x", pady=6)

        # Title (optional)
        title_entry = ctk.CTkEntry(row, placeholder_text="Title (optional): e.g., Camo Outfit Close-up")
        title_entry.insert(0, title_default)
        title_entry.pack(fill="x")

        # Path row: entry + "Browse" + "Remove"
        path_row = ctk.CTkFrame(row, fg_color="transparent")
        path_row.pack(fill="x", pady=(4, 0))

        path_var = ctk.StringVar(value=path_default)
        path_entry = ctk.CTkEntry(path_row, textvariable=path_var)
        path_entry.pack(side="left", fill="x", expand=True)

        def pick():
            p = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")])
            if p:
                path_var.set(p)

        ctk.CTkButton(path_row, text="Browse", width=90, command=pick).pack(side="left", padx=6)

        def remove_row():
            self.extra_image_rows = [t for t in self.extra_image_rows if t[2] is not row]
            for w in row.winfo_children():
                w.destroy()
            row.destroy()
            if not self.extra_image_rows:
                self.extra_images_frame.grid_remove()

        ctk.CTkButton(path_row, text="Remove", width=90, fg_color="red", hover_color="#aa0000",
                      command=remove_row).pack(side="left")

        self.extra_image_rows.append((title_entry, path_var, row))

    def _clear_preview(self):
        # Set placeholder as the current preview
        self.preview_image = self.no_image
        self.image_label.configure(image=self.preview_image, text="")
        self.image_label.image = self.preview_image  # keep strong ref
        self.image_path = None