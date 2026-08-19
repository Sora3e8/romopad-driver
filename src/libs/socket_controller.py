import os
import socket as sock
sock_dir="/tmp/romopadsvc_control.socket"
keep_sock = True
DEBUG = False
# Logical section daemon session
class socket_server:
    global sock_dir
    
    def stop(show_debug = False):
        global keep_sock
        global DEBUG
        show_debug=show_debug
        print("Stopping service")
        keep_sock = False

    handler = {"stop":stop}
    
    def start(show_debug = False):
        global keep_sock 
        global DEBUG
        DEBUG = show_debug
        try:
            intsock = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            intsock.bind(sock_dir)
        except Exception as e:
            print("Creating socket failed with Exception:\n",e)
            exit()

        # Session loop, restarts after session ends
        while keep_sock:
            try:
                intsock.listen(1)
                sock_session, clidress = intsock.accept()
            except Exception as e:
                keep_sock = False
                print("Starting daemon listener failed with Exception:\n",e)
                break
            # Data loop, closes upon transfer complete
            while True:
                data = sock_session.recv(1024).decode()
                if data in socket_server.handler:
                    socket_server.handler[data]()
                else:
                    if not data: break

        sock_session.close()
        os.unlink(sock_dir) if os.path.exists(sock_dir) else next

class socket_client:
    @staticmethod
    def check_if_alive():
        try:
            test_sock = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            test_sock.connect(sock_dir)
            test_sock.close()
        except Exception as e:
            # Checks if connection gets refused
            # If so socket is dead and can be closed
            if e.errno == 111:
                os.unlink(sock_dir)
                return False
            else:
                return True
        return False

    # Enables clear exiting and control over svc daemon
    @staticmethod
    def send_command(cmd):
        if os.path.exists(sock_dir):
            try:
                clisock = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
                clisock.connect(sock_dir)
                clisock.send(cmd.encode())
                clisock.close()
            except Exception as e:
                if e.errno == 111:
                    print("Unable to connect, session seems to be dead")
                    print("If service not running remove session lock and restart service:\n",sock_dir)
                else:
                    print(e)
        else:
            print("No session found. Is service running?")


def check_session_blocked():
    return os.path.exists(sock_dir) or os.path.exists(sock_dir) and socket_client.check_if_alive()
