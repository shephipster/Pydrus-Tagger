import itertools


def mistakenTagSearcher(tags:list):
    search_set = []
    for p in itertools.product([True, False], repeat=len(tags)):
        search_term = []
        params = list(zip(tags, p))
        for entry in params:
            if entry[1] and len(entry[0].split('_') ) == 2:
                spl = entry[0].split('_')
                spl = spl[1] + '_' + spl[0]
                search_term.append(spl)
            else:
                search_term.append(entry[0])
        search_set = sorted(search_set)
        if search_term not in search_set:
            search_set.append(search_term)
            
    return search_set