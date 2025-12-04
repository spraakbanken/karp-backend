from itertools import groupby, repeat
from typing import Iterable, Iterator


def batch_items(items: Iterable, max_batch_size=None) -> Iterator[list]:
    """
    Split a sequence of items up into batches.

    The batches start off very small and increase in size, so that if you just
    want the first few results you don't need to wait for a big batch.
    """

    # Idea: pair each item up with a batch number, then use groupby
    # on the batch numbers

    def batch_numbers():
        # yields 1, 2, 2, 3, 3, 3, 3, ...

        i = 1  # batch number
        n = 1  # number of items in this batch

        while True:
            yield from repeat(i, n)

            i += 1
            n *= 2
            if max_batch_size is not None:
                n = min(n, max_batch_size)

    for _, group in groupby(zip(batch_numbers(), items), key=lambda pair: pair[0]):
        yield [item for _, item in group]
