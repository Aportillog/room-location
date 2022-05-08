import math

import localizationpy.metrics as mt


class FieldValue(object):
    """
    Class containing values of an electromagnetic field, matching a specific point with the id property
    """
    def __init__(self, id: int, ex: complex, ey: complex, ez: complex):
        self.id = id
        self.ex = ex
        self.ey = ey
        self.ez = ez

    def __str__(self):
        return 'Field Value {0} - EX: {1}, EY: {2}, EZ: {3}'.format(self.id, self.ex, self.ey, self.ez)

    def power(self, dbm=True):
        """
        Calculate the power of the field value (defined by its Electric field components).
        Follows this equation: pot=mod(Ex)^2+mod(Ey)^2+mod(Ez)^2

        :return: Float with three decimal precision
        """
        res = 0.0
        if dbm:
            ez_module = mt.get_complex_module(self.ez)
            if ez_module != 0:
                aerial_gain = 0
                radiated_power = 0
                freq = 2.4e9  # GHz
                res += 20 * math.log10(ez_module)
                res += -10 * math.log10(8 * 120)
                res += aerial_gain
                res += radiated_power
                res += 20 * math.log10(3e8 / (freq * math.pi))
                res += 10 * math.log10(3 / 50)
                res += 30
            else:
                res = -200  # Considering -200 as "infinite"

        else:
            power = mt.get_complex_module(self.ex)**2
            power += mt.get_complex_module(self.ey)**2
            power += mt.get_complex_module(self.ez)**2

            if power != 0:
                res = math.log10(power)

        return float('%.3f' % res)
