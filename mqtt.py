import asyncio
import math
import logging
import random
import time

import asyncio_mqtt as aiomqtt

from dali.driver.hid import tridonic, hasseb
from dali.gear.general import Up, Down, SetMinLevel, SetMaxLevel, DAPC, RecallMaxLevel, RecallMinLevel, QueryActualLevel, Off
from dali.address import Broadcast, GearShort


async def main():
    dev = tridonic("/dev/dali/daliusb-*", glob=True)
    dev.connect()
    print("Waiting to be connected...")
    await dev.connected.wait()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")

    async with aiomqtt.Client("192.168.1.254") as client:
        async with client.messages() as msgs:
            await client.subscribe("l1/#")
            async for msg in msgs:
                print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
                #led = GearShort(int(msg.topic[1:]))
                led = 1
                power = int(msg.payload.decode())
                await dev.send(DAPC(led, power))

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
