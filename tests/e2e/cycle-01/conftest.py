"""Shared fixtures for cycle-01 e2e tests."""
import struct

import pytest


@pytest.fixture
def wav_silence():
    """Generate a minimal 1-second WAV file with silence."""
    return make_wav_silence(1.0)


def make_wav_silence(duration_s: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generate a minimal WAV file with silence.

    Available as a plain function for tests that need custom durations.
    """
    num_samples = int(sample_rate * duration_s)
    data_size = num_samples * 2  # 16-bit = 2 bytes per sample

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,        # chunk size
        1,         # PCM
        1,         # mono
        sample_rate,
        sample_rate * 2,  # byte rate
        2,         # block align
        16,        # bits per sample
        b"data",
        data_size,
    )
    return header + b"\x00" * data_size
