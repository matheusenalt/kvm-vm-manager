import customtkinter as ctk

from .theme import COLORS


class VMCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        vm_data,
        controller,
        assets,
    ):
        super().__init__(
            master,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
            height=140,
        )

        self.vm = vm_data
        self.controller = controller
        self.assets = assets

        self.grid_columnconfigure(
            1,
            weight=1,
        )

        self.build_ui()

    def build_ui(self):
        self.build_logo()
        self.build_info()
        self.build_status()
        self.build_actions()

    def build_logo(self):
        logo_container = ctk.CTkFrame(
            self,
            width=92,
            height=92,
            fg_color="#1B2021",
            corner_radius=14,
            border_width=1,
            border_color="#2D3233",
        )

        logo_container.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(20, 20),
            pady=20,
        )

        logo_container.grid_propagate(
            False
        )

        os_name = self.vm.get(
            "os",
            "linux",
        )

        os_image = (
            self.assets
            .get_os_image(os_name)
        )

        if os_image:
            logo = ctk.CTkLabel(
                logo_container,
                text="",
                image=os_image,
            )

            logo.image = os_image

        else:
            logo = ctk.CTkLabel(
                logo_container,
                text=(
                    self.assets
                    .get_fallback(os_name)
                ),
                font=ctk.CTkFont(
                    size=35,
                    weight="bold",
                ),
                text_color=COLORS["text"],
            )

        logo.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

    def build_info(self):
        info_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        info_frame.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="w",
            pady=20,
        )

        self.name_label = (
            ctk.CTkLabel(
                info_frame,
                text=self.vm["name"],
                font=ctk.CTkFont(
                    size=23,
                    weight="bold",
                ),
                text_color=COLORS[
                    "text"
                ],
                anchor="w",
            )
        )

        self.name_label.pack(
            anchor="w",
        )

        self.detail_label = (
            ctk.CTkLabel(
                info_frame,
                text=(
                    self.get_details_text()
                ),
                font=ctk.CTkFont(
                    size=15
                ),
                text_color=COLORS[
                    "text_secondary"
                ],
                anchor="w",
            )
        )

        self.detail_label.pack(
            anchor="w",
            pady=(8, 0),
        )

    def get_details_text(self):
        vcpus = (
            self.vm.get("vcpus")
            or "Unknown"
        )

        ram = (
            self.vm.get("ram")
            or "Unknown"
        )

        ip = (
            self.vm.get("ip")
            or "No IP"
        )

        return (
            f"{vcpus} vCPU"
            f"   •   {ram} RAM"
            f"   •   {ip}"
        )

    def update_vm_data(
        self,
        new_data,
    ):
        old_status = self.vm.get(
            "status"
        )

        old_ip = self.vm.get(
            "ip"
        )

        old_ram = self.vm.get(
            "ram"
        )

        old_vcpus = self.vm.get(
            "vcpus"
        )

        self.vm = new_data

        if (
            old_ip
            != new_data.get("ip")
            or old_ram
            != new_data.get("ram")
            or old_vcpus
            != new_data.get("vcpus")
        ):
            self.detail_label.configure(
                text=(
                    self.get_details_text()
                )
            )

        if (
            old_status
            != new_data.get("status")
        ):
            self.update_status()

        self.update_action_buttons()

    def build_status(self):
        separator = ctk.CTkFrame(
            self,
            width=1,
            height=70,
            fg_color=COLORS[
                "separator"
            ],
        )

        separator.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(20, 20),
        )

        status_frame = (
            ctk.CTkFrame(
                self,
                fg_color="transparent",
            )
        )

        status_frame.grid(
            row=0,
            column=3,
            rowspan=2,
            padx=(0, 25),
        )

        running = self.is_running()

        status_color = (
            COLORS["green"]
            if running
            else COLORS["red"]
        )

        status_text = (
            "Executando"
            if running
            else "Desligado"
        )

        self.status_dot = (
            ctk.CTkLabel(
                status_frame,
                text="●",
                font=ctk.CTkFont(
                    size=24
                ),
                text_color=status_color,
                width=24,
            )
        )

        self.status_dot.pack(
            side="left",
            padx=(0, 8),
        )

        self.status_label = (
            ctk.CTkLabel(
                status_frame,
                text=status_text,
                font=ctk.CTkFont(
                    size=17
                ),
                text_color=COLORS[
                    "text"
                ],
            )
        )

        self.status_label.pack(
            side="left",
        )

        separator_right = (
            ctk.CTkFrame(
                self,
                width=1,
                height=70,
                fg_color=COLORS[
                    "separator"
                ],
            )
        )

        separator_right.grid(
            row=0,
            column=4,
            rowspan=2,
            padx=(0, 22),
        )

    def is_running(self):
        status = str(
            self.vm.get(
                "status",
                "",
            )
        ).lower()

        return status in (
            "running",
            "executando",
        )

    def update_status(self):
        running = self.is_running()

        self.status_dot.configure(
            text_color=(
                COLORS["green"]
                if running
                else COLORS["red"]
            )
        )

        self.status_label.configure(
            text=(
                "Executando"
                if running
                else "Desligado"
            )
        )

    def set_working_status(
        self,
        message,
    ):
        self.status_dot.configure(
            text_color=COLORS[
                "working"
            ]
        )

        self.status_label.configure(
            text=message
        )

    def build_actions(self):
        actions = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        actions.grid(
            row=0,
            column=5,
            rowspan=2,
            padx=(0, 22),
        )

        self.start_button = (
            self.create_button(
                actions,
                "▶",
                lambda: (
                    self.controller
                    .start_vm(
                        self.vm["name"],
                        self,
                    )
                ),
                0,
            )
        )

        self.stop_button = (
            self.create_button(
                actions,
                "■",
                lambda: (
                    self.controller
                    .stop_vm(
                        self.vm["name"],
                        self,
                    )
                ),
                1,
            )
        )

        self.reboot_button = (
            self.create_button(
                actions,
                "↻",
                lambda: (
                    self.controller
                    .reboot_vm(
                        self.vm["name"],
                        self,
                    )
                ),
                2,
            )
        )

        self.launch_button = (
            self.create_button(
                actions,
                "▣",
                lambda: (
                    self.controller
                    .launch_vm(
                        self.vm["name"],
                        self,
                    )
                ),
                3,
            )
        )

        self.settings_button = (
            self.create_button(
                actions,
                "⚙",
                lambda: (
                    self.controller
                    .open_vm_settings(
                        self.vm
                    )
                ),
                4,
            )
        )

        self.update_action_buttons()

    def create_button(
        self,
        master,
        icon,
        command,
        column,
    ):
        button = ctk.CTkButton(
            master,
            text=icon,
            width=58,
            height=58,
            corner_radius=11,
            fg_color=COLORS["button"],
            hover_color=COLORS[
                "button_hover"
            ],
            border_width=1,
            border_color="#343A3B",
            font=ctk.CTkFont(
                size=22,
                weight="bold",
            ),
            command=command,
        )

        button.grid(
            row=0,
            column=column,
            padx=5,
        )

        return button

    def update_action_buttons(
        self
    ):
        running = self.is_running()

        self.start_button.configure(
            state=(
                "disabled"
                if running
                else "normal"
            )
        )

        self.stop_button.configure(
            state=(
                "normal"
                if running
                else "disabled"
            )
        )

        self.reboot_button.configure(
            state=(
                "normal"
                if running
                else "disabled"
            )
        )

        self.launch_button.configure(
            state="normal"
        )

        self.settings_button.configure(
            state="normal"
        )

    def disable_actions(self):
        self.start_button.configure(
            state="disabled"
        )

        self.stop_button.configure(
            state="disabled"
        )

        self.reboot_button.configure(
            state="disabled"
        )

        self.launch_button.configure(
            state="disabled"
        )