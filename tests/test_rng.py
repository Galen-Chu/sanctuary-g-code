"""RNG: determinism, bounds, and per-system independence."""

from __future__ import annotations

from sanctuary.noise import vnoise2
from sanctuary.rng import Stream, Streams

# Golden values produced by the ORIGINAL JavaScript implementation
# (Noniv/abyssal-garden source/src/math.js, seed 20261110) on 2026-11-16 —
# see scripts/verify_lineage.mjs. Any change that shifts one of these numbers
# breaks the cross-language lineage contract documented in docs/DESIGN.md §2.
_JS_DEFAULT_SEED = [
    0.47585524804890156, 0.4372278384398669, 0.7736968537792563, 0.2937412660103291,
    0.3471537437289953, 0.08541534398682415,
    0.16004084376618266, 0.04646476684138179, 0.9177373840939254, 0.4236405179835856,
    0.1357600896153599, 0.5899799983017147, 0.40731236594729125, 0.6738020302727818,
    0.7719425074756145, 0.43280978430993855, 0.22150923125445843, 0.19588565360754728,
    0.5040180119685829, 0.5636834793258458,
]
_JS_STREAM_3 = [
    0.8550673951394856, 0.7395435720682144, 0.8102351524867117, 0.45327418902888894,
    0.6892062439583242, 0.17674460890702903, 0.6920542125590146, 0.393347681267187,
    0.7309054913930595, 0.048540325136855245,
]
_JS_NOISE = [0.7835584939909279, 0.6300746457389663, 0.896215538688004, 0.6792962265173647, 0.0]


def test_js_lineage() -> None:
    """The port reproduces the original JS implementation number for number."""
    stream = Stream(20261110)
    assert [stream.f01() for _ in range(20)] == _JS_DEFAULT_SEED
    stream3 = Streams(20261110).stream(3)
    assert [stream3.f01() for _ in range(10)] == _JS_STREAM_3
    coords = ((0.3, 7.9), (-12.4, 3.1), (25.0, -8.2), (4.7, 4.7), (0.0, 0.0))
    assert [vnoise2(x, y) for x, y in coords] == _JS_NOISE


def test_same_seed_same_sequence() -> None:
    a = [Stream(42).f01() for _ in range(200)]
    b = [Stream(42).f01() for _ in range(200)]
    assert a == b


def test_different_seed_different_sequence() -> None:
    a = [Stream(1).f01() for _ in range(8)]
    b = [Stream(2).f01() for _ in range(8)]
    assert a != b


def test_bounds() -> None:
    s = Stream(7)
    for _ in range(1000):
        v = s.f01()
        assert 0.0 <= v < 1.0
        u = s.next_u32()
        assert 0 <= u < 2**32


def test_range() -> None:
    s = Stream(9)
    for _ in range(100):
        v = s.range(-2.0, 5.0)
        assert -2.0 <= v < 5.0


def test_streams_are_independent() -> None:
    """Two systems sharing a base seed draw from different streams."""
    streams = Streams(100)
    food = [streams.stream(2).f01() for _ in range(50)]
    water = [streams.stream(3).f01() for _ in range(50)]
    assert food != water


def test_stream_zero_equals_base() -> None:
    streams = Streams(1234)
    assert [streams.stream(0).f01() for _ in range(10)] == [Stream(1234).f01() for _ in range(10)]


def test_stream_isolation() -> None:
    """Interleaved draws on another stream never shift this stream's sequence."""
    solo_stream = Streams(77).stream(4)
    solo = [solo_stream.f01() for _ in range(10)]

    streams = Streams(77)
    shelter = streams.stream(4)
    other = streams.stream(2)
    interleaved = []
    for _ in range(10):
        other.f01()  # another system draws in between
        interleaved.append(shelter.f01())
    assert interleaved == solo
