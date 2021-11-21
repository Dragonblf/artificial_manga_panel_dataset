import multiprocessing as mp
from tqdm import tqdm

POOL_PROCESSES = 8


def open_pool(func, iterable):
    elements = []
    with mp.Pool(processes=POOL_PROCESSES) as pool:
        for e in tqdm(pool.imap_unordered(func, iterable), total=len(iterable)):
            elements.append(e)
    return elements
