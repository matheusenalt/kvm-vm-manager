from tkinter import filedialog

import customtkinter as ctk

from os_catalog import get_os_id, get_os_options
from ..theme import COLORS


class CreateVMDialog(ctk.CTkToplevel):
    VCPU_OPTIONS = ["1", "2", "4", "6", "8", "12", "16"]
    RAM_OPTIONS = ["1", "2", "4", "8", "16", "32", "64"]

    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.title("Criar Nova VM")
        self.geometry("620x700")
        self.minsize(580, 660)
        self.configure(fg_color=COLORS["background"])
        self.transient(controller)
        self.name_var = ctk.StringVar()
        self.os_var = ctk.StringVar(value="Ubuntu")
        self.vcpus_var = ctk.StringVar(value="2")
        self.ram_var = ctk.StringVar(value="4")
        self.disk_var = ctk.StringVar(value="40")
        self.iso_var = ctk.StringVar()
        self.build_ui()
        self.after(80, self.grab_set)

    def build_ui(self):
        panel = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.pack(fill="both", expand=True, padx=22, pady=22)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Criar Nova VM",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))

        ctk.CTkLabel(
            panel,
            text="Escolha o sistema, os recursos e uma ISO local.",
            text_color=COLORS["text_secondary"],
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 18))

        row = 2
        row = self.add_entry(panel, row, "Nome da VM", self.name_var, "lab-ubuntu")
        row = self.add_option(panel, row, "Sistema Operacional", self.os_var, get_os_options())

        resources = ctk.CTkFrame(panel, fg_color="transparent")
        resources.grid(row=row, column=0, sticky="ew", padx=22, pady=(0, 14))
        resources.grid_columnconfigure((0, 1), weight=1)

        self.add_resource_option(resources, 0, "vCPUs", self.vcpus_var, self.VCPU_OPTIONS, (0, 7))
        self.add_resource_option(resources, 1, "RAM (GB)", self.ram_var, self.RAM_OPTIONS, (7, 0))
        row += 1

        row = self.add_entry(panel, row, "Disco (GB)", self.disk_var, "40")

        iso_frame = ctk.CTkFrame(panel, fg_color="transparent")
        iso_frame.grid(row=row, column=0, sticky="ew", padx=22, pady=(0, 14))
        iso_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            iso_frame,
            text="Imagem ISO",
            text_color=COLORS["text"],
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        ctk.CTkEntry(
            iso_frame,
            textvariable=self.iso_var,
            placeholder_text="/caminho/para/sistema.iso",
            height=42,
            fg_color=COLORS["header"],
            border_color=COLORS["border"],
        ).grid(row=1, column=0, sticky="ew", pady=(7, 0), padx=(0, 8))

        ctk.CTkButton(
            iso_frame,
            text="Selecionar...",
            width=110,
            height=42,
            corner_radius=9,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            command=self.browse_iso,
        ).grid(row=1, column=1, pady=(7, 0))
        row += 1

        ctk.CTkLabel(
            panel,
            text="Se o libosinfo não reconhecer a ISO, o virt-install usará o modo genérico.",
            wraplength=500,
            justify="left",
            text_color=COLORS["text_secondary"],
        ).grid(row=row, column=0, sticky="w", padx=22, pady=(0, 12))
        row += 1

        self.status_label = ctk.CTkLabel(
            panel,
            text="",
            wraplength=500,
            justify="left",
            text_color=COLORS["text_secondary"],
        )
        self.status_label.grid(row=row, column=0, sticky="w", padx=22, pady=(4, 12))
        row += 1

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=row, column=0, sticky="ew", padx=22, pady=(0, 22))

        ctk.CTkButton(
            buttons,
            text="Cancelar",
            width=120,
            height=42,
            corner_radius=9,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))

        self.create_button = ctk.CTkButton(
            buttons,
            text="+  Criar VM",
            width=140,
            height=42,
            corner_radius=9,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.submit,
        )
        self.create_button.pack(side="right")

    def add_resource_option(self, master, column, label, variable, values, padx):
        box = ctk.CTkFrame(master, fg_color="transparent")
        box.grid(row=0, column=column, sticky="ew", padx=padx)
        ctk.CTkLabel(box, text=label, text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkOptionMenu(
            box,
            values=values,
            variable=variable,
            fg_color=COLORS["button"],
            button_color=COLORS["button"],
            button_hover_color=COLORS["button_hover"],
        ).pack(fill="x", pady=(7, 0))

    def add_entry(self, master, row, label, variable, placeholder):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=22, pady=(0, 14))
        ctk.CTkLabel(frame, text=label, text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkEntry(
            frame,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            fg_color=COLORS["header"],
            border_color=COLORS["border"],
        ).pack(fill="x", pady=(7, 0))
        return row + 1

    def add_option(self, master, row, label, variable, values):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=22, pady=(0, 14))
        ctk.CTkLabel(frame, text=label, text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkOptionMenu(
            frame,
            values=values,
            variable=variable,
            fg_color=COLORS["button"],
            button_color=COLORS["button"],
            button_hover_color=COLORS["button_hover"],
            dropdown_fg_color=COLORS["card"],
            dynamic_resizing=False,
        ).pack(fill="x", pady=(7, 0))
        return row + 1

    def browse_iso(self):
        selected = filedialog.askopenfilename(
            parent=self,
            title="Selecionar imagem ISO",
            filetypes=[("ISO images", "*.iso"), ("All files", "*")],
        )
        if selected:
            self.iso_var.set(selected)

    def submit(self):
        data = {
            "name": self.name_var.get().strip(),
            "os": get_os_id(self.os_var.get()),
            "vcpus": self.vcpus_var.get(),
            "ram_gb": self.ram_var.get(),
            "disk_gb": self.disk_var.get().strip(),
            "iso_path": self.iso_var.get().strip(),
        }

        if not data["name"]:
            self.show_result("Informe o nome da VM.", success=False)
            return
        if not data["iso_path"]:
            self.show_result("Selecione uma imagem ISO.", success=False)
            return

        self.controller.create_vm_from_dialog(self, data)

    def set_busy(self, busy):
        self.create_button.configure(
            state="disabled" if busy else "normal",
            text="Criando..." if busy else "+  Criar VM",
        )

    def show_result(self, message, success):
        self.status_label.configure(
            text=message,
            text_color=COLORS["green"] if success else COLORS["red"],
        )
