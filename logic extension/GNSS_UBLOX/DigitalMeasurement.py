from saleae.range_measurements import DigitalMeasurer

class MyDigitalMeasurer(DigitalMeasurer):
    supported_measurements = ["year", "month", "day", "hour", "minute", "second", "dateValid", "TODValid", "PSM", "gnssFixOK", "LLHValid", "longitude", "latitude", "height"]

    def __init__(self, requested_measurements):
        super().__init__(requested_measurements)
        self.requested_measurements = requested_measurements
        self.data_buffer = bytearray()
        self.trame_to_remove = b'\xB5b\x01\x07\0\0\x08\x19'

    def process_data(self, data):
        for time, bitstate in data:
            # Assuming data is being added as bytes
            self.data_buffer.append(bitstate)
        
        # Search and remove the specific frame if it exists
        self.data_buffer = self.data_buffer.replace(self.trame_to_remove, b'')

    def combine_bytes(self, byte_list):
        import struct
        return struct.unpack('<i', bytes(byte_list))[0]

    def decode_trame(self):
        year = {'X2': [self.data_buffer[10], self.data_buffer[11]]}
        month = self.data_buffer[12]
        day = self.data_buffer[13]
        hour = self.data_buffer[14]
        minute = self.data_buffer[15]
        second = self.data_buffer[16]

        dateValid = (self.data_buffer[17] & 1) + ((self.data_buffer[28] >> 6) & 1)
        TODValid = ((self.data_buffer[17] >> 1) & 1) + ((self.data_buffer[28] >> 7) & 1)
        PSM = (self.data_buffer[27] >> 2) & 0x03
        gnssFixOK = self.data_buffer[27] & 1
        LLHValid = not (self.data_buffer[84] & 1)

        lon = self.combine_bytes(self.data_buffer[30:34]) / 10000000.0
        lat = self.combine_bytes(self.data_buffer[34:38]) / 10000000.0
        height = self.combine_bytes(self.data_buffer[42:46]) / 1000.0

        return {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": second,
            "dateValid": dateValid,
            "TODValid": TODValid,
            "PSM": PSM,
            "gnssFixOK": gnssFixOK,
            "LLHValid": LLHValid,
            "longitude": lon,
            "latitude": lat,
            "height": height
        }

    def measure(self):
        if len(self.data_buffer) < 85:  # Ensure buffer has enough data for decoding
            return {}

        values = self.decode_trame()
        return values
