"""Opt-in observation only; unset VIDEO_SAFE_SCALAR_DIR leaves Python untouched."""
import os
if os.environ.get('VIDEO_SAFE_SCALAR_DIR'):
    try:
        from safe_scalar_probe import install
        install()
    except Exception:
        # A diagnostic hook must never replace an original check's result.
        # Missing observations are not quality acceptance.
        pass
