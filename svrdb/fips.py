
from searchable import Searchable, SearchableItem

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
        return self.search(state_fips=st_fips, county_fips=cty_fips)[0]

if __name__ == "__main__":
    f = FIPS.from_file("/data/geo/us_cty_fips.txt")
    print f.lookup_name('Cleveland', 'OK')
    print f.lookup_fips(40027)
