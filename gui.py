import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, BooleanVar
import ferium_wrapper
import requests
import threading

# Helper to fetch MC release versions
def fetch_mc_versions():
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    resp = requests.get(manifest_url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    releases = [v for v in data.get("versions", []) if v.get("type") == "release"]
    sorted_releases = sorted(
        releases,
        key=lambda x: x.get("releaseTime", ""),
        reverse=True
    )
    return [v["id"] for v in sorted_releases]

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Aurum")
        self.geometry("600x550")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.bind_all("<Button-1>", self._clear_or_set_focus)

        # --- Home Frame ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=20, pady=(20,10), fill="x")

        self.selected_label = ctk.CTkLabel(self.main_frame, text="Selected Profile:")
        self.selected_label.pack(side="left", padx=(0,10))

        self.profile_combo = ctk.CTkComboBox(
            self.main_frame, values=[], command=self.on_profile_select, state="readonly"
        )
        self.profile_combo.pack(side="left", fill="x", expand=True)

        self.add_button = ctk.CTkButton(
            self.main_frame, text="+", width=30, command=self.show_create_profile_fields
        )
        self.add_button.pack(side="left", padx=(10,0))

        self.home_buttons_frame = ctk.CTkFrame(self)
        self.home_buttons_frame.pack(padx=20, pady=(10,20), fill="x")

        self.add_mods_button = ctk.CTkButton(
            self.home_buttons_frame, text="Add Mods", command=self.show_add_mods_fields
        )
        self.add_mods_button.pack(side="left", expand=True, padx=5)

        self.upgrade_button = ctk.CTkButton(
            self.home_buttons_frame, text="Upgrade Mods", command=self.show_upgrade_view
        )
        self.upgrade_button.pack(side="left", expand=True, padx=5)

        self.mod_list_button = ctk.CTkButton(
            self.home_buttons_frame, text="Mod List", command=self.show_mod_list_fields
        )
        self.mod_list_button.pack(side="left", expand=True, padx=5)

        # Global log and return widgets
        self.upgrade_label = ctk.CTkLabel(self, text="")
        self.log_textbox = ctk.CTkTextbox(self, height=200)
        self.log_textbox.configure(state="disabled")
        self.return_button = ctk.CTkButton(self, text="Return", command=self._restore_home)

        # Placeholder frames
        self.create_frame = None
        self.mods_frame = None
        self.mod_list_frame = None

        self.refresh_profiles()

    def _clear_or_set_focus(self, event):
        w = event.widget
        if isinstance(w, (ctk.CTkEntry, tk.Entry, ctk.CTkTextbox)):
            w.focus_set()
        else:
            self.focus()

    def refresh_profiles(self):
        try:
            profiles = ferium_wrapper.list_profiles()
            active = ferium_wrapper.get_active_profile()
            self.profile_combo.configure(values=profiles)
            if active in profiles:
                self.profile_combo.set(active)
        except ferium_wrapper.FeriumError as e:
            messagebox.showerror("Error", str(e))

    def on_profile_select(self, choice):
        try:
            ferium_wrapper.switch_profile(choice)
            messagebox.showinfo("Success", f"Switched to '{choice}'.")
        except ferium_wrapper.FeriumError as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.refresh_profiles()

    def _hide_all_views(self):
        # Hide home and all subviews
        self.main_frame.pack_forget()
        self.home_buttons_frame.pack_forget()
        if self.create_frame:
            self.create_frame.pack_forget()
        if self.mods_frame:
            self.mods_frame.pack_forget()
        if self.mod_list_frame:
            self.mod_list_frame.pack_forget()
        self.upgrade_label.pack_forget()
        self.log_textbox.pack_forget()
        self.return_button.pack_forget()

    def _restore_home(self):
        self._hide_all_views()
        self.main_frame.pack(padx=20, pady=(20,10), fill="x")
        self.home_buttons_frame.pack(padx=20, pady=(10,20), fill="x")

    # Create Profile View
    def show_create_profile_fields(self):
        self._hide_all_views()
        self.create_frame = ctk.CTkFrame(self)
        self.create_frame.pack(padx=20, pady=20, fill="x")

        header = ctk.CTkFrame(self.create_frame)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="New Profile Creation",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="< Back", width=60,
                      command=self._restore_home).pack(side="right")

        self.name_entry = ctk.CTkEntry(self.create_frame, placeholder_text="Profile Name")
        self.name_entry.pack(fill="x", pady=5)

        try:
            versions = fetch_mc_versions()
        except Exception:
            versions = ["1.21.5", "1.20.1", "1.19.4", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4", "1.13.2", "1.12.2", "1.11.2", "1.10.2", "1.9.4", "1.8.9", "1.7.10"]  # Fallback versions
        self.version_combo = ctk.CTkComboBox(
            self.create_frame, values=versions, state="readonly"
        )
        self.version_combo.set(versions[0])
        self.version_combo.pack(fill="x", pady=5)

        self.loader_combo = ctk.CTkComboBox(
            self.create_frame, values=["fabric","forge","quilt"], state="readonly"
        )
        self.loader_combo.set("fabric")
        self.loader_combo.pack(fill="x", pady=5)

        self.custom_dir_var = BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.create_frame, text="Custom Mod Directory",
            variable=self.custom_dir_var, command=self._toggle_custom_dir
        ).pack(anchor="w", pady=5)

        self.dir_frame = ctk.CTkFrame(self.create_frame)
        self.output_entry = ctk.CTkEntry(self.dir_frame, placeholder_text="Custom Mod Directory")
        self.output_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(self.dir_frame, text="Browse",
                      command=self.browse_output_dir).pack(side="left", padx=(10,0))

        ctk.CTkButton(
            self.create_frame, text="Create Profile",
            command=self.create_profile
        ).pack(pady=(10,0))

    def _toggle_custom_dir(self):
        if self.custom_dir_var.get():
            self.dir_frame.pack(fill="x", pady=5)
        else:
            self.dir_frame.pack_forget()

    # Mods View
    def show_add_mods_fields(self):
        self._hide_all_views()
        self.mods_frame = ctk.CTkFrame(self)
        self.mods_frame.pack(padx=20, pady=20, fill="both", expand=True)

        header = ctk.CTkFrame(self.mods_frame)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Add Mods",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="< Back", width=60,
                      command=self._restore_home).pack(side="right")

        ctk.CTkLabel(self.mods_frame, text="Paste Mod IDs (one per line):").pack(anchor="w")
        self.mods_textbox = ctk.CTkTextbox(self.mods_frame)
        self.mods_textbox.pack(fill="both", expand=True, pady=5)

        btn_frame = ctk.CTkFrame(self.mods_frame)
        btn_frame.pack(fill="x", pady=(0,10))
        ctk.CTkButton(
            btn_frame, text="Paste from Clipboard",
            command=self.paste_from_clipboard
        ).pack(side="left", expand=True, padx=5)
        self.add_and_upgrade_btn = ctk.CTkButton(
            btn_frame, text="Add Mods & Upgrade",
            command=self.add_and_upgrade_mods
        )
        self.add_and_upgrade_btn.pack(side="left", expand=True, padx=5)

    def browse_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, d)

    def create_profile(self):
        name = self.name_entry.get().strip()
        version = self.version_combo.get().strip()
        loader = self.loader_combo.get()
        output = self.output_entry.get().strip() if self.custom_dir_var.get() else None
        if not (name and version and loader):
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
        try:
            ferium_wrapper.create_profile(name, version, loader, output)
            messagebox.showinfo("Success", f"Profile '{name}' created.")
            self._restore_home()
        except ferium_wrapper.FeriumError as e:
            messagebox.showerror("Error", str(e))

    # Upgrade View
    def show_upgrade_view(self):
        self._hide_all_views()
        self.upgrade_label = ctk.CTkLabel(self, text="Upgrade Output:")
        self.upgrade_label.pack(padx=20, pady=(10,0), anchor="w")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.pack(fill="x", padx=20, pady=(5,10))
        self.upgrade_button.configure(state="disabled")
        def worker():
            try:
                output = ferium_wrapper.upgrade_mods()
            except ferium_wrapper.FeriumError as e:
                output = str(e)
            self.log_textbox.insert("end", output + "\n")
            self.log_textbox.configure(state="disabled")
            self.upgrade_button.configure(state="normal")
            self.return_button.pack(padx=20, pady=(0,20))
        threading.Thread(target=worker, daemon=True).start()

    def paste_from_clipboard(self):
        try:
            text = self.clipboard_get()
            self.mods_textbox.delete("0.0", "end")
            self.mods_textbox.insert("0.0", text)
        except tk.TclError:
            messagebox.showerror("Error", "Clipboard is empty or unavailable.")

    def add_and_upgrade_mods(self):
        ids = self.mods_textbox.get("0.0", "end").strip().splitlines()
        if not ids:
            messagebox.showwarning("No Mods", "Please paste one or more mod IDs.")
            return
        self.log_textbox.pack(fill="x", padx=20, pady=(0,20))
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.add_and_upgrade_btn.configure(state="disabled")

        def worker():
            for mod_id in ids:
                try:
                    out = ferium_wrapper.add_mod(mod_id)
                except ferium_wrapper.FeriumError as e:
                    out = str(e)
                self.log_textbox.insert("end", out + "\n")
                self.log_textbox.see("end")
            try:
                upgrade_msg = ferium_wrapper.upgrade_mods()
                self.log_textbox.insert("end", upgrade_msg + "\n")
            except ferium_wrapper.FeriumError as e:
                self.log_textbox.insert("end", str(e) + "\n")
            self.log_textbox.configure(state="disabled")
            self.add_and_upgrade_btn.configure(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    # Upgrade Mods View
    def show_upgrade_view(self):
        self._hide_all_views()
        self.upgrade_label.configure(text="Upgrade Output:")
        self.upgrade_label.pack(padx=20, pady=(10,0), anchor="w")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.pack(fill="x", padx=20, pady=(5,10))
        self.upgrade_button.configure(state="disabled")
        def worker():
            try:
                output = ferium_wrapper.upgrade_mods()
            except ferium_wrapper.FeriumError as e:
                output = str(e)
            self.log_textbox.insert("end", output + "\n")
            self.log_textbox.configure(state="disabled")
            self.upgrade_button.configure(state="normal")
            self.return_button.pack(padx=20, pady=(0,20))
        threading.Thread(target=worker, daemon=True).start()

    # Mod List View
    def show_mod_list_fields(self):
        self._hide_all_views()
        self.mod_list_frame = ctk.CTkFrame(self)
        self.mod_list_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.mod_list_frame)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Mod List", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="< Back", width=60, command=self._restore_home).pack(side="right")

        # Text field displaying mod IDs
        self.mod_list_textbox = ctk.CTkTextbox(self.mod_list_frame)
        self.mod_list_textbox.pack(fill="both", expand=True, pady=5)
        # Populate
        try:
            mods = ferium_wrapper.list_mods()
            self.mod_list_textbox.insert("0.0", "\n".join(mods))
        except ferium_wrapper.FeriumError as e:
            self.mod_list_textbox.insert("0.0", str(e))
        self.mod_list_textbox.configure(state="disabled")

        # Copy button
        copy_btn = ctk.CTkButton(
            self.mod_list_frame, text="Copy Mod List", command=self._copy_listbox_content
        )
        copy_btn.pack(pady=(10,0))

    def _copy_listbox_content(self):
        text = self.mod_list_textbox.get("0.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", "Mod list copied to clipboard.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
