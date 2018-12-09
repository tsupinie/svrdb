
from .searchable import SearchableItem

from datetime import datetime, timedelta

_epoch = datetime(1970, 1, 1, 0)

class Hail(SearchableItem):
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
            db_attr = Hail.aliases[attr]
        except KeyError:
            db_attr = attr

        return self._attrs[db_attr]

    def __str__(self):
        time_str = self['datetime'].strftime("%Y-%m-%d %H:%M")
        states = self['st']
        mag = self._get_mag_str()

        return "%16s %11s %5s" % (time_str, states, mag)

    def _repr_html_(self, _make_table=True):
        html_str = ''
        if _make_table:
            html_str += '<table><tr>'

        time_str = self['datetime'].strftime("%Y-%m-%d %H:%M")
        mag_str = self._get_mag_str()
        html_str += '<td>%s</td><td>%s</td>' % (time_str, mag_str)

        if _make_table:
            html_str += '</tr></table>'
        return html_str

    def _get_mag_str(self):
        return "%2.f" % self['mag']
