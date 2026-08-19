import os
import xml.etree.ElementTree as ET
CONFIG_PATH = os.path.expanduser("~/.config/romopad/")
CONF_FNAME = "layout.xml"

# There're 2 types of <root> global, layer
# <global></global> Holds layer agnostic binds
# <layer id="$id"></layer> Holds layer dependent binds, every layer must have defined unique id! otherwise it wont ever load
# <bind keys="$key+$key2" type="$type">child</bind> Defines binding for given root either global or layer 
# attribute $keys defines activation keys syntax is following $keys = "key" or for combination $keys="key1+key2"
# attribute $type there're three possible values control,command and key
    # for $type="control" the child should be recognized in built control for the driver => primarily layer controls
    # for $type="command" the child should be linux bash command in quotes so example <bind keys="KEY_01" type="command">"echo 'Hello world!'"</bind>
    # for $type="key" the child should be keycode name recognized by evdev
    # for $type="control" the child should be recognized in built control for the driver => primarily layer controls
    # for $type="command" the child should be linux bash command in quotes so example <bind keys="KEY_01" type="command">"echo 'Hello world!'"</bind>
    # for $type="key" the child should be keycode name recognized by evdev, in this however the action needs to be provided value which will be passed on key event
        # $value can have 4 possible states integer/float, hold, down, release If multiple keys is defined use ; as delimeter if used the value set must be as long as key set 
            # down = 1 for most keys this means that they're going to be pressed
default_config=(
"""
<?xml version="1.0" encoding="UTF-8"?>
<layout>
  <static-layer>
      <bind keys="NOB1" type="key">KEY_MUTE</bind>
      <bind keys="NOB1_LT" type="key">KEY_VOLUMEDOWN</bind>
      <bind keys="NOB1_RT" type="key">KEY_VOLUMEUP</bind> 
      <bind keys="NOB2_LT" type="layer_control">prev</bind>
      <bind keys="NOB2_RT" type="layer_control">next</bind>
  </static-layer>
  <!--This layer behaves like numpad-->
  <layer id="0">
      <bind keys="KEY_01" type="key">KEY_NUMLOCK</bind>
      <bind keys="KEY_05" type="key">KEY_KPDOT</bind>
      <bind keys="KEY_09" type="key">KEY_KP0</bind>
      <bind keys="KEY_10" type="key">KEY_KP1</bind>
      <bind keys="KEY_11" type="key">KEY_KP2</bind>
      <bind keys="KEY_12" type="key">KEY_KP3</bind>
      <bind keys="KEY_06" type="key">KEY_KP4</bind>
      <bind keys="KEY_07" type="key">KEY_KP5</bind>
      <bind keys="KEY_08" type="key">KEY_KP6</bind>
      <bind keys="KEY_02" type="key">KEY_KP7</bind>
      <bind keys="KEY_03" type="key">KEY_KP8</bind>
      <bind keys="KEY_04" type="key">KEY_KP9</bind>
  </layer>
</layout>
""")

# Can be set by user, but this is default
# NOB_1 left, right by default controls layer

# Writes default config if it does not exist for some reason
def generate_default():
    global default_config
    default_config = "\n".join(default_config.split("\n")[1:])
    try:
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        with open(CONFIG_PATH+CONF_FNAME,"w") as f:
            f.write(default_config)
    
    # Mainly catches permissions issue
    except Exception as e:
        print(str(e))
        print("Could not write ...")
        print("Loading hardcoded preconf")            

# Checks if some layers exist and if they contain binds
def check_layers(layer_arr,is_static=False):
    if len(layer_arr)<1:
        print("No "+str(is_static).replace("False"," layers defined").replace("True"," no static layers defined"))
        return False
    else:
        if is_static == True:
            if len(layer_arr[-1].findall("./bind"))>0:
                return True
            else:
                return False

        if is_static == False:
            for layer in layer_arr:
                if len(layer.findall("./bind"))>0:
                    return True
            return False

def construct_dict(layout):
    layout_object = {}
    static_layer = None
    layers = None
    layout_object["global"]={}
    layout_object["layers"]={}

    if len(layout.findall("."))<1:
        print("Invalid configuration: No layout defined")

    static_layers = layout.findall("./static-layer")
    if check_layers(static_layers,True):
        static_layer = static_layers[-1]

    layers=layout.findall(".//layer")
    if not check_layers(layers):
        # Layers either not existing or all empty
        layers = None

    # Loads global layout
    if static_layer != None:
        for bind in static_layer.findall("bind"):
            if "type" in bind.attrib:
                layout_object["global"][ bind.attrib["keys"] ]={"type":bind.attrib["type"],"args":bind.text} 
    
    # Loads layer dependent layout
    if layers != None:
        for layer in layers:
            layout_object["layers"][layer.attrib["id"]]={}
            for bind in layer.findall("bind"):
                if "type" in bind.attrib:
                    layout_object["layers"][layer.attrib["id"]][ bind.attrib["keys"] ]={"type":bind.attrib["type"],"args":bind.text}
    return layout_object
        
    
def load():
    loaded_xml=None
    if os.path.isfile(CONFIG_PATH+CONF_FNAME):
        try:
            loaded_xml = ET.parse(CONFIG_PATH+CONF_FNAME)
        except Exception as e:
            print("Loading config encountered error:")
            print(str(e))
            exit()
    else:
        print("Could not load configuration, generating default...")
        generate_default()
        print("\n".join(default_config.split("\n")[1:]))
        loaded_xml=ET.fromstring(default_config)
    return construct_dict(loaded_xml) 


