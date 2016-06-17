import RPi.GPIO as GPIO
import time

# GPIOs 22 and 27 need to be connected with a jumper
input_gpio = 8
output_gpio = 7

GPIO.setmode(GPIO.BCM)
GPIO.setup(input_gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(output_gpio, GPIO.OUT)

p = GPIO.PWM(output_gpio, 100)
p.start(0)

do_start_stop = False

def test_duty_cycles(i):
    print(" test_duty_cycles iteration %d" % i)
    if do_start_stop:
        p.stop()
        p.start(0)
    for dc in (40, 60):
        p.ChangeDutyCycle(dc)
        total = sum(GPIO.input(input_gpio) for i in range(20000))
        avg = (total / 20000.0) * 100
        print("  testing %.1f Hz, measured %.2f" % (dc, avg))
        if abs(avg - dc) > 10:
            print("*  over 10 Hz difference!")

try:
    for i in range(5):
        test_duty_cycles(i+1)
finally:
    GPIO.cleanup()