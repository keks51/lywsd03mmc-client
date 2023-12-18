from lywsd03mmc.lywsd03mmc_client import Lywsd03mmcClient
import asyncio

MAC_ADDRESS_OR_UUID = '70C40C24-C60B-BB9D-D737-9895C5DA52F3'


async def main(address):
    async with Lywsd03mmcClient(address, timeout=60) as client:
        lywsd03mmcData = await client.get_data()
        print(lywsd03mmcData)


asyncio.run(main(MAC_ADDRESS_OR_UUID))
