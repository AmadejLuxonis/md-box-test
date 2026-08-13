import time
import os
from luxonis_u2if import ControllerBox

# ------------------------------------------------------------
# Connect to the ControllerBox
# ------------------------------------------------------------
box = ControllerBox()
box.led_init()  # Initialize all LEDs
box.relay_init()

# ------------------------------------------------------------
# Button setup (IRQ)
# ------------------------------------------------------------
BUTTON1_PIN = 20  # GPIO pin where the button is connected
BUTTON2_PIN = 21
BUTTON3_PIN = 19 

box.gpio_init(BUTTON1_PIN, box.GPIO_IN, box.GPIO_PULL_UP)
box.gpio_init(BUTTON2_PIN, box.GPIO_IN, box.GPIO_PULL_UP)
box.gpio_init(BUTTON3_PIN, box.GPIO_IN, box.GPIO_PULL_UP)

# Enable interrupts for rising and falling edges with debounce
box.gpio_set_irq(
    BUTTON1_PIN,
    box.IRQ_RISING | box.IRQ_FALLING,
    debounce=True
)

box.gpio_set_irq(
    BUTTON2_PIN,
    box.IRQ_RISING | box.IRQ_FALLING,
    debounce=True
)

box.gpio_set_irq(
    BUTTON3_PIN,
    box.IRQ_RISING | box.IRQ_FALLING,
    debounce=True
)

box.serial_init()

# ------------------------------------------------------------
# Audio setup
# ------------------------------------------------------------
CARD = 1          # USB audio card number (from /proc/asound/cards)
DEVICE = 0        # Audio device on that card
FREQ = 1000       # Beep frequency in Hz
DURATION = 0.1    # Tone chunk duration in seconds
TONE_FILE = "/tmp/beep.wav"  # Temporary WAV file to use with aplay

def generate_wav():
    """Generate a short 1kHz sine wave WAV file if it doesn't exist."""
    import wave, struct, math
    framerate = 44100
    amplitude = 32767
    n_samples = int(framerate * DURATION)

    with wave.open(TONE_FILE, 'w') as wf:
        wf.setnchannels(1)        # Mono
        wf.setsampwidth(2)        # 16-bit
        wf.setframerate(framerate)
        for i in range(n_samples):
            value = int(amplitude * math.sin(2 * math.pi * FREQ * i / framerate))
            wf.writeframesraw(struct.pack('<h', value))

def play_tone():
    """Play the generated tone using aplay."""
    if not os.path.exists(TONE_FILE):
        generate_wav()
    os.system(f"aplay -D hw:{CARD},{DEVICE} {TONE_FILE} >/dev/null 2>&1")

# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------
blink_interval = 0.5        # Time for LED 1 blink
relay_interval = 1
last_blink = time.monotonic()
last_switch = time.monotonic()
led_on = False
button_pressed = False      # Track if button is currently pressed
led2_state = False
led3_state = False

relay_state = False

GPIOS = list(range(1, 16 + 1))
OUT_GPIOS = [1, 4, 6, 8, 10, 12, 14]
IN_GPIOS = [gpio for gpio in GPIOS if gpio not in OUT_GPIOS]

for gpio in OUT_GPIOS:
    box.gpio_init(gpio, box.GPIO_OUT, box.GPIO_PULL_NONE) 
    box.gpio_set(gpio, True)

for gpio in IN_GPIOS:
    box.gpio_init(gpio, box.GPIO_IN, box.GPIO_PULL_DOWN)

box.relay_reset(1)
box.relay_reset(2)
box.relay_reset(3)
box.relay_reset(4)

stm_fps = 40
stm_polarity = 0

box.fsync_controller_set_pin_configuration(box.PIN_CONFIG_TYPE_PWM_HFSTROBE, box.FsyncOutput.ISOLATED_STROBE)
box.fsync_controller_init()
box.fsync_controller_set_frequency(stm_fps)

box.fsync_controller_set_duty_cycle(box.fsync_controller_maxmin_hfstrobe_duty(stm_fps, stm_polarity) * 0.5, box.FsyncOutput.ISOLATED_STROBE)
box.fsync_controller_set_polarity(stm_polarity, box.FsyncOutput.ISOLATED_STROBE)

box.fsync_controller_set_duty_cycle(50, box.FsyncOutput.M8_FSYNC)
box.fsync_controller_set_polarity(stm_polarity, box.FsyncOutput.M8_FSYNC)

box.fsync_controller_set_mode(box.FsyncMode.MASTER_OUTPUT)

while True:
    now = time.monotonic()

    # ----------------------------
    # LED 1 blinking logic
    # ----------------------------
    if now - last_blink >= blink_interval:
        led_on = not led_on
        if led_on:
            box.led_on(1)
        else:
            box.led_off(1)
        last_blink = now

    if now - last_switch >= relay_interval:
        box.serial_write("Pozdravljen svet!")
        print(f"UART: {box.serial_read()}")

        for gpio in IN_GPIOS:
            print(f"GPIO {gpio}: {box.gpio_get(gpio)}")

        print("--------------------------------")

        relay_state = not relay_state

        if relay_state == True:
            box.relay_set(1) 
            time.sleep(0.1)
            box.relay_set(2)
            time.sleep(0.1)
            box.relay_set(3)
            time.sleep(0.1)
            box.relay_set(4)
            time.sleep(0.1)
        else:
            box.relay_reset(1)
            time.sleep(0.1)
            box.relay_reset(2)
            time.sleep(0.1)
            box.relay_reset(3)
            time.sleep(0.1)
            box.relay_reset(4)
            time.sleep(0.1)

        last_switch = now

    # ----------------------------
    # Handle button IRQ events
    # ----------------------------
    for pin, event in box.gpio_get_irq():
        if pin == BUTTON1_PIN:
            if event == box.IRQ_RISING:
                # Button pressed
                button_pressed = True
            elif event == box.IRQ_FALLING:
                # Button released
                button_pressed = False
        elif pin == BUTTON2_PIN and event == box.IRQ_RISING:
            led2_state = not led2_state

            if led2_state:
                box.led_on(2)
            else:
                box.led_off(2)
        elif pin == BUTTON3_PIN and event == box.IRQ_RISING:
            led3_state = not led3_state

            if led3_state:
                box.led_on(3)
            else:
                box.led_off(3)

    # ----------------------------
    # Continuous beep while button held
    # ----------------------------
    if button_pressed:
        play_tone()  # Play short tone repeatedly
    
    time.sleep(0.01)  # Small delay for loop efficiency
