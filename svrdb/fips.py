
from .searchable import Searchable, SearchableItem

import os
import csv
from collections import defaultdict

class FIPS(Searchable):
    @classmethod
    def from_file(cls, fname):
        return cls.from_file_obj(open(fname, 'r'))

    @classmethod
    def from_file_obj(cls, fobj):
        class FIPSRow(dict, SearchableItem):
            pass

        def cleanup(row):
            row['county'] = " ".join(row['county'].split(" ")[:-1])
            row['state_fips'] = int(row['state_fips'])
            row['county_fips'] = int(row['county_fips'])
            del row['class']
            return row

        col_names = ['state', 'state_fips', 'county_fips', 'county', 'class']
        csvf = csv.DictReader(fobj, fieldnames=col_names)
        db = [ FIPSRow(**cleanup(row)) for row in csvf ]

        return cls(*db)

    def lookup_name(self, cty_name, state):
        return self.search(county=cty_name, state=state)[0]

    def lookup_fips(self, fips_code):
        st_fips, cty_fips = divmod(fips_code, 1000)
        #print(fips_code)
        return self.search(state_fips=st_fips, county_fips=cty_fips)[0]

fips_fname = os.path.join(os.path.dirname(__file__), 'data', 'us_cty_fips.txt')
fips = FIPS.from_file(fips_fname)

if __name__ == "__main__":
    print(fips.lookup_name('Cleveland', 'OK'))
    print(fips.lookup_fips(40027))
