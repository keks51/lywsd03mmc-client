# lywsd03mmc-client
Python library to work with Xiaomi Temperature and Humidifier sensor using [bleak](https://pypi.org/project/bleak/) library.   
The library is based on [LYWSD02](https://github.com/h4/lywsd02) and [lywsd03mmc
](https://github.com/uduncanu/lywsd03mmc).

# Installation
Python >=3.8, <3.13 is required.
```commandline
pip3 install -r requirements.txt
```

# Get device address
## For linux and windows
find the mac address of the device  
From the Xiaomi Home app:
1. Go into the details of the device
2. Click on the three dots to get into the settings
3. Click "About" (near the top of the list)
4. And make a note of the MAC address shown.

## For macOS
Run script scripts/discover_devices.py   
Sample output:  
![discover.png](pics%2Fdiscover.png)   
Note that the UUID is not the MAC address (or any other intrinsic property) of the peripheral.  
It’s just a random UUID assigned by Core Bluetooth. This identifier doesn't always stay the same.  

# Usage
## Sync example
```python
from lywsd03mmc.lywsd03mmc_client import Lywsd03mmcClientSyncContext, Lywsd03mmcData

MAC_ADDRESS_OR_UUID = '70C40C24-C60B-BB9D-D737-9895C5DA52F3'

while True:
    try:
        with Lywsd03mmcClientSyncContext(MAC_ADDRESS_OR_UUID, timeout_sec=60) as client:
            data: Lywsd03mmcData = client.get_data()
            print(data)
            print()
    except Exception as ex:
        print(f"Error: {ex}")
```
## Async example
```python
from lywsd03mmc.lywsd03mmc_client import Lywsd03mmcClient
import asyncio

MAC_ADDRESS_OR_UUID = '70C40C24-C60B-BB9D-D737-9895C5DA52F3'


async def main(address):
    async with Lywsd03mmcClient(address, timeout=60) as client:
        lywsd03mmcData = await client.get_data()
        print(lywsd03mmcData)


asyncio.run(main(MAC_ADDRESS_OR_UUID))
```

# Lywsd03mmc bluetooth services and characteristics     
To get list of services and characteristics run scripts/list_gatt.py    
We are interested only in service <b>ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6</b>     
Characteristics:     
1. EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6   
    Read Temperature, Humidity and Battery voltage.  
    [Read]
    ```text
    Ch: ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 53): Unknown
    		['read', 'notify']
    		 handle: 55 bytearray(b'Temperature and Humidity')
    		 handle: 56 bytearray(b'\x00')
    ```
    ```python
    print(client.get_data()) # temperature_row: 2479, temperature: 24.79, hum: 33, battery_vol: 2994, battery_percentage: 89
    ```
2. EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6        
    Read battery percentage but always 100%.       
    [Read]
    ```text
    Ch: ebe0ccc4-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 57): Unknown
    		['read']
    		 handle: 59 bytearray(b'Batt')
    ```
    ```python
    print(client.get_battery()) # 3001
    ```
3. EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Read or write Temperature Uint (C or F)     
    [Read, Write]     
    ```text
    Ch: ebe0ccbe-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 50): Unknown
    		['read', 'write']
    		 handle: 52 bytearray(b'Temperature Uint')
    ```
    ```python
    print(client.get_temp_unit()) # C
    client.set_celsius()
    print(client.get_temp_unit()) # C
    client.set_fahrenheit()
    print(client.get_temp_unit()) # F
    client.set_celsius()
    print(client.get_temp_unit()) # C 
    ```
4. EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Read or write Timestamp.            
    [Read, Write]     
    ```text
    Ch: ebe0ccb7-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 34): Unknown
    		['read', 'write']
    		 handle: 36 bytearray(b'Time')
    ```
    ```python
    print(datetime.datetime.fromtimestamp(client.get_timestamp())) # 2023-12-18 01:36:38
    client.set_timestamp((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
    print(datetime.datetime.fromtimestamp(client.get_timestamp())) # 2023-12-17 01:36:38
    ```   

5. EBE0CCB9-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Get last calculated hour record and next not calculated since unpacking.     
    [Read]     
    ```text
    Ch: ebe0ccb9-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 37): Unknown
		['read']
		 handle: 39 bytearray(b'Data Count')
    ```
    ```python
    print(client.get_last_calculated_hour_idx_and_next_idx())  # (107, 108)
    ```

6. EBE0CCBB-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Read last calculated hour data.  
    [Read]    
    ```text
    Ch: ebe0ccbb-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 43): Unknown
    		['read']
    		 handle: 45 bytearray(b'Data Read')
    ```
    ```python
    # idx_num: 107, timestamp: 1702803600, temperature_row_max: 21.7, humidity_max: 39, temperature_row_min: 20.6, humidity_min: 37
    print(client.get_last_hour_data()) 
    ```

7. EBE0CCBA-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Get or set first history record.    
    [Read, Write]    
    ```text
    Ch: ebe0ccba-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 40): Unknown
    		['read', 'write']
    		 handle: 42 bytearray(b'Index')
    ```
    ```python
    print(client.get_first_history_idx())  # 0 
    client.set_first_history_idx(100)
    print(client.get_first_history_idx())  # 100
    ```

8. EBE0CCBC-7A0A-4B0C-8A1A-6FF2997DA3A6     
    Get array of history records starting from step (7).   
    [Read]
    ```text
    Ch: ebe0ccbc-7a0a-4b0c-8a1a-6ff2997da3a6 (Handle: 46): Unknown
    		['notify']
    		 handle: 48 bytearray(b'Data Notify')
    		 handle: 49 bytearray(b'')
    ```
    ```python
    client.set_firts_history_idx(100)
    print(client.get_first_history_idx())  # 100
    print(client.get_last_calculated_hour_idx_and_next_idx())  # (110, 111)
    print(len(client.get_history_data()))  # 11
    ```


