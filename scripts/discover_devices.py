import asyncio

from bleak import BleakScanner


async def main():
    devices = await BleakScanner.discover(return_adv=True, timeout=10)

    for (_, (device, adv_data)) in devices.items():
        print(f"Name: {device.name}. RSSI: {adv_data.rssi}. Address: '{device.address}'.")

while True:
    asyncio.run(main())
    print("next cycle")
