import asyncio
import logging
import os

import aiomqtt

from dali.driver.hid import tridonic
from dali.gear.general import (
    DAPC,
    Off,
)
from dali.address import GearShort

from dotenv import load_dotenv

load_dotenv()

MAX_LED_POWER = 255
MIN_LED_POWER = 81

DALI = False  # Set to True if USB connected to DALI bus


async def handle_dim(dev, led, level):
    if level == 0:
        print(f"Turning off LED {led}")
        if DALI:
            await dev.send(Off(led))
    elif level > 0 and level <= 100:
        power = int((level / 100) * (MAX_LED_POWER - MIN_LED_POWER) + MIN_LED_POWER)
        print(f"Dimming LED {led} to {level}% ({power})")
        if DALI:
            await dev.send(DAPC(led, power))
    else:
        print(f"Invalid dim level {level}")


async def main():
    dev = tridonic("/dev/dali/daliusb-*", glob=True)
    if DALI:
        dev.connect()
        print("Waiting to be connected to DALI...")
        await dev.connected.wait()
        print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")
    else:
        print("Not connected to DALI bus, set DALI=True to enable")

    async with aiomqtt.Client(
        "mqtt.happyswing.at",
        port=8883,
        username="happyswing",
        password=os.getenv("MQTT_PASSWORD"),
        tls_params=aiomqtt.TLSParameters(
            ca_certs="mqtt.happyswing.at_cacert.pem",
        ),
        tls_insecure=True,
    ) as client:
        print(f"Connected to `{client}`")
        async with client.messages() as msgs:
            await client.subscribe("cmd/led/+/dim")
            async for msg in msgs:
                print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
                try:
                    path = msg.topic.value.split("/")
                    led = GearShort(int(path[2]))
                    cmd = path[3]
                    payload = msg.payload.decode()

                    if cmd == "dim":
                        level = int(payload)
                        await handle_dim(dev, led, level)
                    else:
                        print(f"Unknown command: {msg.topic}")
                except Exception as e:
                    print(f"Exception processing message {msg.topic}: {e}")


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
