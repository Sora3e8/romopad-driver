from dotenv import load_dotenv
import asyncio
import evdev
import evdev.ecodes as e
import os
import subprocess as sp
import time
import libs.config_loader as config_loader
import threading
import sys
import datetime

supported_devs = [{"vendor":4489,"product":34880,"version":513}]
devnames = [{"name":"Acer Communications & Multimedia USB Composite Device","vendor":4489,"product":34880,"version":513}]
DEBUG = False

class macropad:
    clayers = []
    clayer = "0"
    keymap = None
    last_layer_change_stamp = None
    def layer_control(virtual_device,arg,key_value):
        global DEBUG
        time_stamp_now = datetime.datetime.now()
        if macropad.last_layer_change_stamp == None or (time_stamp_now-macropad.last_layer_change_stamp).microseconds/10> 100:
            if key_value == 0 and arg == "next":
                if macropad.clayers.index(macropad.clayer)+1 > (len(macropad.clayers)-1):
                    macropad.clayer = macropad.clayers[0]
                else:
                    macropad.clayer=macropad.clayers[macropad.clayers.index(macropad.clayer)+1]
                if DEBUG: print("Switched to next layer: ", macropad.clayer)

            if key_value == 0 and arg == "prev":
                if macropad.clayers.index(macropad.clayer)-1 > 0:
                    macropad.clayer = macropad.clayers[len(macropad.layers)-1]
                else:
                    macropad.clayer=macropad.clayers[macropad.clayers.index(macropad.clayer)-1]
                if DEBUG: print("Switched to prev layer: ", macropad.clayer)

            if key_value == 0:
                sp.Popen(f"./indicator.py {str(macropad.clayer)}",stderr=sp.DEVNULL,stdout=sp.DEVNULL,shell=True, start_new_session = True)

            macropad.last_layer_change_stamp = time_stamp_now



