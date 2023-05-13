from typing import Tuple

from clipped.manager_interface import ManagerInterface

from haupt.common.options.option import Option


class OptionManager(ManagerInterface):
    def _get_state_data(  # pylint:disable=arguments-differ
        self, option: Option
    ) -> Tuple[str, Option]:
        return option.key, option

    def subscribe(self, option: Option):  # pylint:disable=arguments-differ
        """
        >>> subscribe(SomeOption)
        """
        super().subscribe(obj=option)

    def get(self, key: str) -> Option:  # pylint:disable=arguments-differ
        return super().get(key=key)
