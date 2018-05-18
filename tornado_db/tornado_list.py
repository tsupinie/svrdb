
from .tornado import TornadoFactory
from .searchable import Searchable

import sys
from math import log10
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict

class TornadoList(Searchable):
    @classmethod
    def from_csv(cls, fname):
        return cls.from_fobj(open(fname, 'rb'))

    @classmethod
    def from_fobj(cls, fobj):
        return cls.from_txt(fobj.read().decode('utf-8'))

    @classmethod
    def from_txt(cls, txt):
        lines = txt.split("\r\n")

        factory = TornadoFactory(lines[0].split(','))
        tors = []

        for line in lines[1:]:
            if line == "":
                continue

            tors.extend(factory.consume(line))

        tors.extend(factory.flush())

        return cls(*tors)

    def to_csv(self, fname):
        with open(fname, 'w') as csvf:
            first_pass = True
            for tor in self:
                entries = tor.to_csv(headers=first_pass)
                csvf.write(entries)

                first_pass = False

    def __str__(self):
        n_places = int(log10(len(self))) + 1
        num_str = "%%%dd" % n_places
        torstr = ""
        torstr += " " * (n_places + 2)
        torstr += "---Time-(UTC)--- "
        torstr += " --States--"
        torstr += " -Mag-"

        for idx, tor in enumerate(self):
            torstr += "\n"
            torstr += str(num_str % (idx + 1))
            torstr += ". "
            torstr += str(tor)
        return torstr

    def days(self):
        tor_days = defaultdict(list)
        for tor in self:
            tor_day = (tor['datetime'] - timedelta(hours=12)).replace(hour=12, minute=0, second=0, microsecond=0)
            tor_days[tor_day].append(tor)

        return OrderedDict((tor_day, type(self)(tor_days[tor_day])) for tor_day in sorted(tor_days.keys()))


def byyear(*years):
    def get_vals(time):
        return (time - timedelta(hours=12)).year in years
    return get_vals


def bymonth(*months):
    month_names = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    month_abrvs = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    def try_strings(mo):
        try:
            mo_num = month_names.index(mo.lower()) + 1
        except (ValueError, AttributeError):
            try:
                mo_num = month_abrvs.index(mo.lower()) + 1
            except (ValueError, AttributeError):
                mo_num = mo
        return mo_num

    month_nums = [ try_strings(mo) for mo in months ]

    def get_vals(time):
        return (time - timedelta(hours=12)).month in month_nums
    return get_vals


def bycday(*days):
    cday_starts = [ d.replace(hour=12, minute=0, second=0, microsecond=0) for d in days ]
    cday_ends = [ d + timedelta(days=1) for d in cday_starts ]

    def get_vals(time):
        return any(cds <= time < cde for cds, cde in zip(cday_starts, cday_ends))
    return get_vals


def byhour(*hours):
    def get_vals(time):
        return time.hour in hours
    return get_vals


if __name__ == "__main__":
    tls = TornadoList.from_csv('/data/All_tornadoes.csv')

#   ok_stg_aug = tls.search(state='OK', datetime=bymonth('AUGUST'), magnitude=lambda m: m >= 2)
#   print(ok_stg_aug)
#   print(ok_stg_aug.days().keys())

    print(tls.search(datetime=bycday(datetime(1991, 4, 26))))

#   tls.to_csv("/data/All_tornadoes_out.csv")
