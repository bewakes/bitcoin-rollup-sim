from typing import List


def chunk_list(lst: List, size: int):
    chunks = []
    tmp = []
    for i, x in enumerate(lst):
        tmp.append(x)
        if (i+1) % size == 0:
            chunks.append(tmp)
            tmp = []
    if tmp:
        chunks.append(tmp)
    return chunks
