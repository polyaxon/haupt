from typing import Any, Dict, Optional

from haupt.common.options.option import Option


class BaseConfHandler:
    def get(self, option: Option, owners: Optional[Dict[str, int]] = None) -> Any:
        raise NotImplementedError

    def set(self, option: Option, value: Any, owners: Optional[Dict[str, int]] = None):
        raise NotImplementedError

    def delete(self, option: Option, owners: Optional[Dict[str, int]] = None) -> Any:
        raise NotImplementedError