class driver:
    selected_device=None
    cap = None
    
    # This cannot be changed by user => Translates easy to understand keynames to signal codes emitted by device, used to translate user 
    # hardware layout names to emitted signals names see: macroboard_map.png
    hwtrans_layer = {
     "KEY_A":"KEY_01",
     "KEY_B":"KEY_02",
     "KEY_C":"KEY_03",
     "KEY_D":"KEY_04",
     "KEY_E":"KEY_05",
     "KEY_F":"KEY_06",
     "KEY_G":"KEY_07",
     "KEY_H":"KEY_08",
     "KEY_I":"KEY_09",
     "KEY_J":"KEY_10",
     "KEY_K":"KEY_11",
     "KEY_L":"KEY_12",
     "KEY_1":"NOB1_LT",
     "KEY_2":"NOB1",
     "KEY_3":"NOB1_RT",
     "KEY_4":"NOB2_LT",
     "KEY_5":"NOB2",
     "KEY_6":"NOB2_RT",
    }

    # Loads key events from layout map which will be used by virtual device and returns it as cap dict
    def load_capabilities(layout_map):
        global DEBUG
        key_ev_list = [e.BTN_MOUSE]
        mouse_evs = [e.ABS_X]

        if DEBUG: print("Loading key events...")
        
        for bind in layout_map["global"].keys():
            if layout_map["global"][bind]["type"] == "key":
                if "+" in layout_map["global"][bind]["args"]:
                    for key in layout_map["global"][bind]["args"].split("+"):
                        if hasattr(e, key) and getattr(e,key) not in key_ev_list:
                            key_ev_list.append(e.key)
                else:
                    if hasattr(e, layout_map["global"][bind]["args"]) and getattr(e,layout_map["global"][bind]["args"]) not in key_ev_list:
                        key_ev_list.append(getattr(e,layout_map["global"][bind]["args"]))

        for layer in layout_map["layers"].keys():
            for bind in layout_map["layers"][layer].keys():
                if layout_map["layers"][layer][bind]["type"] == "key":
                    if "+" in layout_map["layers"][layer][bind]["args"]:
                        for key in layout_map["layers"][layer][bind]["args"].split("+"):
                            if hasattr(e, key) and getattr(e,key) not in key_ev_list:
                                key_ev_list.append( getattr(e,key) )
                    else:
                        if hasattr(e, layout_map["layers"][layer][bind]["args"]) and getattr(e,layout_map["layers"][layer][bind]["args"]) not in key_ev_list:
                            key_ev_list.append(getattr(e,layout_map["layers"][layer][bind]["args"]))

        if DEBUG: print("Key caps:",key_ev_list)
        cap = {e.EV_KEY:key_ev_list}
        if DEBUG: print("Capabilities assembled")
        return cap

    def trigg_key_event(virtual_device,keys,value):
        # Handles multi key bind
        if "+" in keys:
            needs_update = False
            for key in keys.split("+"):
                if hasattr(e,k):
                    needs_update = True
                    virtual_device.write(e.EV_KEY,getattr(e,k),value)
            if needs_update:
                virtual_device.syn()
        
        # If single key bound
        else:
            if hasattr(e, keys):
                virtual_device.write(e.EV_KEY,getattr(e,keys),value)
                virtual_device.syn()

    def unix_command(virtual_device,arg,key_value):
        global DEBUG
        if key_value == 0 or key_value == 2:
            load_dotenv()
            print("Res:",{False:{"shell":True,"stdout":sp.DEVNULL,"stderr":sp.DEVNULL,"start_new_session":True},True:{"shell":True,"start_new_session":True}}[DEBUG])
            sp.Popen(arg, **{False:{"shell":True,"stdout":sp.DEVNULL,"stderr":sp.DEVNULL,"start_new_session":True},True:{"shell":True,"start_new_session":True}}[DEBUG])



    EVENT_HANDLER = {"layer_control":macropad.layer_control,"key":trigg_key_event, "command":unix_command}

    # Handles every event of the driver
    async def event_loop(keymap, virtual_device):
        
        EVENT_HANDLER = driver.EVENT_HANDLER
        hwtrans_layer = driver.hwtrans_layer
        
        while True:
            print("Waiting for device")
            await driver.get_target_device()
            try:
                for event in driver.selected_device.async_read_loop():
                    clayer = macropad.clayer
                    if event != None and event.type == evdev.ecodes.EV_KEY:
                        ev = evdev.categorize(event)
                        if hwtrans_layer[ev.keycode] in keymap["global"]:
                            ev_type = keymap["global"][hwtrans_layer[ev.keycode]]["type"]
                            ev_arg = keymap["global"][hwtrans_layer[ev.keycode]]["args"]
                            EVENT_HANDLER[ev_type](virtual_device,ev_arg,ev.event.value)
                        else:
                            if hwtrans_layer[ev.keycode] in keymap["layers"][clayer]: 
                                ev_type = keymap["layers"][clayer][hwtrans_layer[ev.keycode]]["type"]
                                ev_arg = keymap["layers"][clayer][hwtrans_layer[ev.keycode]]["args"]
                                EVENT_HANDLER[ev_type](virtual_device,ev_arg,ev.event.value)
            except OSError as e:
                if e.errno == 19:
                    print("Device unplugged")
                driver.selected_device.close()
                driver.selected_device = None

    # Searches for devices on list of supported devices
    # Selects device once, supported device found
    # Supports only one device at a time though
    async def get_target_device():
        while driver.selected_device == None:
            # Loads available devices
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            # Loops through available devices until it finds 
            for device in devices:
                devinfo = device.info
                # Checks if the device is the targeted by the driver and preloads it into indev
                if {"vendor":devinfo.vendor,"product":devinfo.product,"version":devinfo.version} in supported_devs: 
                    indev = evdev.device.InputDevice(device)
                    # As the target device has two nodes one with ABS capabilities, the abs supporting device is selected
                    if ("EV_ABS",3) in indev.capabilities(verbose=True):
                        driver.selected_device = indev
                        break
            # Delays repetition by 2 secs to avoid overload
            await asyncio.sleep(2)
        print("Device connected")
        driver.selected_device.grab()


    def create_virtual_device():
        macropad.clayers = list(macropad.keymap["layers"].keys())
        cap = driver.load_capabilities(macropad.keymap)
        for attempt in range(3):
            try:
                driver.virtual_device = evdev.UInput(cap, name="Macroboard",version=1)
                break
            except Exception as e:
                print(e)
                print("Failed to open virtual device")
            time.sleep(3)
        if driver.virtual_device == None:
            print("Failed to create virtual device with 3 attempts.")

    def start(show_debug=False):
        from libs.service_controller import service as svc_controller
        global DEBUG
        global keymap
        global clayers
        DEBUG = show_debug
        # Loads keymapping and all layers from configuration file
        macropad.keymap=config_loader.load()
        driver.create_virtual_device()
        if driver.virtual_device == None:
           svc_controller.stop(show_debug=DEBUG)
        if DEBUG: print("Virtual device created")
        asyncio.run(driver.event_loop(macropad.keymap,driver.virtual_device))
