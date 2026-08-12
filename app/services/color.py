import random


def random_color() -> str:
    """Generate a random hex color code, e.g. '#FF5733'."""
    return f"#{random.randint(0, 0xFFFFFF):06X}"
