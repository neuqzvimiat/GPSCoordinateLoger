try:
    import pyb
except ImportError:
    import tests.pyb as pyb

try:
    import ure
except ImportError:
    import re as ure


class Gps:

    def __init__(self):
        self._uart1 = pyb.UART(1)
        self.buff = bytearray(500)
        self._longitude = 0.0
        self._latitude = 0.0
        self._time = ''
        self._date = ''
        self._usedSats = 0
        self._d = {
            'GPRMC':
                    ['Cmd',
                    'TimeStamp',
                    'Validity',
                    'CurrLatitude',
                    'LatDir',
                    'CurrLongitude',
                    'LongDir',
                    'SpeedInKnots',
                    'TrueCourse',
                    'DateStamp',
                    'Variation',
                    'VarDir',
                    'Checksum'],
            'GPVTG':
                    ['Cmd',
                     'TrackDegTrue',
                    'FixedTextT',
                    'TrackDegMag',
                    'FixedTextM',
                    'SpeedKnots',
                    'FixedTextN',
                    'SpeedKmvsHr',
                    'FixedTextK',
                    'Checksum'],
            'GPGGA':
                    ['Cmd',
                     'UTCOfPosition',
                    'Latitude',
                    'LatDir',
                    'Longitude',
                    'LongDir',
                    'GPSQualityIndicator',
                    'NumberOfSatInUse',
                    'HorizontalDilution',
                    'AntenaAltitude',
                    'AntMeters',
                    'GeoidalSeparation',
                    'GeoMeters',
                    'AgeInSeconds',
                    'DiffID',
                    'Checksum'],
            'GPGSA':
                    ['Cmd',
                     'Mode1',
                    'Mode2',
                    'ID1',
                    'ID2',
                    'ID3',
                    'ID4',
                    'ID5',
                    'ID6',
                    'ID7',
                    'ID8',
                    'ID9',
                    'ID10',
                    'ID11',
                    'ID12',
                    'PDOP',
                    'HDOP',
                    'VDOP',
                    'Checksum'],
            'GPGSV':
                    ['Cmd',
                     'TotalMEssages',
                    'MessageNumber',
                    'TotalSVsInView',
                    'SVNumber1',
                    'ElevationDeg1',
                    'AzimuthDeg1',
                    'SNR1',
                    'SVNumber2',
                    'ElevationDeg2',
                    'AzimuthDeg2',
                    'SNR2',
                    'SVNumber3',
                    'ElevationDeg3',
                    'AzimuthDeg3',
                    'SNR3',
                    'SVNumber4',
                    'ElevationDeg4',
                    'AzimuthDeg4',
                    'SNR4',
                    'Checksum'],
            'GPGLL':
                    ['Cmd',
                     'CurrLatitude',
                    'LatDir',
                    'CurrLongitude',
                    'LongDir',
                    'UTC',
                    'DataValid',
                    'Checksum'],
        }
        self._cmd = None
        self._regx = [
            #'^\$(GPRMC)' + ',([^,]*)' * 12 + '\r\n',
            '^\$(GPRMC),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),(\w*)\*([0-9A-F]{2})',
            '^\$(GPVTG)' + ',([^,]*)' * 9 + '\r\n',
            '^\$(GPGGA),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*)\*([0-9A-F]{2})\r\n',
            # '^\$(GPGSA)' + ',([^,]*)' * 16 + '\r\n',
            # '^\$(GPGSV)' + ',([^,]*)' * 20 + '\r\n',
            '^\$(GPGLL)' + ',([^,]*)' * 7 + '\r\n',
            #^\$(GPRMC),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),(\w*)\*([0-9A-F]{2})$
        ]

        self._regxc = [ure.compile(s) for s in self._regx]
        self._uart1.init(9600, read_buf_len=1024)

    def readData(self):
        self.buff = self._uart1.readline()
        return self.buff

    def parse(self, buff:bytearray):

        if buff is None:
            return None

        buf_dec = buff.decode()

        # print(buf_dec)
        dictionary = {}
        for r in self._regxc:
            m = r.match(buf_dec)

            if m is None:
                continue

            self._cmd = m.group(1)
            # print('cmd -> {}'.format(self._cmd))
            i = 1
            for name in self._d[self._cmd]:
                dictionary[name] = m.group(i)
                i += 1

            break

        print('Cmd -> {}'.format(dictionary.get('Cmd')))
        if dictionary.get('Cmd') == 'GPGGA':
            self._usedSats = int(dictionary.get('NumberOfSatInUse'))
        elif dictionary.get('Cmd') == 'GPRMC':

            print('CurrLatitude -> {}'.format(dictionary.get('CurrLatitude')))
            print('CurrLongitude -> {}'.format(dictionary.get('CurrLongitude')))
            if (dictionary.get('CurrLatitude') != '' and dictionary.get('CurrLongitude') != '' and
                dictionary.get('DateStamp') != '' and dictionary.get('TimeStamp') != ''):

                latitude = float(dictionary.get('CurrLatitude'))
                longitude = float(dictionary.get('CurrLongitude'))
                self._time = dictionary.get('TimeStamp')
                self._date = dictionary.get('DateStamp')

                c, d = self.dm2dd(latitude, longitude)

                print('lat -> {:.6f}'.format(c))
                print('long -> {:.6f}'.format(d))
                print('Used Satellites -> {}'.format(self._usedSats))
                if self._usedSats >= 5:
                    if (not ((self._latitude + 0.0002) > c and (self._latitude - 0.0002) < c) or
                            not ((self._longitude + 0.0002) > d and (self._longitude - 0.0002) < d)):

                        self._latitude = c
                        self._longitude = d
                        # print('Time -> {}'.format(self._time))
                        print('Latitude -> {:.6f}'.format(self._latitude))
                        print('Longitude -> {:.6f}'.format(self._longitude))

                        dict = {}
                        dict['Latitude'] = str(self._latitude)
                        dict['Longitude'] = str(self._longitude)
                        dict['Date'] = self._date
                        dict['Time'] = self._time

                        pyb.LED(1).toggle()

                        return dict

        return None


    def dm2dd(self, latitude, longitude):
        """ Convert degrees minute to decimal degrees GPS coordinate. """
        lat_deg = (latitude // 100)
        long_deg = (longitude // 100)
        a = (((latitude * 1000000.0) % 100000000) / 60.0) % 1000000
        b = (((longitude * 1000000.0) % 100000000) / 60.0) % 1000000
        c = a / 1000000.0 + lat_deg
        d = b / 1000000.0 + long_deg
        return c, d
