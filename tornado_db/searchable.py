
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
                if isinstance(val, str):
                    val = [val]

                try:
                    sval = set(val)
                except TypeError:
                    sval = set([val])

                common = list(sval & set(this_val))
                is_match &= (len(common) > 0)

            if not is_match:
                break

        return is_match
