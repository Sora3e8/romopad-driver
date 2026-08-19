import sys
import os
import macropad_daemon
import threading
import time
import libs.socket_controller as socket_controller
interrupt_attempts=0
DEBUG = False


# Logical section service
class service():
    service_daemon= None
    # Starts service daemon, checks if no other session is running by checking if there's existing socketfile
    @staticmethod
    def start(show_debug=False):
        if socket_controller.check_session_blocked():
             print("Another active session detected.\n","Before running stop the previous session.\n","If no session active remove the session lock:",socket_controller.sock_dir)
             exit() 
        else:
            threading.Thread(target=lambda: socket_controller.socket_server.start(show_debug=show_debug)).start()
            service_daemon = threading.Thread(target=lambda: macropad_daemon.driver.start(show_debug=show_debug)) 
            service_daemon.daemon = True
            service_daemon.start()

    # Stops service daemon
    @staticmethod
    def stop(show_debug = False):
        socket_controller.socket_client.send_command("stop")

    @staticmethod
    def handler(command,args):
        getattr(service, command)(args)
        
# Config should be saved in '~/.confing/romopad/layout.xml'

