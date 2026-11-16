"""RNG: determinism, bounds, and per-system independence."""

from __future__ import annotations

from sanctuary.rng import Stream, Streams


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
