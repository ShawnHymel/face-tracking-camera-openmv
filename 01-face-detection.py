import pyb
import sensor
import image
import time

# Status LED
led = pyb.LED(3)

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

# Start clock
clock = time.clock()

# Create cascade for finding faces
face_cascade = image.HaarCascade("frontalface", stages=25)

# Superloop
while(True):

    # Take timestamp (for calculating FPS)
    clock.tick()

    # Take photo
    img = sensor.snapshot()

    # Find faces in image
    objects = img.find_features(face_cascade, threshold=0.75, scale_factor=1.25)

    # Find largest face in image
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

    # Find line from center of face to center of frame
    if largest_face_bb is not None:

        # Turn on status LED
        led.on()

        # Print out the largest face info
        print("Face:", largest_face_bb)

        # Find x, y of center of largest face in image
        face_x = largest_face_bb[0] + int((largest_face_bb[2]) / 2 + 0.5)
        face_y = largest_face_bb[1] + int((largest_face_bb[3]) / 2 + 0.5)

        # Draw line from center of image to center of face
        img.draw_line(CENTER_X, CENTER_Y, face_x, face_y)

    # If there is no face, don't do anything
    else:

        # Turn off status LED
        led.off()

    # Print FPS
    print("FPS:", clock.fps())
