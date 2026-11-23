from pathlib import Path

import pytest

from morph_studio.stitcher import build_join_command


def test_guard_requires_verified_endpoints():
    with pytest.raises(ValueError):
        build_join_command([Path("a.mp4"), Path("b.mp4")],
                           Path("out.mp4"), fps=16,
                           verified_matching_endpoints=False)


def test_ffmpeg_drops_one_duplicate_start_frame_only():
    args = build_join_command([Path("a.mp4"), Path("b.mp4")],
                              Path("out.mp4"), fps=16,
                              verified_matching_endpoints=True)
    flt = args[args.index("-filter_complex") + 1]
    assert "[0:v]setpts=PTS-STARTPTS[v0]" in flt
    assert "[1:v]trim=start_frame=1,setpts=PTS-STARTPTS[v1]" in flt
    assert "concat=n=2:v=1:a=0[v]" in flt
    assert "-an" in args

def test_default_join_never_overwrites_existing_file():
    args = build_join_command([Path("a.mp4"), Path("b.mp4")],
                              Path("out.mp4"), fps=16,
                              verified_matching_endpoints=True)
    assert "-n" in args and "-y" not in args
    forced = build_join_command([Path("a.mp4"), Path("b.mp4")],
                                Path("out.mp4"), fps=16,
                                verified_matching_endpoints=True,
                                overwrite=True)
    assert "-y" in forced
