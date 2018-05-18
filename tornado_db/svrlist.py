
from .svrfactory import TornadoFactory
from .searchable import Searchable

import sys
from math import log10
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict

class SVRList(Searchable):
    @classmethod
    def from_csv(cls, fname):
        return cls.from_fobj(open(fname, 'rb'))

    @classmethod
    def from_fobj(cls, fobj):
        return cls.from_txt(fobj.read().decode('utf-8'))

    @classmethod
    def from_txt(cls, txt):
        lines = txt.split("\r\n")

        factory = cls.factory(lines[0].split(','))
        svrs = []

        for line in lines[1:]:
            if line == "":
                continue

            svrs.extend(factory.consume(line))

        svrs.extend(factory.flush())

        return cls(*svrs)

    def to_csv(self, fname):
        with open(fname, 'w') as csvf:
            first_pass = True
            for svr in self:
                entries = svr.to_csv(headers=first_pass)
                csvf.write(entries)

                first_pass = False

    def __init_subclass__(cls, factory):
        super().__init_subclass__()
        cls.factory = factory

    def __str__(self):
        n_places = int(log10(len(self))) + 1
        num_str = "%%%dd" % n_places
        svrstr = ""
        svrstr += " " * (n_places + 2)
        svrstr += "---Time-(UTC)--- "
        svrstr += " --States--"
        svrstr += " -Mag-"

        for idx, svr in enumerate(self):
            svrstr += "\n"
            svrstr += str(num_str % (idx + 1))
            svrstr += ". "
            svrstr += str(svr)
        return svrstr

    def days(self):
        svr_days = defaultdict(list)
        for svr in self:
            svr_day = (svr['datetime'] - timedelta(hours=12)).replace(hour=12, minute=0, second=0, microsecond=0)
            svr_days[svr_day].append(svr)

        return OrderedDict((svr_day, type(self)(svr_days[svr_day])) for svr_day in sorted(svr_days.keys()))


class TornadoList(SVRList, factory=TornadoFactory):
    pass
