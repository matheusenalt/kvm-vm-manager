import queue
import threading

import customtkinter as ctk

from connection import get_vm_config
from launcher import launch_vm as backend_launch_vm
from vm_manager import (
    get_vm_snapshot,
    reboot_vm as backend_reboot_vm,
    shutdown_vm as backend_shutdown_vm,
    start_vm as backend_start_vm,
)
from ui.assets import AssetManager
from ui.theme import COLORS


class MiniWidgetApp(ctk.CTk):
    def __init__(self, vm_name):
        super().__init__()
        self.vm_name = vm_name
        self.assets = AssetManager()
        self.result_queue = queue.Queue()
        self.vm_data = None
        self.refresh_in_progress = False
        self.action_in_progress = False
        self.title(f"{vm_name} - KVM VM Manager")
        self.geometry("540x158")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["background"])
        self.assets.apply_window_icon(self)
        self.overrideredirect(True)

        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        self._drag_x = 0
        self._drag_y = 0
        self.build_ui()
        self.bind_drag_events()
        self.after(100, self.process_result_queue)
        self.after(150, self.refresh_vm)
        self.after(2000, self.periodic_refresh)

    def build_ui(self):
        self.card = ctk.CTkFrame(
            self,
            fg_color=COLORS["card"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.card.pack(fill="both", expand=True, padx=7, pady=7)
        self.card.grid_columnconfigure(1, weight=1)

        logo_container = ctk.CTkFrame(
            self.card,
            width=66,
            height=66,
            fg_color="#1B2021",
            corner_radius=13,
            border_width=1,
            border_color="#2D3233",
        )
        logo_container.grid(row=0, column=0, rowspan=2, padx=(16, 14), pady=22)
        logo_container.grid_propagate(False)

        os_name = self.get_vm_os()
        os_image = self.assets.get_os_image(os_name, size=(44, 44))

        if os_image:
            self.logo_label = ctk.CTkLabel(logo_container, text="", image=os_image)
            self.logo_label.image = os_image
        else:
            self.logo_label = ctk.CTkLabel(
                logo_container,
                text=self.assets.get_fallback(os_name),
                font=ctk.CTkFont(size=27, weight="bold"),
                text_color=COLORS["text"],
            )

        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(self.card, fg_color="transparent")
        info.grid(row=0, column=1, rowspan=2, sticky="w", pady=20)

        self.name_label = ctk.CTkLabel(
            info,
            text=self.vm_name,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.name_label.pack(anchor="w")

        status_frame = ctk.CTkFrame(info, fg_color="transparent")
        status_frame.pack(anchor="w", pady=(7, 0))

        self.status_dot = ctk.CTkLabel(
            status_frame,
            text="●",
            width=18,
            font=ctk.CTkFont(size=18),
            text_color=COLORS["working"],
        )
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Consultando...",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
        )
        self.status_label.pack(side="left")

        self.connection_label = ctk.CTkLabel(
            info,
            text=self.get_connection_label(),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
        )
        self.connection_label.pack(anchor="w", pady=(4, 0))

        actions = ctk.CTkFrame(self.card, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=(12, 34), pady=20)

        self.start_button = self.create_action_button(
            actions,
            "▶",
            lambda: self.run_action(backend_start_vm, "Iniciando..."),
        )
        self.stop_button = self.create_action_button(
            actions,
            "■",
            lambda: self.run_action(backend_shutdown_vm, "Desligando..."),
        )
        self.reboot_button = self.create_action_button(
            actions,
            "↻",
            lambda: self.run_action(backend_reboot_vm, "Reiniciando..."),
        )
        self.connect_button = self.create_action_button(
            actions,
            "▣",
            lambda: self.run_action(backend_launch_vm, "Conectando...", allow_dict=True),
        )

        for column, button in enumerate(
            (self.start_button, self.stop_button, self.reboot_button, self.connect_button)
        ):
            button.grid(row=0, column=column, padx=4)

        self.close_button = ctk.CTkButton(
            self.card,
            text="×",
            width=26,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["button_hover"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=17),
            command=self.destroy,
        )
        self.close_button.place(relx=1.0, x=-11, y=11, anchor="ne")
        self.update_button_states(False)

    def create_action_button(self, master, text, command):
        return ctk.CTkButton(
            master,
            text=text,
            width=43,
            height=43,
            corner_radius=10,
            fg_color=COLORS["button"],
            hover_color=COLORS["button_hover"],
            border_width=1,
            border_color="#343A3B",
            font=ctk.CTkFont(size=17, weight="bold"),
            command=command,
        )

    def bind_drag_events(self):
        for widget in (self.card, self.name_label, self.status_label, self.connection_label):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def do_drag(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def get_vm_os(self):
        config = get_vm_config(self.vm_name) or {}
        return config.get("os", "linux")

    def get_connection_label(self):
        config = get_vm_config(self.vm_name) or {}
        connection = str(config.get("connection", "ui")).lower()
        if connection == "viewer":
            connection = "ui"
        names = {"ui": "virt-viewer", "ssh": "SSH", "anydesk": "AnyDesk"}
        return f"Conexão: {names.get(connection, connection)}"

    def is_running(self):
        if not self.vm_data:
            return False
        return str(self.vm_data.get("status", "")).lower() in ("running", "executando")

    def update_view(self):
        self.connection_label.configure(text=self.get_connection_label())

        if not self.vm_data:
            self.status_dot.configure(text_color=COLORS["red"])
            self.status_label.configure(text="VM não encontrada")
            self.update_button_states(False, enabled=False)
            return

        running = self.is_running()
        self.status_dot.configure(text_color=COLORS["green"] if running else COLORS["red"])
        self.status_label.configure(
            text="Executando" if running else "Desligado",
            text_color=COLORS["text_secondary"],
        )
        self.update_button_states(running)

    def update_button_states(self, running, enabled=True):
        if not enabled or self.action_in_progress:
            start = stop = reboot = connect = "disabled"
        else:
            start = "disabled" if running else "normal"
            stop = "normal" if running else "disabled"
            reboot = "normal" if running else "disabled"
            connect = "normal"

        self.start_button.configure(state=start)
        self.stop_button.configure(state=stop)
        self.reboot_button.configure(state=reboot)
        self.connect_button.configure(state=connect)

    def refresh_vm(self):
        if self.refresh_in_progress:
            return
        self.refresh_in_progress = True
        threading.Thread(target=self.refresh_worker, daemon=True).start()

    def refresh_worker(self):
        try:
            data = get_vm_snapshot(self.vm_name)
            self.result_queue.put({"type": "widget_refresh", "success": True, "data": data})
        except Exception as error:
            self.result_queue.put({
                "type": "widget_refresh",
                "success": False,
                "message": str(error),
            })

    def periodic_refresh(self):
        self.refresh_vm()
        self.after(2000, self.periodic_refresh)

    def run_action(self, action, status_text, allow_dict=False):
        if self.action_in_progress:
            return
        self.action_in_progress = True
        self.status_dot.configure(text_color=COLORS["working"])
        self.status_label.configure(text=status_text)
        self.update_button_states(self.is_running())
        threading.Thread(
            target=self.action_worker,
            args=(action, allow_dict),
            daemon=True,
        ).start()

    def action_worker(self, action, allow_dict):
        try:
            result = action(self.vm_name)
            if allow_dict or isinstance(result, dict):
                success = bool(result.get("success"))
                message = result.get("message", "Operation completed.")
            else:
                success = getattr(result, "returncode", 1) == 0
                message = (
                    result.stderr.strip()
                    if not success and getattr(result, "stderr", None)
                    else "Operation completed."
                )
            self.result_queue.put({
                "type": "widget_action",
                "success": success,
                "message": message,
            })
        except Exception as error:
            self.result_queue.put({
                "type": "widget_action",
                "success": False,
                "message": str(error),
            })

    def process_result_queue(self):
        try:
            while True:
                result = self.result_queue.get_nowait()
                result_type = result.get("type")

                if result_type == "widget_refresh":
                    self.refresh_in_progress = False
                    if result.get("success"):
                        self.vm_data = result.get("data")
                        if not self.action_in_progress:
                            self.update_view()
                    else:
                        print("Widget refresh error:", result.get("message"))

                elif result_type == "widget_action":
                    self.action_in_progress = False
                    if not result.get("success"):
                        print("Widget action error:", result.get("message"))
                    self.refresh_vm()
                    self.after(1200, self.refresh_vm)
                    self.after(3000, self.refresh_vm)
        except queue.Empty:
            pass

        self.after(100, self.process_result_queue)


def run_widget(vm_name):
    app = MiniWidgetApp(vm_name)
    app.mainloop()
