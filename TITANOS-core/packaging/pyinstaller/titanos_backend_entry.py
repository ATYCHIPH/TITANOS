from __future__ import annotations

import os

os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

from titanos.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
