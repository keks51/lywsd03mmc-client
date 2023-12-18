import asyncio
import struct
import datetime
import time

import async_to_sync as sync
from bleak import BleakClient, BleakGATTCharacteristic


class Lywsd03mmcData:

    def __init__(self, temperature_row: int, humidity: int, battery_vol: int):
        self.temperature_row = temperature_row
        self.hum = humidity
        self.bat_vol = battery_vol

    @property
    def temperature(self):
        return self.temperature_row / 100

    @property
    def humidity(self):
        return self.hum

    @property
    def battery_vol(self):
        return self.bat_vol

    @property
    def battery_percentage(self):
        return min(int(round((self.bat_vol / 1000 - 2.1), 2) * 100), 100)

    def __str__(self):
        return f"temperature_row: {self.temperature_row}, " + \
            f"temperature: {self.temperature}, " + \
            f"hum: {self.humidity}, " + \
            f"battery_vol: {self.bat_vol}, " + \
            f"battery_percentage: {self.battery_percentage}"


class Lywsd03mmcOneHourHistoryData:

    def __init__(self,
                 idx_num: int,
                 timestamp: int,
                 temperature_row_max: int,
                 humidity_max: int,
                 temperature_row_min: int,
                 humidity_min: int, ):
        self.idx_num = idx_num
        self.timestamp = timestamp
        self.temperature_row_max = temperature_row_max
        self.humidity_max = humidity_max
        self.temperature_row_min = temperature_row_min
        self.humidity_min = humidity_min

    @property
    def temperature_max(self):
        return self.temperature_row_max / 10

    @property
    def temperature_min(self):
        return self.temperature_row_min / 10

    def __str__(self):
        return f"idx_num: {self.idx_num}, " + \
            f"timestamp: {self.timestamp}, " + \
            f"temperature_row_max: {self.temperature_max}, " + \
            f"humidity_max: {self.humidity_max}, " + \
            f"temperature_row_min: {self.temperature_min}, " + \
            f"humidity_min: {self.humidity_min}"


