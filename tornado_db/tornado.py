
from datetime import datetime, timedelta
import ast
from collections import defaultdict
from searchable import SearchableItem

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

    parsers = {
        'om': int, 'yr': int, 'mo': int, 'dy': int, 'date': str, 'time': str, 'tz': int,
        'st': str, 'stf': int, 'stn': int, 'mag': int, 'inj': int, 'fat': int, 'loss': float, 'closs': float,
        'slat': float, 'slon': float, 'elat': float, 'elon': float, 'len': float, 'wid': int,
        'ns': int, 'sn': int, 'sg': int, 'f1': int, 'f2': int, 'f3': int, 'f4': int, 'fc': int,
    }

    def __init__(self, **kwargs):
        tor_dt = datetime.strptime("%s %s" % (kwargs['date'], kwargs['time']), "%Y-%m-%d %H:%M:%S")
        tz_offset = timedelta(hours=6) if kwargs['tz'] == 3 else timedelta(hours=0)
        tor_dt += tz_offset

        for attr in ['date', 'time', 'yr', 'mo', 'dy', 'tz']:
            del kwargs[attr]

        cty_fips = []
        for attr in ['f1', 'f2', 'f3', 'f4']:
            if kwargs[attr] != 0:
                cty_st_fips = kwargs['stf'] * 1000 + kwargs[attr]
                cty_fips.append(cty_st_fips)

            del kwargs[attr]

        kwargs['time'] = tor_dt
        kwargs['cty_fips'] = cty_fips

        self._attrs = kwargs
        self._patch()

    def merge(self, other):
        # This fails for tornadoes that leave and then re-enter a state (for example, see OM#480993, 2013-11-17)
        if self['ns'] == 1:
            if self['sn'] == 1:
                merge_sg = other
            else:
                merge_sg = self
        else:
            if other['sn'] == 1:
                merge_sg = other
            else:
                merge_sg = self

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

    def _patch(self):
        # Patch some goofs I noticed in the database
        if self['time'].year == 1953 and self['om'] == 265 and self['st'] == 'IA':
            self._attrs['om'] = 263
        if self['time'].year == 1961 and self['om'] == 456 and self['st'] == 'SD':
            self._attrs['om'] = 454
        if self['time'].year == 1995 and self['om'] == 9999 and self['st'] == 'IA':
            self._attrs['om'] = 9998
        if self['time'].year == 2015 and self['om'] == 576455 and self['st'] == 'NE':
            self._attrs['om'] = 576454


class Tornado(SearchableItem):
    def __init__(self, segments):
        self._segs = segments

    def __str__(self):
        time_str = self['time'].strftime("%Y-%m-%d %H:%M")
        states = ", ".join(self['st'])
        mag = "EF%d" % self['mag'] if self['time'] >= datetime(2007, 2, 1, 0) else "F%d" % self['mag']
        return "%16s %11s %5s" % (time_str, states, mag)

    @classmethod
    def from_segments(cls, segments):
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
            result = sum(attr_list)
        elif db_attr in [ 'time', 'slat', 'slon' ]:
            result = attr_list[0]
        elif db_attr in [ 'elat', 'elon' ]:
            result = attr_list[-1]
        elif db_attr in [ 'cty_fips' ]:
            result = [ c for lst in attr_list for c in lst ]
            if attr == 'counties':
                pass
        else:
            result = attr_list

        return result


class TornadoFactory(object):
    def __init__(self):
        self._year = None
        self._cols = None
        self._segments = defaultdict(list)

    def consume(self, line):
        def parse(val):
            try:
                pval = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                pval = val
            return pval

        results = []

        if self._cols is None:
            self._cols = line.split(",")
        else:
            line_dict = dict((c, parse(v)) for c, v in zip(self._cols, line.split(",")))
            seg = TornadoSegment(**line_dict)
            om = seg['om']
            yr = seg['time'].year

            if self._year is not None and yr != self._year:
                results = self.flush()

            self._segments[om].append(seg)
            if yr == 1993 and om == 74:
                line_dict.update({'st':'NE', 'stf':31, 'f1':65, 'stn':1, 'elat':40.02, 'elon':-99.92})
                seg = TornadoSegment(**line_dict)
                self._segments[om].append(seg)
            if yr == 2006 and om == 80 and seg['sg'] == 1:
                line_dict.update({'st':'IL', 'stf':17, 'f1':157, 'f2':145, 'stn':5, 'slat':37.78, 'slon':-90.05})
                seg = TornadoSegment(**line_dict)
                self._segments[om].append(seg)

            self._year = yr
        return results

    def flush(self):
        result = []
        for segs in self._segments.values():
            if TornadoFactory._is_complete(segs):
                result.append(Tornado.from_segments(segs))
            else:
                print("Incomplete segment list:")
                for seg in segs:
                    print(seg)

        self._year = None
        self._segments = defaultdict(list)

        return result

    @staticmethod
    def _is_complete(seg_list):
        states = list(set(seg['st'] for seg in seg_list))
        return len(states) == seg_list[0]['ns']

