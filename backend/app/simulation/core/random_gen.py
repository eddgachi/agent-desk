import random


class SeededRNG:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def randint(self, a: int, b: int) -> int:
        return self.rng.randint(a, b)

    def random(self) -> float:
        return self.rng.random()

    def choice(self, seq):
        return self.rng.choice(seq)

    def shuffle(self, seq):
        return self.rng.shuffle(seq)


# Factory to create RNG per simulation
_rng_store = {}


def get_rng(sim_id: str, seed: int) -> SeededRNG:
    if sim_id not in _rng_store:
        _rng_store[sim_id] = SeededRNG(seed)
    return _rng_store[sim_id]


def clear_rng(sim_id: str):
    if sim_id in _rng_store:
        del _rng_store[sim_id]
