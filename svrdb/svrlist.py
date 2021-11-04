
from .parsers import TornadoUnpacker, WindUnpacker, HailUnpacker
from .searchable import Searchable
from .fips import fips
from .plotters import plot_tornadoes, plot_wind, plot_hail

import pandas as pd

import sys
import os
from math import log10
from datetime import datetime, timedelta
from collections import defaultdict
from io import StringIO

class SVRList(Searchable):
    @classmethod
    def load_db(cls):
        fname = os.path.join(os.path.dirname(__file__), 'data', cls.db_fname)
        return cls.from_csv(fname)

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

    def __init_subclass__(cls, unpacker, plotter, db_fname):
        super().__init_subclass__()
        cls.unpacker = unpacker
        cls.plotter = plotter
        cls.db_fname = db_fname

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

    def _repr_html_(self):
        css = """
        .svrlist {
            font-size: 14px !important;
        }
        .svrlist td, th {
            text-align: center !important;
        }
        .svrlist tr:nth-child(odd) {
            background: #bbbbbb !important;
        }
        .svrlist tr:nth-child(even) {
            background: #dddddd !important;
        }
        .svrlist td {
            padding: 2px;
        }
        """

        html_str = '<style>%s</style><table class="svrlist">' % css
        html_str += '<tr><th>&nbsp;</th><th>Date/Time (UTC)</th><th>Magnitude</th></tr>'
        for idx, svr in enumerate(self):
            html_str += '<tr>'
            html_str += '<td>%d.</td>' % (idx + 1)
            html_str += svr._repr_html_(_make_table=False)
            html_str += '</tr>'

        return html_str + '</table>'

    def search(self, **keys):
        def extract_fips(fips_dct):
            return fips_dct['state_fips'] * 1000 + fips_dct['county_fips']

        if 'county' in keys:
            ctys = keys.pop('county')
            if type(ctys) == tuple:
                cty_fips = extract_fips(fips.lookup_name(*ctys))
            else:
                cty_fips = [extract_fips(fips.lookup_name(*cty)) for cty in ctys]

            keys['cty_fips'] = cty_fips
        return super().search(**keys)

    def groupby(self, group):
        if '.' in group:
            group, attr = group.split('.', 1)
        else:
            attr = None

        keys = [svr[group] for svr in self]

        if attr is not None:
            keys = [getattr(key, attr) for key in keys]

        groups = defaultdict(list)
        for key, svr in zip(keys, self):
            groups[key].append(svr)

        return dict((key, type(self)(*grp)) for key, grp in groups.items())

    def days(self):
        svr_days = defaultdict(list)
        for svr in self:
            svr_day = (svr['datetime'] - timedelta(hours=12)).replace(hour=12, minute=0, second=0, microsecond=0)
            svr_days[svr_day].append(svr)

        return dict((svr_day, type(self)(*svr_days[svr_day])) for svr_day in sorted(svr_days.keys()))

    def plot(self, label=None, filename=None):
        type(self).plotter(self, label=label, filename=filename)


class TornadoList(SVRList, unpacker=TornadoUnpacker, 
                           plotter=plot_tornadoes,
                           db_fname='1950-2019_all_tornadoes.csv'):
    pass


class WindList(SVRList, unpacker=WindUnpacker, 
                        plotter=plot_wind,
                        db_fname='1955-2019_wind.csv'):
    pass


class HailList(SVRList, unpacker=HailUnpacker, 
                        plotter=plot_hail,
                        db_fname='1955-2019_hail.csv'):
    pass
