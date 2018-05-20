
from .parsers import TornadoUnpacker, WindUnpacker
from .searchable import Searchable

import pandas as pd

import sys
from math import log10
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from io import StringIO

class SVRList(Searchable):
    @classmethod
    def from_csv(cls, fname):
        return cls.from_fobj(open(fname, 'rb'))

    @classmethod
    def from_fobj(cls, fobj):
        return cls.from_txt(fobj.read().decode('utf-8'))

    @classmethod
    def from_txt(cls, txt):
        sio = StringIO(txt)
        df = pd.read_csv(sio, index_col=False, dtype={'mt': str})

        unpacker = cls.unpacker()
        reports = unpacker.parse(df)
        svrs = unpacker.merge(reports)

        return cls(*svrs)

    def to_csv(self, fname):
        with open(fname, 'w') as csvf:
            first_pass = True
            for svr in self:
                entries = svr.to_csv(headers=first_pass)
                csvf.write(entries)

                first_pass = False

    def __init_subclass__(cls, unpacker):
        super().__init_subclass__()
        cls.unpacker = unpacker

    def __str__(self):
        if len(self) > 0:
            n_places = int(log10(len(self))) + 1
        else:
            n_places = 1
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

        if len(self) == 0:
            svrstr += "\n   [              None              ]"

        return svrstr

    def days(self):
        svr_days = defaultdict(list)
        for svr in self:
            svr_day = (svr['datetime'] - timedelta(hours=12)).replace(hour=12, minute=0, second=0, microsecond=0)
            svr_days[svr_day].append(svr)

        return OrderedDict((svr_day, type(self)(svr_days[svr_day])) for svr_day in sorted(svr_days.keys()))


class TornadoList(SVRList, unpacker=TornadoUnpacker):
    pass

class WindList(SVRList, unpacker=WindUnpacker):
    pass
