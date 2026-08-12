import queue
import threading

import customtkinter as ctk

from connection import (
    load_vm_config,
    save_vm_config,
)

from launcher import (
    launch_vm as backend_launch_vm,
)

from os_catalog import get_logo_key

from vm_manager import (
    create_vm as backend_create_vm,
    get_all_vms_info,
    reboot_vm as backend_reboot_vm,
    shutdown_vm as backend_shutdown_vm,
    start_vm as backend_start_vm,
)

from .assets import AssetManager

from .dialogs.create_vm import (
    CreateVMDialog,
)

from .dialogs.vm_settings import (
    VMSettingsDialog,
)

from .theme import COLORS
from .vm_card import VMCard


class VMManagerApp(
    ctk.CTk
):
    def __init__(self):
        super().__init__()

        self.assets = AssetManager()
        self.assets.apply_window_icon(self)

        self.result_queue = (
            queue.Queue()
        )

        self.vm_data = []
        self.vm_cards = {}

        self.empty_label = None

        self.creation_in_progress = (
            False
        )

        self.refresh_in_progress = (
            False
        )

        self.title(
            "KVM VM Manager"
        )

        self.geometry(
            "1280x760"
        )

        self.minsize(
            1000,
            600,
        )

        self.configure(
            fg_color=COLORS[
                "background"
            ]
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            2,
            weight=1,
        )

        self.build_title()
        self.build_header()
        self.build_vm_list()
        self.build_footer()

        self.refresh_vms()

        self.after(
            100,
            self.process_result_queue,
        )

    def build_title(self):
        title_frame = (
            ctk.CTkFrame(
                self,
                height=75,
                fg_color=COLORS[
                    "header"
                ],
                corner_radius=0,
            )
        )

        title_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        title = ctk.CTkLabel(
            title_frame,
            text="KVM VM Manager",
            font=ctk.CTkFont(
                size=30,
                weight="bold",
            ),
            text_color=COLORS[
                "text"
            ],
        )

        title.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        separator = ctk.CTkFrame(
            title_frame,
            height=1,
            fg_color="#292E2F",
        )

        separator.pack(
            side="bottom",
            fill="x",
        )

    def build_header(self):
        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        header.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=42,
            pady=(25, 18),
        )

        header.grid_columnconfigure(
            1,
            weight=1,
        )

        app_image = self.assets.get_app_image(size=(34, 34))
        icon = ctk.CTkLabel(
            header,
            text="" if app_image else "▣",
            image=app_image,
            font=ctk.CTkFont(size=27),
            text_color=COLORS["text"],
        )
        if app_image:
            icon.image = app_image
        icon.grid(row=0, column=0, padx=(0, 12))

        title = ctk.CTkLabel(
            header,
            text="Máquinas Virtuais",
            font=ctk.CTkFont(
                size=25,
                weight="bold",
            ),
            text_color=COLORS[
                "text"
            ],
        )

        title.grid(
            row=0,
            column=1,
            sticky="w",
        )

        self.create_vm_button = (
            ctk.CTkButton(
                header,
                text="+  Criar Nova VM",
                width=170,
                height=48,
                corner_radius=10,
                fg_color=COLORS[
                    "accent"
                ],
                hover_color=COLORS[
                    "accent_hover"
                ],
                font=ctk.CTkFont(
                    size=15,
                    weight="bold",
                ),
                command=(
                    self
                    .open_create_vm_dialog
                ),
            )
        )

        self.create_vm_button.grid(
            row=0,
            column=2,
            padx=(0, 10),
        )

        self.refresh_button = (
            ctk.CTkButton(
                header,
                text="↻  Atualizar",
                width=150,
                height=48,
                corner_radius=10,
                fg_color=COLORS[
                    "button"
                ],
                hover_color=COLORS[
                    "button_hover"
                ],
                border_width=1,
                border_color=COLORS[
                    "border"
                ],
                font=ctk.CTkFont(
                    size=16
                ),
                command=(
                    self.refresh_vms
                ),
            )
        )

        self.refresh_button.grid(
            row=0,
            column=3,
        )

    def build_vm_list(self):
        self.scroll_frame = (
            ctk.CTkScrollableFrame(
                self,
                fg_color="transparent",
                corner_radius=0,
            )
        )

        self.scroll_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=42,
            pady=(0, 15),
        )

        self.scroll_frame.grid_columnconfigure(
            0,
            weight=1,
        )

    def show_empty_state(self):
        if (
            self.empty_label
            is not None
        ):
            return

        self.empty_label = (
            ctk.CTkLabel(
                self.scroll_frame,
                text=(
                    "Nenhuma máquina "
                    "virtual encontrada."
                ),
                font=ctk.CTkFont(
                    size=17
                ),
                text_color=COLORS[
                    "text_secondary"
                ],
            )
        )

        self.empty_label.grid(
            row=0,
            column=0,
            pady=50,
        )

    def hide_empty_state(self):
        if (
            self.empty_label
            is not None
        ):
            self.empty_label.destroy()
            self.empty_label = None

    def sync_vms(self):
        if not self.vm_data:
            for card in (
                self.vm_cards.values()
            ):
                card.destroy()

            self.vm_cards.clear()

            self.show_empty_state()

            return

        self.hide_empty_state()

        current_names = set(
            self.vm_cards.keys()
        )

        new_names = {
            vm["name"]
            for vm in self.vm_data
        }

        for vm_name in (
            current_names
            - new_names
        ):
            card = (
                self.vm_cards.pop(
                    vm_name
                )
            )

            card.destroy()

        for index, vm in enumerate(
            self.vm_data
        ):
            vm_name = vm[
                "name"
            ]

            if (
                vm_name
                in self.vm_cards
            ):
                card = (
                    self.vm_cards[
                        vm_name
                    ]
                )

                card.update_vm_data(
                    vm
                )

            else:
                card = VMCard(
                    self.scroll_frame,
                    vm,
                    self,
                    self.assets,
                )

                self.vm_cards[
                    vm_name
                ] = card

            card.grid(
                row=index,
                column=0,
                sticky="ew",
                pady=7,
            )

    def build_footer(self):
        footer = ctk.CTkFrame(
            self,
            height=62,
            fg_color=COLORS[
                "header"
            ],
            corner_radius=0,
        )

        footer.grid(
            row=3,
            column=0,
            sticky="ew",
        )

        separator = ctk.CTkFrame(
            footer,
            height=1,
            fg_color="#292E2F",
        )

        separator.pack(
            side="top",
            fill="x",
        )

        self.total_label = (
            ctk.CTkLabel(
                footer,
                text=(
                    "▤   Total de VMs: 0"
                ),
                font=ctk.CTkFont(
                    size=16
                ),
                text_color=COLORS[
                    "text"
                ],
            )
        )

        self.total_label.pack(
            side="left",
            padx=42,
            pady=20,
        )

    def detect_os(self, vm_name):
        name = vm_name.lower()
        if "win" in name:
            return "windows11"
        if "ubuntu" in name:
            return "ubuntu"
        if "mint" in name:
            return "linuxmint"
        if "debian" in name:
            return "debian"
        if "kali" in name:
            return "kali"
        if "fedora" in name:
            return "fedora"
        if "arch" in name:
            return "archlinux"
        if "manjaro" in name:
            return "manjaro"
        if "centos" in name:
            return "centos"
        return "other-linux"

    def prepare_vm_data(
        self,
        backend_data,
    ):
        prepared = []

        config = load_vm_config()

        for vm in backend_data:
            vm_copy = dict(
                vm
            )

            vm_config = config.get(
                vm_copy["name"],
                {},
            )

            if not isinstance(
                vm_config,
                dict,
            ):
                vm_config = {}

            vm_copy[
                "os"
            ] = (
                vm_config.get("os")
                or vm_copy.get("os")
                or self.detect_os(
                    vm_copy["name"]
                )
            )
            vm_copy["logo"] = get_logo_key(vm_copy["os"])

            prepared.append(
                vm_copy
            )

        return prepared

    def open_vm_settings(
        self,
        vm_data,
    ):
        VMSettingsDialog(
            self,
            vm_data,
        )

    def open_create_vm_dialog(
        self
    ):
        CreateVMDialog(
            self
        )

    def create_vm_from_dialog(
        self,
        dialog,
        data,
    ):
        if (
            self.creation_in_progress
        ):
            dialog.show_result(
                (
                    "Já existe uma criação "
                    "de VM em andamento."
                ),
                success=False,
            )

            return

        self.creation_in_progress = (
            True
        )

        dialog.set_busy(
            True
        )

        dialog.show_result(
            (
                "Executando virt-install. "
                "Isso pode levar alguns "
                "segundos..."
            ),
            success=True,
        )

        threading.Thread(
            target=self.create_vm_worker,
            args=(
                dialog,
                data,
            ),
            daemon=True,
        ).start()

    def create_vm_worker(
        self,
        dialog,
        data,
    ):
        try:
            result = backend_create_vm(
                name=data["name"],
                os_name=data["os"],
                vcpus=data["vcpus"],
                ram_gb=data["ram_gb"],
                disk_gb=data[
                    "disk_gb"
                ],
                iso_path=data[
                    "iso_path"
                ],
            )

        except Exception as error:
            result = {
                "success": False,
                "message": str(error),
            }

        self.result_queue.put({
            "type": "create_vm",
            "result": result,
            "dialog": dialog,
            "data": data,
        })

    def save_created_vm_metadata(
        self,
        name,
        os_name,
    ):
        config = load_vm_config()

        current = config.get(
            name,
            {},
        )

        if not isinstance(
            current,
            dict,
        ):
            current = {}

        current[
            "os"
        ] = os_name

        current.setdefault(
            "connection",
            "ui",
        )

        config[
            name
        ] = current

        return save_vm_config(
            config
        )

    def handle_create_vm_result(
        self,
        payload,
    ):
        self.creation_in_progress = (
            False
        )

        result = payload.get(
            "result",
            {},
        )

        dialog = payload.get(
            "dialog"
        )

        data = payload.get(
            "data",
            {},
        )

        success = bool(
            result.get(
                "success"
            )
        )

        message = result.get(
            "message",
            "VM creation finished.",
        )

        if success:
            metadata_result = (
                self
                .save_created_vm_metadata(
                    data.get(
                        "name"
                    ),
                    data.get(
                        "os"
                    ),
                )
            )

            if isinstance(
                metadata_result,
                dict,
            ):
                metadata_success = bool(
                    metadata_result.get(
                        "success"
                    )
                )

            else:
                metadata_success = bool(
                    metadata_result
                )

            if not metadata_success:
                message += (
                    " Warning: VM criada, "
                    "mas config.json não "
                    "pôde ser atualizado."
                )

        try:
            if (
                dialog is not None
                and dialog.winfo_exists()
            ):
                dialog.set_busy(
                    False
                )

                dialog.show_result(
                    message,
                    success=success,
                )

                if success:
                    dialog.after(
                        1200,
                        dialog.destroy,
                    )

        except Exception:
            pass

        if not success:
            print(
                "Create VM error:",
                message,
            )

            return

        self.after(
            400,
            lambda: self.refresh_vms(
                show_indicator=False
            ),
        )

        self.after(
            1400,
            lambda: self.refresh_vms(
                show_indicator=False
            ),
        )

    def refresh_vms(
        self,
        show_indicator=True,
    ):
        if self.refresh_in_progress:
            return

        self.refresh_in_progress = (
            True
        )

        if show_indicator:
            self.refresh_button.configure(
                state="disabled",
                text="↻  Atualizando...",
            )

        threading.Thread(
            target=self.refresh_worker,
            args=(
                show_indicator,
            ),
            daemon=True,
        ).start()

    def refresh_worker(
        self,
        show_indicator,
    ):
        try:
            data = (
                get_all_vms_info()
            )

            self.result_queue.put({
                "type": "refresh",
                "success": True,
                "data": data,
                "show_indicator": (
                    show_indicator
                ),
            })

        except Exception as error:
            self.result_queue.put({
                "type": "refresh",
                "success": False,
                "message": str(error),
                "show_indicator": (
                    show_indicator
                ),
            })

    def start_vm(
        self,
        vm_name,
        card,
    ):
        self.run_vm_action(
            vm_name,
            card,
            backend_start_vm,
            "Iniciando...",
        )

    def stop_vm(
        self,
        vm_name,
        card,
    ):
        self.run_vm_action(
            vm_name,
            card,
            backend_shutdown_vm,
            "Desligando...",
        )

    def reboot_vm(
        self,
        vm_name,
        card,
    ):
        self.run_vm_action(
            vm_name,
            card,
            backend_reboot_vm,
            "Reiniciando...",
        )

    def launch_vm(
        self,
        vm_name,
        card,
    ):
        self.run_vm_action(
            vm_name,
            card,
            backend_launch_vm,
            "Abrindo...",
        )

    def run_vm_action(
        self,
        vm_name,
        card,
        action,
        message,
    ):
        card.set_working_status(
            message
        )

        card.disable_actions()

        threading.Thread(
            target=self.action_worker,
            args=(
                vm_name,
                action,
            ),
            daemon=True,
        ).start()

    def action_worker(
        self,
        vm_name,
        action,
    ):
        try:
            result = action(
                vm_name
            )

            success = True

            message = (
                "Operation completed."
            )

            if isinstance(
                result,
                dict,
            ):
                success = result.get(
                    "success",
                    False,
                )

                message = result.get(
                    "message",
                    message,
                )

            else:
                success = (
                    result.returncode
                    == 0
                )

                if not success:
                    message = (
                        result.stderr.strip()
                        if result.stderr
                        else (
                            "VM operation "
                            "failed."
                        )
                    )

            self.result_queue.put({
                "type": "action",
                "success": success,
                "vm_name": vm_name,
                "message": message,
            })

        except Exception as error:
            self.result_queue.put({
                "type": "action",
                "success": False,
                "vm_name": vm_name,
                "message": str(error),
            })

    def process_result_queue(
        self
    ):
        try:
            while True:
                result = (
                    self.result_queue
                    .get_nowait()
                )

                result_type = (
                    result.get(
                        "type"
                    )
                )

                if (
                    result_type
                    == "refresh"
                ):
                    self.handle_refresh_result(
                        result
                    )

                elif (
                    result_type
                    == "action"
                ):
                    self.handle_action_result(
                        result
                    )

                elif (
                    result_type
                    == "create_vm"
                ):
                    self.handle_create_vm_result(
                        result
                    )

        except queue.Empty:
            pass

        self.after(
            100,
            self.process_result_queue,
        )

    def handle_refresh_result(
        self,
        result,
    ):
        self.refresh_in_progress = (
            False
        )

        if result.get(
            "show_indicator",
            True,
        ):
            self.refresh_button.configure(
                state="normal",
                text="↻  Atualizar",
            )

        if not result[
            "success"
        ]:
            print(
                "Refresh error:",
                result.get(
                    "message"
                ),
            )

            return

        self.vm_data = (
            self.prepare_vm_data(
                result["data"]
            )
        )

        self.sync_vms()

        self.total_label.configure(
            text=(
                f"▤   Total de VMs: "
                f"{len(self.vm_data)}"
            )
        )

    def handle_action_result(
        self,
        result,
    ):
        print(
            result.get(
                "message",
                "Operation completed.",
            )
        )

        self.refresh_vms(
            show_indicator=False
        )

        self.after(
            1500,
            lambda: self.refresh_vms(
                show_indicator=False
            ),
        )

        self.after(
            3500,
            lambda: self.refresh_vms(
                show_indicator=False
            ),
        )

        self.after(
            7000,
            lambda: self.refresh_vms(
                show_indicator=False
            ),
        )