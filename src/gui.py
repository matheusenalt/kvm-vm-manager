import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from vm_manager import (
    get_all_vms_info,
    start_vm,
    shutdown_vm,
    reboot_vm
)

from launcher import launch_vm


class VMManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.set_title("KVM VM Manager")
        self.set_default_size(700, 500)

        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12
        )

        self.main_box.set_margin_top(20)
        self.main_box.set_margin_bottom(20)
        self.main_box.set_margin_start(20)
        self.main_box.set_margin_end(20)

        self.set_child(self.main_box)

        header_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10
        )

        self.main_box.append(header_box)

        title = Gtk.Label(label="KVM VM Manager")
        title.set_xalign(0)
        title.set_hexpand(True)

        header_box.append(title)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect(
            "clicked",
            self.on_refresh_clicked
        )

        header_box.append(refresh_button)

        self.vm_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10
        )

        self.main_box.append(self.vm_container)

        self.load_vms()

    def clear_vm_container(self):
        child = self.vm_container.get_first_child()

        while child is not None:
            next_child = child.get_next_sibling()
            self.vm_container.remove(child)
            child = next_child

    def load_vms(self):
        self.clear_vm_container()

        vms = get_all_vms_info()

        if not vms:
            label = Gtk.Label(
                label="No virtual machines found."
            )

            label.set_xalign(0)
            self.vm_container.append(label)
            return

        for vm in vms:
            self.create_vm_card(vm)

    def create_vm_card(self, vm):
        frame = Gtk.Frame()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8
        )

        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        frame.set_child(box)

        name = Gtk.Label(
            label=f"VM: {vm['name']}"
        )
        name.set_xalign(0)

        status = Gtk.Label(
            label=f"Status: {vm['status']}"
        )
        status.set_xalign(0)

        vcpus = Gtk.Label(
            label=(
                f"vCPU: "
                f"{vm['vcpus'] if vm['vcpus'] else 'Unknown'}"
            )
        )
        vcpus.set_xalign(0)

        ram = Gtk.Label(
            label=(
                f"RAM: "
                f"{vm['ram'] if vm['ram'] else 'Unknown'}"
            )
        )
        ram.set_xalign(0)

        ip = Gtk.Label(
            label=(
                f"IP: "
                f"{vm['ip'] if vm['ip'] else 'Unknown'}"
            )
        )
        ip.set_xalign(0)

        box.append(name)
        box.append(status)
        box.append(vcpus)
        box.append(ram)
        box.append(ip)

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8
        )

        box.append(button_box)

        start_button = Gtk.Button(label="Start")
        start_button.connect(
            "clicked",
            self.on_start_clicked,
            vm["name"]
        )

        launch_button = Gtk.Button(label="Launch")
        launch_button.connect(
            "clicked",
            self.on_launch_clicked,
            vm["name"]
        )

        reboot_button = Gtk.Button(label="Reboot")
        reboot_button.connect(
            "clicked",
            self.on_reboot_clicked,
            vm["name"]
        )

        shutdown_button = Gtk.Button(label="Shutdown")
        shutdown_button.connect(
            "clicked",
            self.on_shutdown_clicked,
            vm["name"]
        )

        button_box.append(start_button)
        button_box.append(launch_button)
        button_box.append(reboot_button)
        button_box.append(shutdown_button)

        self.vm_container.append(frame)

    def on_refresh_clicked(self, button):
        self.load_vms()

    def on_start_clicked(self, button, vm_name):
        result = start_vm(vm_name)

        if result.returncode != 0:
            print(f"Could not start VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())
        else:
            print(f"VM '{vm_name}' started successfully.")

        self.load_vms()

    def on_launch_clicked(self, button, vm_name):
        result = launch_vm(vm_name)

        print(result["message"])

        self.load_vms()

    def on_reboot_clicked(self, button, vm_name):
        result = reboot_vm(vm_name)

        if result.returncode != 0:
            print(f"Could not reboot VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())
        else:
            print(f"Reboot signal sent to VM '{vm_name}'.")

        self.load_vms()

    def on_shutdown_clicked(self, button, vm_name):
        result = shutdown_vm(vm_name)

        if result.returncode != 0:
            print(f"Could not shutdown VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())
        else:
            print(f"Shutdown signal sent to VM '{vm_name}'.")

        self.load_vms()


class VMManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="com.kvmvmmanager.app"
        )

    def do_activate(self):
        window = VMManagerWindow(self)
        window.present()


app = VMManagerApp()

app.run(None)