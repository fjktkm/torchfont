from pathlib import Path

import tomli
import tomli_w

path = Path("pyproject.toml")
data = tomli.loads(path.read_text(encoding="utf-8"))
data["tool"]["uv"]["sources"]["torch"] = [{"index": "pytorch-cpu"}]
path.write_bytes(tomli_w.dumps(data).encode("utf-8"))
