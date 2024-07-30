import struct

data = b'\xB5b\x01\x07\\0\xF0\xF9\xC6\x12\xE8\x07\x07\x18\x0F\x1E\x0C7J\0\0\0\xC2\xF1\xFF\xFF\x03\x01\xEB\x07\xB7yY\x01z!<\x1D\xE5\x95\x03\0\xE7\xE1\x02\0Bc\0\0\xF8Q\0\0\x19\xC6\xFF\xFFC\x14\0\0\xCB\xFC\xFF\xFFX=\0\0^;\xF5\0\xC2\x05\0\0\xBB\x9A\x02\0@\x01\0\0\@V/\0\0\0\0\0\0\0\0\xE3\xF9AT+CEREG?'

# Trame à rechercher et supprimer
trame_to_remove = b'\xB5b\x01\x07\0\0\x08\x19'

# Recherche et suppression de la trame
data = data.replace(trame_to_remove, b'')

class Mia10:
    def __init__(self, data):
        self.rx_buffer = data
        self.year = {'X2': [0, 0]}
        self.month = 0
        self.day = 0
        self.hour = 0
        self.min = 0
        self.sec = 0
        self.dateValid = 0
        self.TODValid = 0
        self.PSM = 0
        self.gnssFixOK = 0
        self.LLHValid = 0
        self.lon = {'X4': [0, 0, 0, 0]}
        self.lat = {'X4': [0, 0, 0, 0]}
        self.height = {'X4': [0, 0, 0, 0]}
        self.decode()

    def decode(self):
        self.year['X2'][0] = self.rx_buffer[10]
        self.year['X2'][1] = self.rx_buffer[11]

        self.month = self.rx_buffer[12]
        self.day = self.rx_buffer[13]
        self.hour = self.rx_buffer[14]
        self.min = self.rx_buffer[15]
        self.sec = self.rx_buffer[16]

        self.dateValid = (self.rx_buffer[17] & 1) + ((self.rx_buffer[28] >> 6) & 1)
        self.TODValid = ((self.rx_buffer[17] >> 1) & 1) + ((self.rx_buffer[28] >> 7) & 1)
        self.PSM = (self.rx_buffer[27] >> 2) & 0x03
        self.gnssFixOK = self.rx_buffer[27] & 1
        self.LLHValid = not (self.rx_buffer[84] & 1)

        self.lon['X4'][0] = self.rx_buffer[30]
        self.lon['X4'][1] = self.rx_buffer[31]
        self.lon['X4'][2] = self.rx_buffer[32]
        self.lon['X4'][3] = self.rx_buffer[33]

        self.lat['X4'][0] = self.rx_buffer[34]
        self.lat['X4'][1] = self.rx_buffer[35]
        self.lat['X4'][2] = self.rx_buffer[36]
        self.lat['X4'][3] = self.rx_buffer[37]

        self.height['X4'][0] = self.rx_buffer[42]
        self.height['X4'][1] = self.rx_buffer[43]
        self.height['X4'][2] = self.rx_buffer[44]
        self.height['X4'][3] = self.rx_buffer[45]

    def combine_bytes(self, byte_list):
        # Combine the bytes and convert to signed 32-bit integer
        return struct.unpack('<i', bytes(byte_list))[0]

    def get_coordinates(self):
        lon = self.combine_bytes(self.lon['X4']) / 10000000.0
        lat = self.combine_bytes(self.lat['X4']) / 10000000.0
        height = self.combine_bytes(self.height['X4']) / 1000.0
        return lon, lat, height

mia10 = Mia10(data)
print(f"Year: {mia10.year}")
print(f"Month: {mia10.month}")
print(f"Day: {mia10.day}")
print(f"Hour: {mia10.hour}")
print(f"Min: {mia10.min}")
print(f"Sec: {mia10.sec}")
print(f"Date Valid: {mia10.dateValid}")
print(f"TOD Valid: {mia10.TODValid}")
print(f"PSM: {mia10.PSM}")
print(f"GNSS Fix OK: {mia10.gnssFixOK}")
print(f"LLH Valid: {mia10.LLHValid}")

lon, lat, height = mia10.get_coordinates()
print(f"Longitude: {lon}")
print(f"Latitude: {lat}")
print(f"Height: {height}")
