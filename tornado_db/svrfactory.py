
from .tornado import TornadoSegment, Tornado

from collections import defaultdict

class SVRFactory(object):
    def __init__(self, cols):
        self._cols = cols

    def consume(self):
        raise NotImplementedError("Implement consume() in a subclass!")

    def flush(self):
        raise NotImplementedError("Implement flush() in a subclass!")


class TornadoFactory(SVRFactory):
    def __init__(self, cols):
        super(TornadoFactory, self).__init__(cols)

        self._year = None
        self._segments = defaultdict(list)

    def consume(self, line):
        results = []

        line_dict = dict((c, TornadoSegment.parsers[c](v)) for c, v in zip(self._cols, line.split(',')))
        seg = TornadoSegment(**line_dict)
        om = seg['om']
        yr = seg['datetime'].year

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

