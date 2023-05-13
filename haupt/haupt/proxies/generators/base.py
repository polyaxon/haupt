from typing import Optional


def write_to_conf_file(
    name: str, content: str, path: Optional[str] = None, ext: str = "conf"
):
    with open("{}/{}.{}".format(path or ".", name, ext), "w") as f:
        f.write(content)
