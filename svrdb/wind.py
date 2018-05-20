
from .searchable import SearchableItem

from datetime import datetime, timedelta

_epoch = datetime(1970, 1, 1, 0)

class Wind(SearchableItem):
    aliases = {
        'state':'st',
        'magnitude':'mag',
        'fatalities':'fat',
        'injuries':'inj',
        'lat':'slat',
        'lon':'slon',
        'counties':'cty_fips',
    }

    def __init__(self, **kwargs):
        try:
            kwargs['datetime'] = _epoch + timedelta(seconds=kwargs['datetime'])
        except TypeError:
            pass

        kwargs['cty_fips'] = kwargs['stf'] * 1000 + kwargs['f1']
        del kwargs['f1']

        self._attrs = kwargs

    def __getitem__(self, attr):
        try:
            db_attr = Wind.aliases[attr]
        except KeyError:
            db_attr = attr

        return self._attrs[db_attr]

    def __str__(self):
        time_str = self['datetime'].strftime("%Y-%m-%d %H:%M")
        states = self['st']

        if self['mag'] == 0:
            mag = '--'
        else:
            mag = "%s%d" % (self['mt'][0], self['mag'])

        return "%16s %11s %5s" % (time_str, states, mag)
