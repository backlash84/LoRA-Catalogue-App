# character_catalogue.py
import customtkinter as ctk
import os, json, re
from PIL import Image
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont

CATEGORY_FOLDERS = {
    "Characters": "Character JSONs",
    "Styles": "Style JSONs",
    "Misc": "Misc JSONs",
}

COLOUR_MAP = {
    "Characters": "#343334",
    "Styles":     "#551111",
    "Misc":       "#113311",
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

class CharacterCatalogue(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_file_path = None

        # --- Data dir (same as AddEditCharacter) ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        last_cat = _load_last_category("Characters")
        self.category_var = ctk.StringVar(value=last_cat)

        # Initialise save_dir immediately so refresh_list() has a folder
        initial_folder = CATEGORY_FOLDERS.get(last_cat, "Character JSONs")
        self.save_dir = os.path.join(self.base_dir, initial_folder)
        os.makedirs(self.save_dir, exist_ok=True)

        def _set_category(cat):
            folder = CATEGORY_FOLDERS.get(cat, "Character JSONs")
            self.save_dir = os.path.join(self.base_dir, folder)
            os.makedirs(self.save_dir, exist_ok=True)
            _save_last_category(cat)  # persist on change
            self._apply_category_theme(cat)
            self.refresh_list()

        cat_bar = ctk.CTkFrame(self)
        cat_bar.grid(row=0, column=0, columnspan=2, sticky="we", padx=10, pady=(8, 0))
        cat_bar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(cat_bar, text="Category:").grid(row=0, column=0, padx=(0,8))
        ctk.CTkOptionMenu(cat_bar, values=list(CATEGORY_FOLDERS.keys()),
                          variable=self.category_var, command=_set_category).grid(row=0, column=1)

        self.selected_button = None
        self.entries = []   # list of (filepath, data)

        # --- Layout: two columns ---
        self.grid_rowconfigure(0, weight=0)  # category bar (fixed)
        self.grid_rowconfigure(1, weight=1)  # main content (expands)
        self.grid_columnconfigure(0, weight=0)  # list panel
        self.grid_columnconfigure(1, weight=1)  # details panel

        # ===== Left: list panel =====
        self.list_panel = ctk.CTkFrame(self, fg_color="transparent")   
        self.list_panel.grid(row=1, column=0, sticky="nsw", padx=(10, 5), pady=10)

        # Optional header + refresh
        header = ctk.CTkFrame(self.list_panel)
        header.grid(row=0, column=0, sticky="we", pady=(0, 5))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Characters", font=("Arial", 16)).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Refresh", width=80, command=self.refresh_list).grid(row=0, column=1, sticky="e", padx=(8,0))

        self.list_scroll = ctk.CTkScrollableFrame(self.list_panel, width=260)
        self.list_scroll.grid(row=1, column=0, sticky="nswe")
        self.list_panel.grid_rowconfigure(1, weight=1)

        self.details_container = ctk.CTkFrame(self, fg_color="transparent")  # <— transparent
        self.details_container.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.details_container.grid_columnconfigure(0, weight=1)
        self.details_container.grid_rowconfigure(0, weight=0)  # top bar
        self.details_container.grid_rowconfigure(1, weight=1)  # scrollable info

        # Top bar (Back button stays fixed, not scrollable)
        topbar = ctk.CTkFrame(self.details_container, fg_color="transparent")
        topbar.grid(row=0, column=0, sticky="we", padx=0, pady=(0, 6))
        ctk.CTkButton(topbar, text="Back",
                      command=lambda: controller.show_frame("MainMenu")
                     ).pack(side="right", padx=10, pady=10)

        # Scrollable details panel
        self.details = ctk.CTkScrollableFrame(self.details_container)
        self.details.grid(row=1, column=0, sticky="nsew")
        self.details.grid_columnconfigure(0, weight=1)

        # Image preview (inside scrollable frame)
        self.image_label = ctk.CTkLabel(self.details, text="No image")
        self.image_label.grid(row=0, column=0, pady=(10, 10))

        # Simple field rows (inside scrollable frame)
        self.name_var = ctk.StringVar(value="")
        self.file_var = ctk.StringVar(value="")
        self.source_var = ctk.StringVar(value="")
        self.type_var = ctk.StringVar(value="")
        self.tags_var = ctk.StringVar(value="")

        self._row(self.details, "Name:", self.name_var, 1)
        self._row(self.details, "File Name:", self.file_var, 2)
        self._row(self.details, "Source:", self.source_var, 3)
        self._row(self.details, "Model Type:", self.type_var, 4)
        ctk.CTkLabel(self.details, text="Tags:").grid(row=5, column=0, sticky="w", padx=10)

        # container to hold one button per tag (one per row)
        self.tags_container = ctk.CTkFrame(self.details, fg_color="transparent")
        self.tags_container.grid(row=6, column=0, sticky="we", padx=10, pady=(0,10))
        self.details.grid_rowconfigure(6, weight=0)

        ctk.CTkLabel(self.details, text="Notes:").grid(row=7, column=0, sticky="w", padx=10)
        self.notes_box = ctk.CTkTextbox(self.details, height=160, wrap="word")
        self.notes_box.grid(row=8, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.details.grid_rowconfigure(8, weight=1)

        # Additional Images (display)
        ctk.CTkLabel(self.details, text="Additional Images:").grid(row=9, column=0, sticky="w", padx=10, pady=(8, 0))

        self.extra_images_container = ctk.CTkFrame(self.details, fg_color="transparent")
        self.extra_images_container.grid(row=10, column=0, sticky="we", padx=10, pady=(4, 10))
        self.extra_images_container.grid_columnconfigure(0, weight=1)

        # DELETE button under notes
        self.delete_button = ctk.CTkButton(
            self.details,
            text="DELETE",
            fg_color="red",
            hover_color="#aa0000",
            font=("Arial", 16, "bold"),
            command=self.delete_selected_character
        )
        self.delete_button.grid(row=11, column=0, sticky="we", padx=10, pady=(6, 12))

        # --- Placeholder image for "No image found" ---
        ph_w, ph_h = 300, 200
        ph = Image.new("RGBA", (ph_w, ph_h), (50, 50, 50, 255))
        draw = ImageDraw.Draw(ph)
        text = "No image found"

        # Use textbbox (works on modern Pillow); fall back to fixed position if it fails
        try:
            bbox = draw.textbbox((0, 0), text)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (ph_w - tw) // 2
            y = (ph_h - th) // 2
        except Exception:
            x = ph_w // 6
            y = ph_h // 2 - 10

        draw.text((x, y), text, fill=(220, 220, 220, 255))
        self.no_image = ctk.CTkImage(light_image=ph, dark_image=ph, size=(ph_w, ph_h))

        # State for image
        self.preview_image = None
        # set initial folder + build list
        _set_category(self.category_var.get())
        self.refresh_list()  # now save_dir and list_scroll both exist

    def _row(self, parent, label, var, row):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, sticky="we", padx=10, pady=(0,6))
        wrap.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(wrap, text=label).grid(row=0, column=0, sticky="w", padx=(0,8))
        ctk.CTkLabel(wrap, textvariable=var).grid(row=0, column=1, sticky="we")

    def _apply_category_theme(self, cat: str):
        colour = COLOUR_MAP.get(cat, "#1a1a1a")
        # Colour the root
        self.configure(fg_color=colour)
        # Make child panels transparent so the root colour shows everywhere
        try:
            self.list_panel.configure(fg_color="transparent")
            #Made by thebacklash from Discord
            self.details_container.configure(fg_color="transparent")
            self.details.configure(fg_color="transparent")
        except Exception:
            pass

    def refresh_list(self):
        # Clear old buttons
        for w in self.list_scroll.winfo_children():
            w.destroy()
        self.entries.clear()
        self.selected_button = None
        self.current_file_path = None
        self._clear_details()

        # Load all jsons
        files = sorted(
            [f for f in os.listdir(self.save_dir) if f.lower().endswith(".json")],
            key=str.lower
        )
        if not files:
            ctk.CTkLabel(self.list_scroll, text="(No JSONs found)").pack(pady=10)
            return

        for fname in files:
            fpath = os.path.join(self.save_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                # show a disabled button with error note
                btn = ctk.CTkButton(self.list_scroll, text=f"{fname} (invalid)", state="disabled")
                btn.pack(fill="x", pady=2, padx=6)
                continue

            # attach full path for delete
            data["full_path"] = fpath
            self.entries.append((fpath, data))

            btn_text = data.get("name") or os.path.splitext(fname)[0]
            btn = ctk.CTkButton(self.list_scroll, text=btn_text)
            btn.configure(command=lambda d=data, b=btn: self._select_entry(d, b))
            btn.pack(fill="x", pady=2, padx=6)

    def _select_entry(self, data, btn):
        # Remember which file is open (for DELETE)
        self.current_file_path = data.get("full_path", None)

        # Unhighlight previous
        if self.selected_button:
            try:
                self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            except Exception:
                pass

        # Highlight current
        self.selected_button = btn
        try:
            btn.configure(fg_color="#444444")
        except Exception:
            pass

        # Populate details
        self._show_details(data)

    def _clear_details(self):
        self.name_var.set("")
        self.file_var.set("")
        self.source_var.set("")
        self.type_var.set("")
        self.tags_var.set("")
        self._render_tags([])

        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.configure(state="disabled")

        self._set_preview(None)
        self.current_file_path = None

        self._render_tags([])
        self._render_extra_images([])

    def _show_details(self, data):

        # Jump scroll bar to top when showing details
        try:
            self.details._parent_canvas.yview_moveto(0)
        except Exception as e:
            print(f"[Scroll Reset] Could not reset scroll: {e}")
        self.name_var.set(data.get("name", ""))
        self.file_var.set(data.get("file_name", ""))
        self.source_var.set(data.get("source", ""))
        self.type_var.set(data.get("model_type", ""))
        self._render_tags(data.get("tags", []))

        # notes: toggle to NORMAL, set, then DISABLED
        self.notes_box.configure(state="normal")
        self.notes_box.delete("1.0", "end")
        self.notes_box.insert("1.0", data.get("notes", ""))
        self.notes_box.configure(state="disabled")

        img_path = data.get("image_path") or ""
        self._set_preview(img_path if os.path.exists(img_path) else None)

        self._render_tags(data.get("tags", []))
        self._render_extra_images(data.get("extra_images", []))
        self.after(10, self._scroll_details_to_top)

    def _set_preview(self, image_path):
        # If no path, show placeholder
        if not image_path:
            self.preview_image = self.no_image
            self.image_label.configure(image=self.preview_image, text="")
            self.image_label.image = self.preview_image  # keep strong ref
            return
        try:
            img = Image.open(image_path).convert("RGBA")
            ow, oh = img.size
            # shortest side -> 300
            scale = 300 / min(ow, oh)
            nw, nh = max(1, int(ow * scale)), max(1, int(oh * scale))
            img = img.resize((nw, nh), Image.LANCZOS)

            self.preview_image = ctk.CTkImage(light_image=img, dark_image=img, size=(nw, nh))
            self.image_label.configure(image=self.preview_image, text="")
            self.image_label.image = self.preview_image  # keep strong ref
        except Exception as e:
            print(f"[Catalogue Preview] Failed to load '{image_path}': {e}")
            # Fall back to placeholder
            self.preview_image = self.no_image
            self.image_label.configure(image=self.preview_image, text="")
            self.image_label.image = self.preview_image

    def _render_tags(self, tags):
        # clear old
        for w in self.tags_container.winfo_children():
            w.destroy()

        self.tags_container.grid_columnconfigure(0, weight=1)

        if not tags:
            ctk.CTkLabel(self.tags_container, text="(No tags)").grid(row=0, column=0, sticky="w")
            return

        row = 0
        for tag in tags:
            # Expect {"label": "...", "value": "..."}; tolerate strings just in case
            if isinstance(tag, dict):
                label_text = (tag.get("label") or "").strip()
                value_text = (tag.get("value") or "").strip()
            else:
                label_text = ""
                value_text = str(tag).strip()

            # Optional label (what it's for)
            if label_text:
                ctk.CTkLabel(self.tags_container, text=label_text).grid(
                    row=row, column=0, sticky="w", pady=(2, 0)
                )
                row += 1

            # Button with the tag value (click to copy)
            btn = ctk.CTkButton(
                self.tags_container,
                text=value_text if value_text else "(empty)",
                fg_color="transparent",
                border_width=1,
                hover_color="#333333",
            )
            btn.configure(command=lambda t=value_text, b=btn: self._copy_tag_to_clipboard(t, b))
            btn.grid(row=row, column=0, sticky="we", pady=(2, 6))
            row += 1

    def _copy_tag_to_clipboard(self, text, btn):
        try:
            # copy
            self.clipboard_clear()
            self.clipboard_append(text)
            # flash feedback
            original = btn.cget("text")
            btn.configure(text="Copied!")
            self.after(850, lambda: btn.configure(text=original))
        except Exception as e:
            print(f"[Tags] Clipboard copy failed: {e}")

    def delete_selected_character(self):
        if not self.current_file_path:
            messagebox.showwarning("No Selection", "No character is currently selected.")
            return

        fname = os.path.basename(self.current_file_path)
        confirm = messagebox.askyesno(
            "Delete Character",
            f"Are you sure you want to permanently delete:\n\n{fname}?"
        )
        if not confirm:
            return

        try:
            if os.path.exists(self.current_file_path):
                os.remove(self.current_file_path)
            # Clear UI + state
            self.current_file_path = None
            self._clear_details()
            # also clear highlight
            if self.selected_button:
                try:
                    self.selected_button.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                except Exception:
                    pass
                self.selected_button = None
            # Rebuild the list
            self.refresh_list()
            messagebox.showinfo("Deleted", f"Deleted:\n{fname}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file:\n{e}")

    def _render_extra_images(self, items):
        # Clear old
        for w in self.extra_images_container.winfo_children():
            w.destroy()

        # Keep references to CTkImage to avoid GC
        self._extra_previews = []

        if not items:
            ctk.CTkLabel(self.extra_images_container, text="(None)").grid(row=0, column=0, sticky="w")
            return

        row = 0
        for item in items:
            title = (item.get("title") or "").strip()
            path = (item.get("image_path") or "").strip()

            if title:
                ctk.CTkLabel(self.extra_images_container, text=title).grid(row=row, column=0, sticky="w", pady=(4, 2))
                row += 1

            # Make a preview (use same shortest-side=300 rule; fall back to placeholder)
            img_to_use = None
            if path and os.path.exists(path):
                try:
                    from PIL import Image
                    img = Image.open(path).convert("RGBA")
                    ow, oh = img.size
                    scale = 300 / min(ow, oh)
                    nw, nh = max(1, int(ow * scale)), max(1, int(oh * scale))
                    img = img.resize((nw, nh), Image.LANCZOS)
                    cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(nw, nh))
                    img_to_use = cimg
                except Exception as e:
                    print(f"[Catalogue] Extra image failed '{path}': {e}")

            if not img_to_use:
                # Use the same placeholder you created earlier
                img_to_use = self.no_image

            lbl = ctk.CTkLabel(self.extra_images_container, image=img_to_use, text="")
            lbl.grid(row=row, column=0, sticky="w", pady=(0, 8))
            lbl.image = img_to_use  # strong ref
            self._extra_previews.append(img_to_use)
            row += 1

    def _scroll_details_to_top(self):
        try:
            self.details._parent_canvas.yview_moveto(0)
        except Exception:
            pass