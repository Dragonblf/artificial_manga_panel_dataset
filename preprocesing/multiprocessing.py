import multiprocessing as mp
from tqdm import tqdm


def open_pool(func, iterable):
    elements = []
    with mp.Pool(processes=8) as pool:
        for e in tqdm(pool.imap_unordered(func, iterable), total=len(iterable)):
            elements.append(e)
    return elements
