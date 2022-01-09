import pyb
import sensor
import image
import time

# Status LED
led = pyb.LED(3)

# Pan servo settings
servo_pan_ch = 1        # Pan servo channel
pulse_pan_min = 1000    # Pan minimum pulse (microseconds)
pulse_pan_max = 2000    # Pan maximum pulse (microseconds)

# Tilt servo settings
servo_tilt_ch = 0       # Tilt servo channel
pulse_tilt_min = 1000   # Tilt minimum pulse (microseconds)
pulse_tilt_max = 2000   # Tilt maximum pulse (microseconds)

# Other settings
threshold_x = 20        # Num pixels BB center x can be from CENTER_X
threshold_y = 20        # Num pixels BB center y can be from CENTER_Y
dir_x = 1               # Direction of servo movement (1 or -1)
dir_y = -1              # Direction of servo movement (1 or -1)
maestro_uart_ch = 1     # UART channel connected to Maestro board
maestro_num_ch = 12     # Number of servo channels on the Maestro board
baud_rate = 9600        # Baud rate of Mini Maestro servo controller

# Commands (for talking to Maestro servo controller)
cmd_set_target = 0x84

###############################################################################
# Functions

def servo_send_cmd(cmd, ch, payload):
    """
    Send generic compact protocol command to servo controller:
    | cmd | ch | msg lsb | msg msb |
    """

    # Check that channel is in range
    if (ch < 0) or (ch >= maestro_num_ch):
        return

    # Construct message
    msg = bytearray()
    msg.append(cmd)
    msg.append(ch)
    msg.append(payload & 0x7F)
    msg.append((payload >> 7) & 0x7F)

    # Send a message
    uart.write(msg)

def servo_set_target(ch, pulse):
    """
    Write pulse width (in microseconds) to given channel to control servo.
    """

    # Pulse number is 4x pulse width (in microseconds)
    p_num = 4 * int(pulse)

    # Send command to servo controller
    servo_send_cmd(cmd_set_target, ch, p_num)

###############################################################################
# Main

# Configure camera
sensor.reset()
sensor.set_contrast(3)
sensor.set_gainceiling(16)
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.GRAYSCALE)

# Get center x, y of camera image
WIDTH = sensor.width()
HEIGHT = sensor.height()
CENTER_X = int(WIDTH / 2 + 0.5)
CENTER_Y = int(HEIGHT / 2 + 0.5)

# Pour a bowl of serial
uart = pyb.UART(maestro_uart_ch, baud_rate)

# Start clock
clock = time.clock()

# Create cascade for finding faces
face_cascade = image.HaarCascade("frontalface", stages=25)

# Initial servo positions
servo_pos_x = int(((pulse_pan_max - pulse_pan_min) / 2) + pulse_pan_min)
servo_pos_y = int(((pulse_tilt_max - pulse_tilt_min) / 2) + pulse_tilt_min)

# Superloop
while(True):

    # Take timestamp (for calculating FPS)
    clock.tick()

    # Take photo
    img = sensor.snapshot()

    # Find faces in image
    objects = img.find_features(face_cascade, threshold=0.75, scale_factor=1.25)

    # Print out all faces in image
    largest_face_size = 0
    largest_face_bb = None
    for r in objects:

        # Find largest bounding box
        face_size = r[2] * r[3]
        if (face_size > largest_face_size):
            largest_face_size = face_size
            largest_face_bb = r

        # Draw bounding boxes around all faces
        img.draw_rectangle(r)

    # Find distance from center of face to center of frame
    if largest_face_bb is not None:

        # Turn on status LED
        led.on()

        # Print out the largest face info
        print("Face:", largest_face_bb)

        # Find x, y of center of largest face in image
        face_x = largest_face_bb[0] + int((largest_face_bb[2]) / 2 + 0.5)
        face_y = largest_face_bb[1] + int((largest_face_bb[3]) / 2 + 0.5)

        # Draw line from center of face to center of frame
        img.draw_line(CENTER_X, CENTER_Y, face_x, face_y)

        # Figure out how far away from center the face is (minus the dead zone)
        diff_x = face_x - CENTER_X
        if abs(diff_x) <= threshold_x:
            diff_x = 0
        diff_y = face_y - CENTER_Y
        if abs(diff_y) <= threshold_y:
            diff_y = 0

        # Calculate how fast the servo should move based on distance
        mov_x = dir_x * diff_x
        mov_y = dir_y * diff_y

        # Adjust camera position left/right and up/down
        servo_pos_x = servo_pos_x + mov_x
        servo_pos_y = servo_pos_y + mov_y

        # Constrain servo positions to range of servos
        servo_pos_x = max(servo_pos_x, pulse_pan_min)
        servo_pos_x = min(servo_pos_x, pulse_pan_max)
        servo_pos_y = max(servo_pos_y, pulse_tilt_min)
        servo_pos_y = min(servo_pos_y, pulse_tilt_max)

        # Set pan/tilt
        print("Moving to X:", int(servo_pos_x), "Y:", int(servo_pos_y))
        servo_set_target(servo_pan_ch, servo_pos_x)
        servo_set_target(servo_tilt_ch, servo_pos_y)


    # If there are no faces, don't do anything
    else:

        # Turn off status LED
        led.off()

    # Print FPS
    print("FPS:", clock.fps())
