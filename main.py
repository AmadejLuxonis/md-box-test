"""Pytest hardware checks for the Luxonis M8 Controller Box.

Run on the OAK4 host with::

    pytest -v main.py

The GPIO test expects every logical ControllerBox GPIO (1..16) to be high.
Output GPIOs are driven high by the fixture and input GPIOs use their internal
pull-up, so the assertion is made through the same read path used by an
application.
"""

import math
import os
import shutil
import struct
import subprocess
import tempfile
import wave
import time
from pathlib import Path

import pytest

from luxonis_u2if import ControllerBox

USB_DEVICE_ID = "0403:6001"

GPIOS = tuple(range(1, 17))
#OUT_GPIOS = (1, 4, 6, 8, 10, 12, 14)
OUT_GPIOS = (1, 4, 6, 8, 10, 16)
IN_GPIOS = tuple(gpio for gpio in GPIOS if gpio not in OUT_GPIOS)
RELAY_GPIOS = (12, 13, 14, 15)

FSYNC_FREQUENCY_HZ = 5
FSYNC_DUTY_CYCLE = 50.0
FSYNC_POLARITY = False  # Active-low, matching the original example.

AUDIO_CARD = os.environ.get("M8_AUDIO_CARD", "1")
AUDIO_DEVICE = os.environ.get("M8_AUDIO_DEVICE", "0")
TONE_FILE = Path(tempfile.gettempdir()) / "m8_controller_box_beep.wav"

@pytest.fixture(scope="module")
def box():
    """Open the ControllerBox and leave all test GPIOs in the high state."""

    controller = ControllerBox()
    try:
        for gpio in OUT_GPIOS:
            controller.gpio_init(
                gpio, controller.GPIO_OUT, controller.GPIO_PULL_NONE
            )
            controller.gpio_set(gpio, True)

        for gpio in IN_GPIOS:
            controller.gpio_init(
                gpio, controller.GPIO_IN, controller.GPIO_PULL_DOWN
            )

        yield controller
    finally:
        # Leave externally connected outputs in a safe state before closing.
        for gpio in OUT_GPIOS:
            try:
                controller.gpio_set(gpio, False)
            except Exception:
                pass
        controller.close()


def _write_tone_file(path: Path) -> None:
    """Create a short tone used to turn on the onboard buzzer."""

    sample_rate = 44_100
    duration = 0.1
    frequency = 1_000
    amplitude = 32_767
    sample_count = int(sample_rate * duration)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in range(sample_count):
            value = int(
                amplitude
                * math.sin(2 * math.pi * frequency * sample / sample_rate)
            )
            wav_file.writeframes(struct.pack("<h", value))


def _turn_buzzer_on() -> None:
    """Play one tone through the M8 audio device; there is no loop/button logic."""

    aplay = shutil.which("aplay")
    if aplay is None:
        pytest.skip("aplay is not installed on this host")

    _write_tone_file(TONE_FILE)
    subprocess.run(
        [aplay, "-D", f"hw:{AUDIO_CARD},{AUDIO_DEVICE}", str(TONE_FILE)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_all_gpios_read_logical_one(box):
    """Every logical GPIO 1..16 must read back as a logical 1."""

    time.sleep(0.1)

    for gpio in IN_GPIOS:
        if gpio not in RELAY_GPIOS:
            assert box.gpio_get(gpio) == 1, f"GPIO {gpio} did not read logical 1"


def test_buzzer_is_turned_on():
    """Turn the onboard buzzer on once for the duration of the check."""

    _turn_buzzer_on()


def test_fsync_controller_setup(box):
    """Configure both FSYNC outputs; ControllerBox raises on setup failure."""

    box.fsync_controller_init()
    box.fsync_controller_set_frequency(FSYNC_FREQUENCY_HZ)

    for output in (
        box.FsyncOutput.ISOLATED_STROBE,
        box.FsyncOutput.M8_FSYNC,
    ):
        box.fsync_controller_set_duty_cycle(FSYNC_DUTY_CYCLE, output)
        box.fsync_controller_set_polarity(FSYNC_POLARITY, output)

    box.fsync_controller_set_mode(box.FsyncMode.MASTER_OUTPUT)

def test_uart(box):
    box.serial_init()

    box.serial_write("Pozdravljen svet!")
    assert box.serial_read() == b"Pozdravljen svet!"

def test_relays(box):
    box.relay_init()

    box.relay_set(1)
    box.relay_set(2)
    box.relay_set(3)
    box.relay_set(4)

    time.sleep(0.5)

    for gpio in RELAY_GPIOS:
        assert box.gpio_get(gpio) == 0, f"GPIO {gpio} did not read logical 0"

    box.relay_reset(1)
    box.relay_reset(2)
    box.relay_reset(3)
    box.relay_reset(4)

    time.sleep(0.5)

    for gpio in RELAY_GPIOS:
        assert box.gpio_get(gpio) == 1, f"GPIO {gpio} did not read logical 1"

def test_usb_device_is_present():
    """Verify that the configured USB device is visible through the M8 hub."""

    lsusb = shutil.which("lsusb")
    if lsusb is None:
        pytest.fail("lsusb is not installed in the OakApp container")

    result = subprocess.run(
        [lsusb, "-d", USB_DEVICE_ID.lower()],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip(), (
        f"USB device {USB_DEVICE_ID} was not found through the M8 hub"
    )

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
