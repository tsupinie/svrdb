
from .tornado import TornadoSegment, Tornado
from .wind import Wind
from .hail import Hail

import pandas as pd

from datetime import datetime, timedelta
from collections import defaultdict

_epoch = datetime(1970, 1, 1, 0)

class ReportUnpacker(object):
    def __init_subclass__(cls, report_primitive):
        super().__init_subclass__()
        cls.report_primitive = report_primitive

    def parse(self, df):
        def str_to_timestamp(date, time):
            yr, mo, dy = date.split('-')
            hr, mn, sc = time.split(':')
            dt = datetime(int(yr), int(mo), int(dy), int(hr), int(mn), int(sc))
            return (dt - _epoch).total_seconds()

        dts = [str_to_timestamp(d, t) for d, t in zip(df['date'], df['time'])]
        tds = [0 if tz == 9 else 6 * 3600 for tz in df['tz']]

        dt = pd.Series([dt + td for dt, td in zip(dts, tds)], index=df.index)

        del df['date'], df['time'], df['tz'], df['yr'], df['mo'], df['dy']
        df['datetime'] = dt

        reports = df.apply(type(self).to_reports, axis=1)
        return reports.tolist()

    def merge(self, svrs):
        return svrs

    @classmethod
    def to_reports(cls, series):
        rep_dict = dict(zip(series.index.values, series.values))
        return cls.report_primitive(**rep_dict)


class TornadoUnpacker(ReportUnpacker, report_primitive=TornadoSegment):
    def merge(self, segments):
        segs_om = defaultdict(list)
        for seg in segments:
            segs_om[seg['datetime'].year, seg['om']].append(seg)

        def patch_seg(yr, om, patch):
            seg = dict(segs_om[yr, om][0])
            seg.update(patch)
            segs_om[yr, om].append(TornadoSegment(**seg))

        patch_seg(1993, 74, {'st':'NE', 'stf':31, 'f1':65, 'stn':1, 'elat':40.02, 'elon':-99.92})
        patch_seg(2006, 80, {'st':'IL', 'stf':17, 'f1':157, 'f2':145, 'stn':5, 'slat':37.78, 'slon':-90.05})

        tors = [ Tornado.from_segments(segs) for segs in segs_om.values() ]
        return tors

class WindUnpacker(ReportUnpacker, report_primitive=Wind):
    def parse(self, df):
        del df['elat'], df['elon'], df['len'], df['wid'], df['ns'], df['sn'], df['sg'], df['f2'], df['f3'], df['f4']

        return super(WindUnpacker, self).parse(df)

class HailUnpacker(ReportUnpacker, report_primitive=Hail):
    def parse(self, df):
        del df['elat'], df['elon'], df['len'], df['wid'], df['ns'], df['sn'], df['sg'], df['f2'], df['f3'], df['f4']

        return super(HailUnpacker, self).parse(df)
