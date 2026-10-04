"""Platform generators. One module per platform: tools/generators/<platform>.py.

Each exposes `generate(design: Design, out_dir: Path) -> list[Path]`, writes that platform's files,
and returns the paths written. Output must be deterministic. `build_sheet` is shared.
"""
