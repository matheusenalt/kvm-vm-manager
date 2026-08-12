from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk


class AssetManager:
    def __init__(self):
        self.base_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
        )

        self.logo_files = {
            "windows": "windows.png",
            "linux": "linux.png",
        }

        self.logo_fallback = {
            "windows": "⊞",
            "linux": "🐧",
        }

    def normalize_os_logo(self, os_name):
        value = str(
            os_name or ""
        ).lower()

        if (
            "windows" in value
            or "win" in value
        ):
            return "windows"

        return "linux"

    def get_os_image(
        self,
        os_name,
        size=(60, 60),
    ):
        key = self.normalize_os_logo(
            os_name
        )

        filename = self.logo_files.get(
            key
        )

        if not filename:
            return None

        path = (
            self.base_path
            / filename
        )

        if not path.exists():
            return None

        try:
            image = Image.open(
                path
            )

            return ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=size,
            )

        except Exception as error:
            print(
                f"Could not load image "
                f"'{path}': {error}"
            )

            return None

    def get_fallback(
        self,
        os_name,
    ):
        key = self.normalize_os_logo(
            os_name
        )

        return self.logo_fallback.get(
            key,
            "▣",
        )

    def get_app_icon_path(self):
        for filename in (
            "app-icon.png",
            "app-icon.gif",
        ):
            path = (
                self.base_path
                / filename
            )

            if path.exists():
                return path

        return None

    def get_app_image(
        self,
        size=(36, 36),
    ):
        path = (
            self.get_app_icon_path()
        )

        if path is None:
            return None

        try:
            image = Image.open(
                path
            )

            return ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=size,
            )

        except Exception as error:
            print(
                "Could not load "
                f"application icon: {error}"
            )

            return None

    def apply_window_icon(
        self,
        window,
    ):
        path = (
            self.get_app_icon_path()
        )

        if path is None:
            return False

        try:
            image = Image.open(
                path
            )

            icon = ImageTk.PhotoImage(
                image
            )

            window.iconphoto(
                True,
                icon,
            )

            window._kvm_app_icon = icon

            return True

        except Exception as error:
            print(
                "Could not apply "
                f"application icon: {error}"
            )

            return False 