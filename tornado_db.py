
import pandas as pd

import sys
from datetime import datetime, timedelta
from itertools import izip
from collections import OrderedDict, defaultdict
from urllib2 import urlopen

class TornadoDB(object):
    def __init__(self, db, meta):
        self._db = db
        self._meta = meta

    @classmethod
    def from_csv(cls, path="/data/tornadoes.csv"):
        return cls.from_file_obj(open(path))

    @classmethod
    def from_web(cls):
        url = "http://www.spc.noaa.gov/wcm/data/Actual_tornadoes.csv"
        return cls.from_file_obj(urlopen(url))

    @classmethod
    def from_file_obj(cls, fobj):
        col_names = [
            u'om_number', u'year', u'month', u'day', u'date', u'time', u'time_zone', 
            u'state', u'state_fips', u'state_seq', 
            u'f_scale', u'injuries', u'fatalities', u'prpty_loss', u'crop_loss', 
            u'start_lat', u'start_lon', u'end_lat', u'end_lon', u'length', u'width', 
            u'num_states', u'state_num', u'seg_num', u'county_fips1', u'county_fips2', u'county_fips3', u'county_fips4', 
            u'f_scale_mod'
        ]

        db = pd.read_csv(fobj, header=None, names=col_names, index_col=False)
        dts = [datetime.strptime("%s %s" % (d, t), "%Y-%m-%d %H:%M:%S") for d, t in izip(db['date'], db['time'])]
        tds = [timedelta(hours=0) if tz == 9 else timedelta(hours=6) for tz in db['time_zone']]

        dt = pd.to_datetime(pd.Series([dt + td for dt, td in izip(dts, tds)], index=db.index))

        del db['date'], db['time'], db['time_zone'], db['year'], db['month'], db['day']

        db['time'] = dt
        db.set_index('time', inplace=True)

        db_start = db.iloc[0].name.to_pydatetime().replace(month=1, day=1, hour=0, minute=0)
        db_end = db.iloc[-1].name.to_pydatetime().replace(month=12, day=31, hour=23, minute=59)

        meta = {
            'db_start': db_start,
            'db_end': db_end,
        }
        return cls(db, meta)

    def search(self, **kwargs):
        new_db = self._db

        def get_col(db, col):
            if col == 'time':
                db_col = new_db.index
            else:
                db_col = new_db[col]
            return db_col

        for col, val in kwargs.iteritems():
            db_col = get_col(new_db, col)
            try:
                # Try for function-type items
                if type(val) in [ list, tuple ]:
                    for v in val:
                        db_col = get_col(new_db, col)
                        new_db = new_db[v(db_col)]
                else:
                    new_db = new_db[val(db_col)]
            except TypeError:
                # Try for single-value items
                if type(val) in [ list, tuple ]:
                    new_db = new_db[[ v in val for v in db_col ]]
                else:
                    new_db = new_db[[ v == val for v in db_col ]]

        return self._subset(new_db)

    def _subset(self, new_db):
        return type(self)(new_db, self._meta)

    def days(self):
        tor_days = defaultdict(type(self._db))
        for day, df in pd.groupby(self._db, by=[self._db.index.year, 
                                                self._db.index.month, 
                                                self._db.index.day, 
                                                self._db.index.hour]):
            dt = datetime.strptime("%d%d%d%d" % day, "%Y%m%d%H")
            if dt.hour < 12:
                dt -= timedelta(days=1)
        
            dt = dt.replace(hour=12)
            tor_days[dt] = tor_days[dt].append(df)
        
        return OrderedDict((d, self._subset(tor_days[d])) for d in sorted(tor_days.keys()))

    def __getitem__(self, key):
        item = None
        if key == 'time':
            item = self._db.index
        else:
            item = self._db[key]
        return item

    def list(self, fobj=sys.stdout):
        fobj.write("\n--------Time------- -State- -F-scale-\n")
        for time, state, f_scale in izip(self._db.index, self._db['state'], self._db['f_scale']):
            fs = "EF%d" % f_scale if time > datetime(2007, 2, 1, 0, 0, 0) else "F%d" % f_scale
            fobj.write("%s %7s %9s\n" % (time, state, fs))

    def count(self):
        return len(self._db)

    def meta(*args):
        meta_vals = {}

        if args == []:
            meta_vals.update(self._meta)
        else:
            for arg in arg:
                meta_vals[arg] = self._meta[arg]

        return meta_vals

    @staticmethod
    def byyear(*years):
        def get_vals(times):
            return [ (t - timedelta(hours=12)).year in years for t in times ]
        return get_vals

    @staticmethod
    def bymonth(*months):
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        month_abrvs = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        def try_strings(mo):
            try:
                mo_num = month_names.index(mo) + 1
            except ValueError:
                try:
                    mo_num = month_abrvs.index(mo) + 1
                except ValueError:
                    mo_num = mo
            return mo_num

        month_nums = [ try_strings(mo) for mo in months ]

        def get_vals(times):
            return [ (t - timedelta(hours=12)).month in month_nums for t in times ]
        return get_vals

    @staticmethod
    def bycday(*days):
        cday_starts = [ d.replace(hour=12, minute=0, second=0, microsecond=0) for d in days ]
        cday_ends = [ d + timedelta(days=1) for d in cday_starts ]

        def get_vals(times):
            return [ any(cds <= t < cde for cds, cde in izip(cday_starts, cday_ends)) for t in times ]
        return get_vals

    @staticmethod
    def byhour(*hours):
        def get_vals(times):
            return [ t.hour in hours for t in times ]
        return get_vals

if __name__ == "__main__":
    db = TornadoDB.from_csv()
    ok_nov = db.search(state='OK', time=TornadoDB.bymonth(11), f_scale=lambda f: f >= 2)
#   ok_nov.list()

    print "November strong-violent tornado days in Oklahoma:"
    for day, tors in ok_nov.days().iteritems():
        print "%s (%d)" % (day.strftime('%d %b %Y'), tors.count())

    print
    db.search(state='KS', time=[TornadoDB.bymonth('March', 'Apr', 5), TornadoDB.byyear(1991)]).list() 

#   db.search(state=['OK', 'KS'], time=TornadoDB.bycday(datetime(2011, 5, 24))).list()
#   db.search(length=lambda l: l > 100).list()

#   print "Oklahoma strong tors between 04-11 UTC"
#   print db.search(state='OK', f_scale=lambda f: f >= 2, time=TornadoDB.byhour(4, 5, 6, 7, 8, 9, 10, 11)).count()
#   print
#   print "Alabama strong tors between 04-11 UTC"
#   print db.search(state='AL', f_scale=lambda f: f >= 2, time=TornadoDB.byhour(4, 5, 6, 7, 8, 9, 10, 11)).count()
