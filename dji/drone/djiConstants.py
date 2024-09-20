# Aircraft state endpoints suffixes
# GETTER
EP_BASE = "/"
EP_SPEED = "/aircraft/speed"
EP_HEADING = "/aircraft/heading"
EP_ATTITUDE = "/aircraft/attitude"
EP_LOCATION = "/aircraft/location"
EP_GIMBAL_ATTITUDE = "/aircraft/gimbalAttitude"
EP_ALL_STATES = "/aircraft/allStates"

# SETTER
EP_STICK = "/send/stick" # expects a sting formated as: "<leftX>,<leftY>,<rightX>,<rightY>"
EP_ZOOM = "/send/camera/zoom"
EP_GIMBAL_SET_PITCH = "/send/gimbal/pitch"

# P-CONROLLER
CTRL_THRESH_HEAD = 0.1 # degrees
CTRL_THRESH_ALT = 0.1 # meters
CTRL_THRESH_X = 0.1 # meters
CTRL_THRESH_Y = 0.1 # meters

CTRL_GAIN_HEAD = 1/200
CTRL_GAIN_ALT = 0.1
CTRL_GAIN_X = 0.03
CTRL_GAIN_Y = 0.03
