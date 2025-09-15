from typing import Literal, Union
from numbers import Real
import math

Label = Literal["STANDARD", "SPECIAL", "REJECTED"]
Number = Union[int, float]

VOL_THRESH = 1_000_000  # cm^3
DIM_THRESH = 150        # cm
MASS_THRESH = 20        # kg

def _validate_dim(x: Number, name: str) -> Number:
   
    if isinstance(x, bool) or not isinstance(x, Real):
        raise TypeError(f"{name} must be a real number, got {type(x).__name__}")
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{name} must be finite (not NaN/∞)")
    if x < 0:
        raise ValueError(f"{name} must be non-negative")
    return x

def _validate_mass(x: Number) -> Number:
    # Same checks as dimensions; mass must also be non-negative.
    return _validate_dim(x, "mass")

def _volume_ge_threshold(w: Number, h: Number, l: Number) -> bool:
    
    dims = (w, h, l)

    int_like = []
    for d in dims:
        if isinstance(d, int):
            int_like.append(d)
        elif isinstance(d, float) and d.is_integer():
            int_like.append(int(d))
        else:
            int_like = None
            break

    if int_like is not None:
        w_i, h_i, l_i = int_like
        # Python ints are arbitrary precision; no overflow risk.
        return (w_i * h_i * l_i) >= VOL_THRESH

    # General case (floats allowed). Using >= follows problem spec exactly.
    return (w * h * l) >= VOL_THRESH

def sort(width: Number, height: Number, length: Number, mass: Number) -> Label:
   
    width  = _validate_dim(width,  "width")
    height = _validate_dim(height, "height")
    length = _validate_dim(length, "length")
    mass   = _validate_mass(mass)

    bulky = (
        _volume_ge_threshold(width, height, length)
        or width >= DIM_THRESH
        or height >= DIM_THRESH
        or length >= DIM_THRESH
    )
    heavy = mass >= MASS_THRESH

    # Required ternary operator use
    return "REJECTED" if (bulky and heavy) else ("SPECIAL" if (bulky or heavy) else "STANDARD")


if __name__ == "__main__":
    # Exhaustive sanity checks, including boundaries & pathologies

    # Standard
    assert sort(100, 100, 99, 19.9) == "STANDARD"
    assert sort(0, 0, 0, 0) == "STANDARD"

    # Bulky by volume boundary
    assert sort(100, 100, 100, 0) == "SPECIAL"  # 1,000,000 exactly

    # Bulky by dimension boundary
    assert sort(150, 1, 1, 0) == "SPECIAL"

    # Heavy boundary
    assert sort(1, 1, 1, 20) == "SPECIAL"

    # Both -> Rejected
    assert sort(150, 1, 1, 20) == "REJECTED"
    assert sort(200, 200, 1, 25) == "REJECTED"

    # Float inputs (integer-like)
    assert sort(150.0, 1.0, 1.0, 19.0) == "SPECIAL"
    assert sort(100.0, 100.0, 100.0, 0.0) == "SPECIAL"  # volume threshold

    # Float inputs (non-integer-like)
    assert sort(149.9999, 149.9999, 44.5, 19.9999) == "STANDARD"

    # Very large ints (no overflow)
    assert sort(1_000_000, 1_000_000, 1, 0) == "SPECIAL"

    # Error cases
    try:
        sort(-1, 1, 1, 1)
        raise AssertionError("Expected ValueError for negative dimension")
    except ValueError:
        pass

    try:
        sort(1, 1, 1, -0.1)
        raise AssertionError("Expected ValueError for negative mass")
    except ValueError:
        pass

    try:
        sort(True, 1, 1, 1)  # bools are not allowed even though bool is a subclass of int
        raise AssertionError("Expected TypeError for boolean dimension")
    except TypeError:
        pass

    try:
        sort(float("nan"), 1, 1, 1)
        raise AssertionError("Expected ValueError for NaN")
    except ValueError:
        pass

    try:
        sort(1, float("inf"), 1, 1)
        raise AssertionError("Expected ValueError for Infinity")
    except ValueError:
        pass

    print("All edge-case tests passed!")
