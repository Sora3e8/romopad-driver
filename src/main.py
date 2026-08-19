#!/bin/env python
import argparse
import signal
import sys
import textwrap
import libs.service_controller as service_controller
interrupt_attempts = 0

def handle_interrtupt(sig,frame):
    global interrupt_attempts
    
    interrupt_attempts = interrupt_attempts + 1
    # Gives program last chance to close cleanly
    # Gets killed if it fails to do so, sesion lock has to be removed manually then
    if interrupt_attempts<2:
        print('\b\b\r')
        service_controller.service.stop()
    else:
        sys.exit(0)


prog_descr = '''User level macropad driver designed for Romoral 12 key macropad.
Allows to change Key codes emitted by the macropad eg. output "B" => "KP_1" or execute system commands. 
It's meant as supplement for original untrustyworthy Chinese driver, which is otherwise only availabled for Windows.'''

signal.signal(signal.SIGINT,handle_interrtupt)
prog_argparser = argparse.ArgumentParser(prog="romopad",formatter_class=argparse.RawDescriptionHelpFormatter, description = textwrap.dedent(prog_descr))
prog_argparser.add_argument("--svc",dest = "command", choices = ["start","stop"], help = "Starts or stops driver, note that the start is blocking.")
prog_argparser.add_argument("--debug", dest = "show_debug",required=False, nargs= "?",const = True ,default= False)


def main():
    if len(sys.argv) >1:
        args=vars(prog_argparser.parse_args(sys.argv[1:]))
        if args["show_debug"]: print(args)
        command = args.pop("command")
        getattr(service_controller.service,command)(**args)

    else:
        prog_argparser.print_help()
 
if __name__ == "__main__":
    main()


