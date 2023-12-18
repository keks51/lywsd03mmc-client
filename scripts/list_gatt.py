import asyncio

from bleak import BleakClient

MAC_ADDRESS_OR_UUID = '70C40C24-C60B-BB9D-D737-9895C5DA52F3'


async def main(address):
    async with BleakClient(address, timeout=60) as client:
        services = await client.get_services()
        for s in services:
            print(f"Service: {s}")

            for c in s.characteristics:
                print(f"\tCh: {c}")
                print(f"\t\t{c.properties}")
                for d in c.descriptors:
                    x = await client.read_gatt_descriptor(d.handle)
                    print(f"\t\t handle: {d.handle} {x}")


asyncio.run(main(MAC_ADDRESS_OR_UUID))
