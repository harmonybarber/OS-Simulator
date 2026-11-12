"""Deterministic FIFO/LRU page replacement."""
def simulate_memory(addresses, page_size=4096, frames=4, policy='FIFO'):
    if type(page_size) is not int or page_size < 1 or type(frames) is not int or frames < 1: raise ValueError('Page size and frames must be positive integers')
    if policy not in ('FIFO', 'LRU'): raise ValueError('Unknown policy')
    if not addresses or len(addresses) > 100000 or any(type(a) is not int or a < 0 for a in addresses): raise ValueError('Addresses must be nonnegative integers (1 to 100000 entries)')
    slots = [None] * frames; last = {}; inserted = {}; rows = []; hits = faults = evictions = 0
    for i, addr in enumerate(addresses):
        page = addr // page_size
        if page in slots: hits += 1; action = 'Hit'; victim = None
        else:
            faults += 1; action = 'Fault'; victim = None
            if None in slots: pos = slots.index(None)
            else:
                pos = min(range(frames), key=lambda j: (inserted[slots[j]] if policy == 'FIFO' else last[slots[j]], j))
                victim = slots[pos]; evictions += 1
            slots[pos] = page; inserted[page] = i
        last[page] = i
        rows.append({'step': i + 1, 'address': addr, 'page': page, 'action': action, 'victim': victim, 'frames': list(slots)})
    return {'references': len(addresses), 'hits': hits, 'faults': faults, 'evictions': evictions, 'trace': rows}
