import customtkinter as ctk

from connection import get_vm_config, load_vm_config, save_vm_config
from desktop_shortcuts import create_widget_shortcut, remove_widget_shortcut
from ..theme import COLORS


class VMSettingsDialog(ctk.CTkToplevel):
    CONNECTION_OPTIONS = ["ui", "ssh", "anydesk"]

    def __init__(self, controller, vm_data):
        super().__init__(controller)
        self.controller = controller
        self.vm_data = vm_data
        self.vm_name = vm_data["name"]
        self.vm_config = get_vm_config(self.vm_name) or {}
        self.title(f"Configurações - {self.vm_name}")
        self.geometry("520x520")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["background"])
        self.transient(controller)
        self.connection_var = ctk.StringVar(value=self.get_initial_connection_type())
        self.address_var = ctk.StringVar(value=str(self.vm_config.get("address", "")))
        self.user_var = ctk.StringVar(value=str(self.vm_config.get("user", "")))
        self.build_ui()
        self.after(80, self.grab_set)

    def get_initial_connection_type(self):
        configured = str(self.vm_config.get("connection", "")).strip().lower()
        if configured in {"web", "viewer"}:
            return "ui"
        if configured in self.CONNECTION_OPTIONS:
            return configured
        return "ui" if str(self.vm_data.get("os", "linux")).lower().startswith("windows") else "ssh"

    def build_ui(self):
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.pack(fill="both", expand=True, padx=22, pady=22)

        ctk.CTkLabel(
            panel,
            text=f"Configurações de {self.vm_name}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=22, pady=(22, 6))

        ctk.CTkLabel(
            panel,
            text="Escolha como esta VM será aberta.",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=22, pady=(0, 18))

        ctk.CTkLabel(panel, text="Tipo de conexão", text_color=COLORS["text"]).pack(anchor="w", padx=22)

        self.connection_menu = ctk.CTkOptionMenu(
            panel,
            values=self.CONNECTION_OPTIONS,
            variable=self.connection_var,
            command=self.connection_changed,
            fg_color=COLORS["button"],
            button_color=COLORS["button"],
            button_hover_color=COLORS["button_hover"],
            dropdown_fg_color=COLORS["card"],
        )
        self.connection_menu.pack(fill="x", padx=22, pady=(7, 16))

        self.dynamic_frame = ctk.CTkFrame(panel, fg_color="transparent")
        self.dynamic_frame.pack(fill="x", padx=22)

        shortcut_frame = ctk.CTkFrame(
            panel,
            fg_color=COLORS["header"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        shortcut_frame.pack(fill="x", padx=22, pady=(18, 0))

        ctk.CTkLabel(
            shortcut_frame,
            text="Atalho do mini-widget",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            shortcut_frame,
            text="Crie um atalho na área de trabalho para abrir somente esta VM.",
            wraplength=420,
            justify="left",
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=14, pady=(0, 10))

        shortcut_buttons = ctk.CTkFrame(shortcut_frame, fg_color="transparent")
        shortcut_buttons.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkButton(
            shortcut_buttons,
            text="Criar atalho",
            width=130,
            height=36,
            corner_radius=8,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            command=self.create_shortcut,
        ).pack(side="left")

        ctk.CTkButton(
            shortcut_buttons,
            text="Remover",
            width=100,
            height=36,
            corner_radius=8,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            command=self.remove_shortcut,
        ).pack(side="left", padx=(8, 0))

        self.message_label = ctk.CTkLabel(
            panel,
            text="",
            text_color=COLORS["text_secondary"],
            wraplength=430,
        )
        self.message_label.pack(anchor="w", padx=22, pady=(12, 0))

        button_row = ctk.CTkFrame(panel, fg_color="transparent")
        button_row.pack(side="bottom", fill="x", padx=22, pady=22)

        ctk.CTkButton(
            button_row,
            text="Cancelar",
            width=110,
            height=40,
            corner_radius=9,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            button_row,
            text="Salvar",
            width=110,
            height=40,
            corner_radius=9,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.save,
        ).pack(side="right")

        self.render_dynamic_field()

    def connection_changed(self, _value):
        self.message_label.configure(text="")
        self.render_dynamic_field()

    def render_dynamic_field(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        connection_type = self.connection_var.get()

        if connection_type == "anydesk":
            self.add_entry("Address", self.address_var, "Ex.: 123456789")
        elif connection_type == "ssh":
            self.add_entry("User", self.user_var, "Ex.: matheus")
        else:
            info_box = ctk.CTkFrame(
                self.dynamic_frame,
                fg_color=COLORS["header"],
                corner_radius=10,
                border_width=1,
                border_color=COLORS["border"],
            )
            info_box.pack(fill="x")
            ctk.CTkLabel(
                info_box,
                text="▣  virt-viewer",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text"],
            ).pack(anchor="w", padx=15, pady=(14, 5))
            ctk.CTkLabel(
                info_box,
                text="A interface gráfica será aberta diretamente pelo virt-viewer em qemu:///system.",
                font=ctk.CTkFont(size=13),
                text_color=COLORS["text_secondary"],
                justify="left",
                wraplength=390,
            ).pack(anchor="w", padx=15, pady=(0, 14))

    def add_entry(self, label, variable, placeholder):
        ctk.CTkLabel(self.dynamic_frame, text=label, text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkEntry(
            self.dynamic_frame,
            textvariable=variable,
            placeholder_text=placeholder,
            height=42,
            corner_radius=9,
            fg_color=COLORS["header"],
            border_color=COLORS["border"],
        ).pack(fill="x", pady=(7, 0))

    def create_shortcut(self):
        try:
            result = create_widget_shortcut(self.vm_name)
        except Exception as error:
            result = {"success": False, "message": str(error)}
        self.show_message(result.get("message", ""), result.get("success", False))

    def remove_shortcut(self):
        try:
            result = remove_widget_shortcut(self.vm_name)
        except Exception as error:
            result = {"success": False, "message": str(error)}
        self.show_message(result.get("message", ""), result.get("success", False))

    def save(self):
        connection_type = self.connection_var.get().strip().lower()
        if connection_type not in self.CONNECTION_OPTIONS:
            self.show_error("Tipo de conexão inválido.")
            return

        address = self.address_var.get().strip()
        user = self.user_var.get().strip()

        if connection_type == "anydesk" and not address:
            self.show_error("Informe o Address do AnyDesk.")
            return
        if connection_type == "ssh" and not user:
            self.show_error("Informe o usuário SSH.")
            return

        config = load_vm_config()
        current = config.get(self.vm_name, {})
        if not isinstance(current, dict):
            current = {}

        cleaned = dict(current)
        for key in ("connection", "address", "user", "host", "port", "url", "scheme", "path", "startup_delay"):
            cleaned.pop(key, None)

        cleaned["connection"] = connection_type
        if connection_type == "anydesk":
            cleaned["address"] = address
        elif connection_type == "ssh":
            cleaned["user"] = user

        config[self.vm_name] = cleaned
        result = save_vm_config(config)
        success = bool(result.get("success")) if isinstance(result, dict) else bool(result)
        message = result.get("message", "") if isinstance(result, dict) else ""

        if not success:
            self.show_error(message or "Não foi possível salvar o config.json.")
            return

        self.show_message("Configuração salva.", True)
        self.controller.refresh_vms(show_indicator=False)
        self.after(450, self.destroy)

    def show_message(self, message, success):
        self.message_label.configure(
            text=message,
            text_color=COLORS["green"] if success else COLORS["red"],
        )

    def show_error(self, message):
        self.show_message(message, False)
