
from tornado import TornadoFactory

import sys
from math import log10

class TornadoList(object):
    def __init__(self, *lst):
        self._tors = lst

    @classmethod
    def from_csv(cls, fname):
        return cls.from_fobj(open(fname))

    @classmethod
    def from_fobj(cls, fobj):
        return cls.from_txt(fobj.read())

    @classmethod
    def from_txt(cls, txt):
        lines = txt.split("\r\n")

        factory = TornadoFactory()
        tors = []

        for line in lines:
            if line == "":
                continue

            tors.extend(factory.consume(line))

        tors.extend(factory.flush())

        return cls(*tors)

    def search(self, **kwargs):
        new_tors = [tor for tor in self._tors if tor.matches(**kwargs)]
        return TornadoList(*new_tors)

    def list(self, stream=sys.stdout):
        n_places = int(log10(len(self._tors))) + 1
        num_str = "%%%dd" % n_places
        stream.write(" " * (n_places + 2))
        stream.write("---Time-(UTC)--- ")
        stream.write(" --States--")
        stream.write(" -Mag-")
        stream.write("\n")

        for idx, tor in enumerate(self._tors):
            stream.write(num_str % (idx + 1))
            stream.write(". ")
            stream.write(str(tor))
            stream.write("\n")


if __name__ == "__main__":
    tls = TornadoList.from_csv('/data/All_tornadoes.csv')

    ok_vio = tls.search(st='OK', mag=lambda m: m >= 5)
    ok_vio.list()
