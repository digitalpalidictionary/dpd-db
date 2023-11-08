from typing import List

def list_into_batches(input_list: List, num_batches: int) -> List[List]:
    """Splits a list into a number of lists.

    When the division has remainder, this results in num + 1 batches, where the
    last batch has a small number of items, i.e. the remainder of the integer
    division.
    """

    batch_size = len(input_list) // num_batches
    return [input_list[i:i + batch_size] for i in range(0, len(input_list), batch_size)]
