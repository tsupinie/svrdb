
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