class Lywsd03mmcClient:
    BYTES_TO_TEMP_UNIT = {
        '1': 'F',
        '0': 'C'
    }

    GET_TEMP_AND_HUMIDITY_ATTRIBUTE_UUID = 'EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_BATTERY_ATTRIBUTE_UUID = 'EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_OR_SET_UNITS_ATTRIBUTE_UUID = 'EBE0CCBE-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_OR_SET_TIMESTAMP_ATTRIBUTE_UUID = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_OR_SET_FIRST_HISTORY_RECORD_IDX_ATTRIBUTE_UUID = 'EBE0CCBA-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_LAST_CALC_AND_NEXT_IDX_ATTRIBUTE_UUID = 'EBE0CCB9-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_HISTORY_DATA_ATTRIBUTE_UUID = 'EBE0CCBC-7A0A-4B0C-8A1A-6FF2997DA3A6'
    GET_LAST_CALC_DATA_ATTRIBUTE_UUID = 'EBE0CCBB-7A0A-4B0C-8A1A-6FF2997DA3A6'

    def __init__(self, mac_or_uuid: str, timeout: float):
        self.mac_or_uuid = mac_or_uuid
        self.client = BleakClient(
            address_or_ble_device=self.mac_or_uuid,
            timeout=timeout)

    async def connect(self) -> bool:
        return await self.client.connect()

    async def get_data(self) -> Lywsd03mmcData:
        # returns for example (2216, 23, 3001) -> (temp, humidity, battery_voltage)
        # temp = (22.16) integral and fractional parts
        res: bytearray = await self.__get_attribute(self.GET_TEMP_AND_HUMIDITY_ATTRIBUTE_UUID)
        (temp, hum, battery_vol) = struct.unpack_from('<hBh', res)
        return Lywsd03mmcData(temperature_row=temp, humidity=hum, battery_vol=battery_vol)

    async def get_battery(self):
        res: bytearray = await self.__get_attribute(self.GET_BATTERY_ATTRIBUTE_UUID)
        return struct.unpack_from('b', res)[0]

    async def get_temp_unit(self):
        res: bytearray = await self.__get_attribute(self.GET_OR_SET_UNITS_ATTRIBUTE_UUID)
        return self.BYTES_TO_TEMP_UNIT[str(res[0])]

    async def set_celsius(self):
        await self.__write_attribute(self.GET_OR_SET_UNITS_ATTRIBUTE_UUID, b'\x00')

    async def set_fahrenheit(self):
        await self.__write_attribute(self.GET_OR_SET_UNITS_ATTRIBUTE_UUID, b'\x01')

    async def get_timestamp(self):
        res: bytearray = await self.__get_attribute(self.GET_OR_SET_TIMESTAMP_ATTRIBUTE_UUID)
        timestamp = struct.unpack('I', res)[0]
        return timestamp

    async def set_timestamp(self, milliseconds: int):
        data: bytes = struct.pack('I', int(milliseconds))
        await self.__write_attribute(self.GET_OR_SET_TIMESTAMP_ATTRIBUTE_UUID, data)

    async def get_first_history_idx(self):
        res: bytearray = await self.__get_attribute(self.GET_OR_SET_FIRST_HISTORY_RECORD_IDX_ATTRIBUTE_UUID)
        _idx = 0 if len(res) == 0 else struct.unpack_from('I', res)[0]
        return _idx

    async def set_first_history_idx(self, idx: int):
        data: bytes = struct.pack('I', int(idx))
        await self.__write_attribute(self.GET_OR_SET_FIRST_HISTORY_RECORD_IDX_ATTRIBUTE_UUID, data)

    async def get_last_calculated_hour_idx_and_next_idx(self):
        # last_calc, last_idx
        res: bytearray = await self.__get_attribute(self.GET_LAST_CALC_AND_NEXT_IDX_ATTRIBUTE_UUID)
        return struct.unpack_from('II', res)

    async def get_history_data(self):
        records = []
        last_rec_idx = (await self.get_last_calculated_hour_idx_and_next_idx())[1]

        def callback(sender: BleakGATTCharacteristic, data_bytes: bytearray):
            data_tuple = struct.unpack_from('<IIhBhB', data_bytes)
            data = Lywsd03mmcOneHourHistoryData(
                idx_num=data_tuple[0],
                timestamp=data_tuple[1],
                temperature_row_max=data_tuple[2],
                humidity_max=data_tuple[3],
                temperature_row_min=data_tuple[4],
                humidity_min=data_tuple[5]
            )
            records.append(data)

        await self.client.start_notify(self.GET_HISTORY_DATA_ATTRIBUTE_UUID, callback)

        await asyncio.sleep(3.0)  # to get first record
        while records[-1].idx_num < last_rec_idx - 1:
            await asyncio.sleep(1.0)
            continue
        await self.client.stop_notify(self.GET_HISTORY_DATA_ATTRIBUTE_UUID)

        return records

    async def get_last_hour_data(self):
        res: bytearray = await self.__get_attribute(self.GET_LAST_CALC_DATA_ATTRIBUTE_UUID)
        data = struct.unpack_from('<IIhBhB', res)
        return Lywsd03mmcOneHourHistoryData(
            idx_num=data[0],
            timestamp=data[1],
            temperature_row_max=data[2],
            humidity_max=data[3],
            temperature_row_min=data[4],
            humidity_min=data[5]
        )

    async def __get_attribute(self, attribute_name: str):
        return await self.client.read_gatt_char(attribute_name)

    async def __write_attribute(self, attribute_name: str, value: bytes):
        await self.client.write_gatt_char(attribute_name, value)

    async def close(self):
        if self.client.is_connected:
            await self.client.disconnect()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class Lywsd03mmcClientSyncContext:

    def __init__(self, mac_or_uuid: str, timeout_sec: int):
        self.sync_client = sync.methods(Lywsd03mmcClient(mac_or_uuid, timeout=timeout_sec))

    def __enter__(self):
        self.sync_client.connect()
        return self.sync_client

    def __exit__(self, exc_type, exc_value, traceback):
        if self.sync_client is not None:
            self.sync_client.close()
