import os

import localizationpy.file_manager as fm


class AerialMeasure(object):
    """
    Class containing the field values for a specific antenna and the relevant information
    of the measure itself
    """
    def __init__(self, file_path: str):
        self.name = os.path.basename(file_path).split('.')[0]
        self.id = self.name.split('_')[-1]
        self.freq, entries = fm._parse_file_aerial_measure(file_path)
        self.entries = dict()
        for entry in entries:
            self.entries.update({entry.id: entry})

    def __repr__(self):
        return (f'Aerial {self.id}\r\n'
                f'------------\r\n'
                f'\tName: {self.name!r}\r\n'
                f'\tFreq: {self.freq!r}\r\n'
                f'\tNum of measures: {len(self.entries)!r}\r\n')

