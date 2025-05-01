import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, BooleanVar
import ferium_wrapper
import requests


def fetch_mc_versions():
    """
    Fetch available Minecraft release versions from Mojang's version manifest.
    Returns a list of version IDs of type 'release', sorted by release date (most recent first).
    """
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    resp = requests.get(manifest_url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    # Filter only release versions
    release_versions = [v for v in data.get("versions", []) if v.get("type") == "release"]
    # Sort by newest first
    sorted_releases = sorted(
        release_versions,
        key=lambda x: x.get("releaseTime", ""),
        reverse=True
    )
    versions = [v["id"] for v in sorted_releases]
    return versions

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Aurum")
        self.geometry("400x350")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Bind clicks to manage entry focus
        self.bind_all("<Button-1>", self._clear_or_set_focus)

        # Main selection frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(padx=20, pady=20, fill="x", expand=True)

        self.profile_combo = ctk.CTkComboBox(
            self.main_frame, values=[], command=self.on_profile_select, state="readonly"
        )
        self.profile_combo.pack(side="left", fill="x", expand=True)

        self.add_button = ctk.CTkButton(
            self.main_frame, text="+", width=30, command=self.show_create_profile_fields
        )
        self.add_button.pack(side="left", padx=(10, 0))

        self.create_frame = None
        self.refresh_profiles()

    def _clear_or_set_focus(self, event):
        widget = event.widget
        if isinstance(widget, (ctk.CTkEntry, tk.Entry)):
            widget.focus_set()
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

    def show_create_profile_fields(self):
        self.main_frame.pack_forget()
        self.create_frame = ctk.CTkFrame(self)
        self.create_frame.pack(padx=20, pady=20, fill="x", expand=True)

        header = ctk.CTkFrame(self.create_frame)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="New Profile Creation", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        ctk.CTkButton(
            header, text="< Back", width=60, command=self.hide_create_profile_fields
        ).pack(side="right")

        # Profile name
        self.name_entry = ctk.CTkEntry(
            self.create_frame, placeholder_text="Profile Name"
        )
        self.name_entry.pack(fill="x", pady=5)

        # Minecraft version dropdown (dynamic)
        try:
            versions = fetch_mc_versions()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Could not fetch Minecraft versions: {e}"
            )
            versions = ["1.21.4"]
        self.version_combo = ctk.CTkComboBox(
            self.create_frame, values=versions, state="readonly"
        )
        self.version_combo.set(versions[0])
        self.version_combo.pack(fill="x", pady=5)

        # Mod loader dropdown
        self.loader_combo = ctk.CTkComboBox(
            self.create_frame, values=["fabric", "forge", "quilt"], state="readonly"
        )
        self.loader_combo.set("fabric")
        self.loader_combo.pack(fill="x", pady=5)

        # Custom mod directory checkbox
        self.custom_dir_var = BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.create_frame,
            text="Custom Mod Directory",
            variable=self.custom_dir_var,
            command=self.toggle_custom_dir
        ).pack(anchor="w", pady=5)

        # Directory selector (hidden initially)
        self.dir_frame = ctk.CTkFrame(self.create_frame)
        self.output_entry = ctk.CTkEntry(
            self.dir_frame, placeholder_text="Custom Mod Directory"
        )
        self.output_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            self.dir_frame, text="Browse", command=self.browse_output_dir
        ).pack(side="left", padx=(10,0))

        # Create profile button
        self.create_btn = ctk.CTkButton(
            self.create_frame, text="Create Profile", command=self.create_profile
        )
        self.create_btn.pack(pady=(10,0))

    def toggle_custom_dir(self):
        if self.custom_dir_var.get():
            self.dir_frame.pack(fill="x", pady=5, before=self.create_btn)
        else:
            self.dir_frame.pack_forget()

    def hide_create_profile_fields(self):
        if self.create_frame:
            self.create_frame.destroy()
            self.create_frame = None
        self.main_frame.pack(padx=20, pady=20, fill="x", expand=True)
        self.refresh_profiles()

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)

    def create_profile(self):
        name = self.name_entry.get().strip()
        version = self.version_combo.get().strip()
        loader = self.loader_combo.get()
        output = self.output_entry.get().strip() if self.custom_dir_var.get() else None
        if not name or not version or not loader:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return
        try:
            ferium_wrapper.create_profile(name, version, loader, output)
            messagebox.showinfo("Success", f"Profile '{name}' created.")
            self.hide_create_profile_fields()
        except ferium_wrapper.FeriumError as e:
            messagebox.showerror("Error", str(e))
