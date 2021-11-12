
from datetime import datetime, timedelta
from collections import defaultdict

from .searchable import SearchableItem
from .fips import fips

_epoch = datetime(1970, 1, 1, 0)

class TornadoSegment(object):
    aliases = {
        'state':'st',
        'magnitude':'mag',
        'fatalities':'fat',
        'injuries':'inj',
        'length':'len',
        'width':'wid',
        'start_lat':'slat',
        'end_lat':'elat',
        'start_lon':'slon',
        'end_lon':'elon',
        'counties':'cty_fips',
    }

    cols = ["om", "yr", "mo", "dy", "date", "time", "tz", 
            "st", "stf", "stn", "mag", "inj", "fat", "loss", "closs", 
            "slat", "slon", "elat", "elon", "len", "wid", 
            "ns", "sn", "sg", "f1", "f2", "f3", "f4", "fc"]

    def __init__(self, **kwargs):
        try:
            kwargs['datetime'] = _epoch + timedelta(seconds=kwargs['datetime'])
        except TypeError:
            pass

        if kwargs['elat'] < 10:
            kwargs['elat'] = kwargs['slat']
        if kwargs['elon'] > -10:
            kwargs['elon'] = kwargs['slon']

        cty_fips = []
        for attr in ['f1', 'f2', 'f3', 'f4']:
            if attr not in kwargs:
                continue

            if kwargs[attr] != 0:
                cty_st_fips = kwargs['stf'] * 1000 + kwargs[attr]
                cty_fips.append(cty_st_fips)

            del kwargs[attr]

        kwargs['cty_fips'] = cty_fips

        self._attrs = kwargs

        def replace_fips(old, new):
            cty_fips = self._attrs['cty_fips']
            if old in cty_fips:
                cty_fips[cty_fips.index(old)] = new
                cty_fips = list(set(cty_fips))
            self._attrs['cty_fips'] = cty_fips

        replace_fips(46131, 46071) # Washabaugh County, SD merged with Jackson County, SD
        replace_fips(12025, 12086) # Dade County, FL renamed Miami-Dade County, FL
        replace_fips(13597, 13197) # Typo on the FIPS code for Marion County, GA?
        replace_fips(51039, 51037) # Typo on the FIPS code for Charlotte County, VA?
        replace_fips(27002, 27003) # Typo on the FIPS code for Anoka County, MN?
        replace_fips(51123, 51800) # Suffolk City, VA replaced Nansemond County, VA
        replace_fips(46001, 46003) # Typo on the FIPS code for Aurora County, SD?
        replace_fips(29677, 29077) # Typo on the FIPS code for Greene County, MO?
        replace_fips(21022, 21033) # Typo on the FIPS code for Caldwell County, KY?
        replace_fips(42159, 42015) # Typo on the FIPS code for Bradford County, PA?
        replace_fips(2155, 2050) # Old code for Bethel Census Area?
        replace_fips(72008, 72005) # Typo on the FIPS code for Aguadilla, PR?
        replace_fips(2181, 2013) # Old code for Aleutians East Borough?
        replace_fips(46113, 46102) # Shannon County, SD became Ogalala Lakota County

        # Patch some goofs I noticed in the database
        yr = kwargs['datetime'].year
        if yr == 1953 and self['om'] == 265 and self['st'] == 'IA':
            self._attrs['om'] = 263
        if yr == 1961 and self['om'] == 456 and self['st'] == 'SD':
            self._attrs['om'] = 454
        if yr == 1966 and self['om'] == 13:
            self._attrs['cty_fips'] = [51083]
        if yr == 1966 and self['om'] == 14:
            self._attrs['cty_fips'] = [51081]
        if yr == 1995 and self['om'] == 9999 and self['st'] == 'IA':
            self._attrs['om'] = 9998
        if yr == 2015 and self['om'] == 576455 and self['st'] == 'NE':
            self._attrs['om'] = 576454


    def merge(self, other):
        seg_tup_self = (self['ns'], self['sn'], self['sg'])
        seg_tup_other = (other['ns'], other['sn'], other['sg'])

        if seg_tup_self in [(1, 1, 1), (2, 0, 1), (3, 0, 1)] or other['sg'] == -9:
            merge_sg = self
        else:
            merge_sg = other

        merge_sg._attrs['cty_fips'] = self['cty_fips'] + other['cty_fips']
        return merge_sg

    def to_csv(self):
        cols = TornadoSegment.cols
        fips_cols = ['f1', 'f2', 'f3', 'f4']

        attrs = self._attrs
        tor_dt = attrs['datetime'] - timedelta(hours=6)
        attrs['yr'] = tor_dt.year
        attrs['mo'] = tor_dt.month
        attrs['dy'] = tor_dt.day
        attrs['date'] = tor_dt.strftime("%Y-%m-%d")
        attrs['time'] = tor_dt.strftime("%H:%M:%S")
        attrs['tz'] = 3

        fips = [ cf % 1000 for cf in attrs['cty_fips'] ]
        csv = ""
        while len(fips) > 4:
            fips_chunk = [ fips.pop(0) for idx in range(4) ]
            if len(csv) > 0:
                attrs.update({'sn': 0, 'sg': -9, 'slat': 0, 'elat': 0, 'slon': 0, 'elon': 0, 'wid': 0, 'len': 0, 
                              'inj': 0, 'fat': 0, 'loss': 0, 'closs': 0})

            for fp, col in zip(fips_chunk, fips_cols):
                attrs[col] = fp

            csv += ",".join(str(attrs[c]) for c in cols) + "\n"

        for col in fips_cols:
            attrs[col] = 0

        for fp, col in zip(fips, fips_cols):
            attrs[col] = fp

        if len(csv) > 0:
            attrs.update({'sn': 0, 'sg': -9, 'slat': 0, 'elat': 0, 'slon': 0, 'elon': 0, 'wid': 0, 'len': 0, 
                          'inj': 0, 'fat': 0, 'loss': 0, 'closs': 0})

        csv += ",".join(str(attrs[c]) for c in cols) + "\n"
        return csv

    def __getitem__(self, attr):
        try:
            attr = TornadoSegment.aliases[attr]
        except KeyError:
            pass

        return self._attrs[attr]

    def __str__(self):
        return str(self._attrs)

    def __repr__(self):
        return repr(self._attrs)

    def __iter__(self):
        for k, v in self._attrs.items():
            yield k, v


