
from datetime import datetime, timedelta

class Searchable(object):
    def __init__(self, *lst):
        self._lst = lst

    def search(self, **keys):
        new_searchable = [ item for item in self._lst if item.matches(**keys) ]
        return type(self)(*new_searchable)

    def __iter__(self):
        for item in self._lst:
            yield item

    def __len__(self):
        return len(self._lst)

    def __getitem__(self, key):
        try:
            item = self._lst[key]
        except TypeError:
            item = [ it[key] for it in self._lst ]
        return item

def _to_set(val):
    if isinstance(val, str):
        val = [val]

    try:
        sval = set(val)
    except TypeError:
        sval = set([val])
    return sval

class SearchableItem(object):
    def matches(self, **kwargs):
        is_match = True
        for attr, val in kwargs.items():
            this_val = self[attr]
            try:
                # Try for function-type items
                try:
                    for v in val:
                        is_match &= v(this_val)
                except TypeError:
                    is_match &= val(this_val)
            except TypeError:
                # Try for other-type items
                val = _to_set(val)
                this_val = _to_set(this_val)

                common = list(val & this_val)
                is_match &= (len(common) > 0)

            if not is_match:
                break

        return is_match


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
