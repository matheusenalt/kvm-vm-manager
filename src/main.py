import sys
import subprocess


def run_virsh_command(command_args):
    """
    Executes a virsh command using the qemu:///system connection.

    Returns the complete subprocess result, including:
    - stdout
    - stderr
    - returncode
    """

    result = subprocess.run(
        ["virsh", "--connect", "qemu:///system"] + command_args,
        capture_output=True,
        text=True
    )

    return result


def get_vm_status(vm_name):
    """
    Gets the current state of a virtual machine.

    Possible examples:
    - running
    - shut off
    - paused
    """

    result = run_virsh_command(
        ["domstate", vm_name]
    )

    
    if result.returncode != 0:
        return None

    return result.stdout.strip()


def start_vm(vm_name):
    """
    Starts a virtual machine.
    """

    return run_virsh_command(
        ["start", vm_name]
    )


def shutdown_vm(vm_name):
    """
    Sends a normal shutdown request to the virtual machine.
    """

    return run_virsh_command(
        ["shutdown", vm_name]
    )


def reboot_vm(vm_name):
    """
    Sends a reboot request to the virtual machine.
    """

    return run_virsh_command(
        ["reboot", vm_name]
    )


def main():
    """
    Main entry point of the application.

    Expected usage:

    python src/main.py <vm_name> <command>

    Example:

    python src/main.py win10 status
    """

    
    if len(sys.argv) < 3:
        print("Usage: python src/main.py <vm_name> <command>")
        print()
        print("Commands:")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")
        return


    vm_name = sys.argv[1]

    
    command = sys.argv[2].lower()

    
    status = get_vm_status(vm_name)

    if status is None:
        print(f"Error: VM '{vm_name}' was not found.")
        return

    

    if command == "status":
        print(f"VM: {vm_name}")
        print(f"Status: {status}")

   

    elif command == "start":

        if status in ("running", "executando"):
            print(f"VM '{vm_name}' is already running.")
            return

        result = start_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not start VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"VM '{vm_name}' started successfully.")

    

    elif command == "shutdown":

        if status in ("shut off", "desligado"):
            print(f"VM '{vm_name}' is already powered off.")
            return

        # This line was missing in your previous code
        result = shutdown_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not shutdown VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"Shutdown signal sent to VM '{vm_name}'.")

    

    elif command == "reboot":

        if status in ("shut off", "desligado"):
            print(f"Error: VM '{vm_name}' is powered off.")
            return

        result = reboot_vm(vm_name)

        if result.returncode != 0:
            print(f"Error: could not reboot VM '{vm_name}'.")

            if result.stderr:
                print(result.stderr.strip())

            return

        print(f"Reboot signal sent to VM '{vm_name}'.")

    

    else:
        print(f"Error: unknown command '{command}'.")
        print()
        print("Available commands:")
        print("  status")
        print("  start")
        print("  shutdown")
        print("  reboot")


# Runs main() only when this file is executed directly
if __name__ == "__main__":
    main()