class Tornado(SearchableItem):
    def __init__(self, segments):
        self._segs = segments

    def __str__(self):
        time_str = self['datetime'].strftime("%Y-%m-%d %H:%M")
        states = ", ".join(self['st'])
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

    @classmethod
    def from_segments(cls, segments):
        if len(segments) == 1:
            return cls(segments)

        segments_st = defaultdict(list)
        for seg in segments:
            segments_st[seg['st']].append(seg)

        states = [seg['st'] for seg in segments]
        states_unique = list(set(states))
        states_unique.sort(key=states.index)
        states = states_unique

        seg_list = []

        for st in states:
            st_segs = segments_st[st]
            if len(st_segs) > 1:
                accum_seg = st_segs[0]
                for seg in st_segs[1:]:
                    accum_seg = accum_seg.merge(seg)
                seg_list.append(accum_seg)
            else:
                seg_list.extend(st_segs)

        return cls(seg_list)

    def to_csv(self, headers=False):
        csv = ""
        cols = TornadoSegment.cols

        if headers:
            csv += ",".join(cols) + "\n"

        if len(self._segs) > 1:
            self_dict = {}
            for col in cols:
                if col == 'yr':
                    val = (self['datetime'] - timedelta(hours=6)).year
                elif col == 'mo':
                    val = (self['datetime'] - timedelta(hours=6)).month
                elif col == 'dy':
                    val = (self['datetime'] - timedelta(hours=6)).day
                elif col == 'date':
                    val = (self['datetime'] - timedelta(hours=6)).strftime("%Y-%m-%d")
                elif col == 'time':
                    val = (self['datetime'] - timedelta(hours=6)).strftime("%H:%M:%S")
                elif col == 'tz':
                    val = 3
                elif col in ['f1', 'f2', 'f3', 'f4']:
                    val = 0
                elif col in ['om', 'st', 'stf', 'stn', 'ns', 'sn', 'sg']:
                    val = self[col][0]
                else:
                    val = self[col]
                self_dict[col] = val

            if self_dict['ns'] > 1:
                self_dict['sn'] = 0
                self_dict['sg'] = 1

            csv += ",".join(str(self_dict[col]) for col in cols) + "\n"

        for seg in self._segs:
            csv += seg.to_csv()

        return csv

    def __getitem__(self, attr):
        try:
            db_attr = TornadoSegment.aliases[attr]
        except KeyError:
            db_attr = attr

        attr_list = [ seg[db_attr] for seg in self._segs ]

        if db_attr in [ 'wid', 'mag', 'closs', 'loss', 'fc' ]:
            result = max(attr_list)
        elif db_attr in [ 'len', 'fat', 'inj' ]:
            result = attr_list[0] #sum(attr_list)
        elif db_attr in [ 'datetime', 'slat', 'slon' ]:
            result = attr_list[0]
        elif db_attr in [ 'elat', 'elon' ]:
            result = attr_list[-1]
        elif db_attr in [ 'cty_fips' ]:
            result = [ c for lst in attr_list for c in lst ]
            if attr == 'counties':
                def lookup_fips(cty):
                    fips_entry = fips.lookup_fips(cty)
                    return fips_entry['county'], fips_entry['state']

                result = [ lookup_fips(c) for c in result ]
        else:
            result = attr_list

        return result

    def _get_mag_str(self):
        mag_str = 'U' if self['mag'] < 0 else str(self['mag'])
        return "EF%s" % mag_str if self['datetime'] >= datetime(2007, 2, 1, 0) else "F%s" % mag_str
