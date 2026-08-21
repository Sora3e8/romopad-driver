#!/bin/env python

import argparse
import os
from posix import W_OK
import shutil as sh
import subprocess as sb
from typing import Any
import glob

UDEV_RULES_DIRECTORY: str = "/lib/udev/rules.d/"
SERVICE_DIRECTORIES= {"dinit":"/etc/dinit.d/user/","systemd":"/etc/systemd/user/"}


setup_parser = argparse.ArgumentParser(prog="setup", description="Setups the romopad-driver")
_ = setup_parser.add_argument("action", choices=["install", "uninstall"])

def main():
    action: list[Any] = vars(setup_parser.parse_args())["action"] #pyright: ignore[reportAny,reportExplicitAny]
    if action: globals()[action]() #pyright: ignore[reportArgumentType] 

def install():
    print("Checking permissions...")
    # Terminates if we do not have permission to write into "/lib/udev/rules.d"
    if not os.access("/lib/udev/rules.d/",W_OK):
        print("Insufficient permission, could not install udev rules.")
        print("Try to re-run with sudo.")
        return
    print("Installing udev rules")

    
    for rule in glob.glob(f"udev/*.rules"):
        res = sh.copy(f"{rule}",UDEV_RULES_DIRECTORY)
        if not res:
            print(f"Failed installing udev rule: udev/{rule}")
            break
    
    print("Reloading udev rules...")
    # Reload rules
    _ = sb.run(["udevadm", "control", "--reload-rules"])
    _ = sb.run(["udevadm", "trigger"])
    
    print("Detecting init system...")
    # Retrieves currently supported init systems
    init_systems:list[str] = os.listdir("services/") 
    # Checks what init system is used on device by checking name of pid 1
    init_system: str = sb.check_output("ps -p 1 -o comm=",text=True,shell=True).replace('\n','')
    
    print(f"Detected init system: {init_system}")
    # Terminates if we do not have service file for given init system
    if init_system not in init_systems:
        print(f"We're sorry, but {init_system} is not currently supported by romopad-driver.")
        print(f"Supported init systems are: {init_systems}")
        return
    
    print("Installing services.")
    for srv in glob.glob(f"services/{init_system}/*"):
        print(f"Copying service {srv} -> {SERVICE_DIRECTORIES[init_system]} ...")
        res = sh.copy(srv,SERVICE_DIRECTORIES[init_system])
        if not res: 
            print(f"Failed service: {SERVICE_DIRECTORIES[init_system]}{srv}")
            return

    print("Setup complete!")
 
def uninstall():

    # Terminates if we do not have permission to write into "/lib/udev/rules.d"
    if not os.access("/lib/udev/rules.d/",W_OK):
        print("Insufficient permission, could not uninstall udev rules.")
        print("Try to re-run with sudo.")
        return
    
    for rule in os.listdir(f"udev/"):
        if os.path.isfile(f"udev/{rule}") and rule.split(".")[-1]=="rules":
            os.remove(f"{UDEV_RULES_DIRECTORY}{rule}")


    # Retrieves currently supported init systems
    init_systems:list[str] = os.listdir("services/") 
    # Checks what init system is used on device by checking name of pid 1
    init_system: str = sb.check_output("ps -p 1 -o comm=",text=True,shell=True).replace('\n','')

    # Terminates if we do not have service file for given init system
    if init_system not in init_systems:
        print(f"We're sorry, but {init_system} is not currently supported by romopad-driver.")
        print(f"Supported init systems are: {init_systems}")
        return
    
    for srv in os.listdir(f"services/{init_system}/"):
        if os.path.isfile(f"services/{init_system}/{srv}"):
            os.remove(f"{SERVICE_DIRECTORIES[init_system]}{srv}")

if __name__ == "__main__":
    main()
