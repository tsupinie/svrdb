
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


if __name__ == "__main__":
    from searchable import bymonth, bycday
    tls = TornadoList.from_csv('/data/All_tornadoes.csv')

#   ok_stg_aug = tls.search(state='OK', datetime=bymonth('AUGUST'), magnitude=lambda m: m >= 2)
#   print(ok_stg_aug)
#   print(ok_stg_aug.days().keys())

    print(tls.search(datetime=bycday(datetime(1991, 4, 26))))

#   tls.to_csv("/data/All_tornadoes_out.csv")
