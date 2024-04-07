import RPi.GPIO as GPIO
import time

class RobotControl:
    def __init__(self, left_forward, left_backward, right_forward, right_backward):
        self.left_forward = left_forward
        self.left_backward = left_backward
        self.right_forward = right_forward
        self.right_backward = right_backward

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.left_forward, GPIO.OUT)
        GPIO.setup(self.left_backward, GPIO.OUT)
        GPIO.setup(self.right_forward, GPIO.OUT)
        GPIO.setup(self.right_backward, GPIO.OUT)

    def move_forward(self, duration=None):
        GPIO.output(self.left_forward, GPIO.HIGH)
        GPIO.output(self.right_forward, GPIO.HIGH)
        if duration:
            time.sleep(duration)
            self.stop()

    def stop(self):
        GPIO.output(self.left_forward, GPIO.LOW)
        GPIO.output(self.left_backward, GPIO.LOW)
        GPIO.output(self.right_forward, GPIO.LOW)
        GPIO.output(self.right_backward, GPIO.LOW)

def cleanup_gpio():
    GPIO.cleanup()
