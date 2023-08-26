import logging
import asyncio
import math
from dali.driver.hid import tridonic, hasseb
from dali.gear.general import Up, Down, SetMinLevel, SetMaxLevel, DAPC, RecallMaxLevel, RecallMinLevel, QueryActualLevel, Off
from dali.address import Broadcast, GearShort

LEDs = [0, 1]

async def main():
    # Edit to pick a device type.
    # dev = tridonic("/dev/dali/daliusb-*", glob=True)
    dev = tridonic("/dev/dali/daliusb-*", glob=True)

    # dev = hasseb("/dev/dali/hasseb-*", glob=True)
    dev.connect()
    print("Waiting to be connected...")
    await dev.connected.wait()
    print(f"Connected, firmware={dev.firmware_version}, serial={dev.serial}")

    for i in range (0, int(5*math.pi)*10, 2):
        power = int((math.cos(i/10)+1)*85)+85;
        if power > 255:
            power=255
        if power < 0:
            power=0
        print(f"Set to {power}")
        await dev.send(DAPC(GearShort(1), power))
        await asyncio.sleep(0.1)
        response = await dev.send(QueryActualLevel(GearShort(1)))
        print(f"Response was {response}")

    for power in range(254, 0, -8):
        print(f"Set to {power}")
        await dev.send(DAPC(GearShort(0), power))
        await asyncio.sleep(0.1)
        response = await dev.send(QueryActualLevel(GearShort(0)))
        print(f"Response was {response}")


    for i in range(3):
        print("Set max...")
        await dev.send(RecallMaxLevel(Broadcast()))
        await asyncio.sleep(1)
        response = await dev.send(QueryActualLevel(Broadcast()))
        print(f"Response was {response}")
        print("Set min...")
        await dev.send(RecallMinLevel(Broadcast()))
        await asyncio.sleep(1)
        response = await dev.send(QueryActualLevel(Broadcast()))
        print(f"Response was {response}")
    await dev.send(Off(Broadcast()))
    dev.disconnect()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
