#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.options import option_namespaces, option_subjects
from haupt.common.options.option import Option, OptionScope, OptionStores

# Global Async Countdown
SCHEDULER_GLOBAL_COUNTDOWN = "{}_{}".format(
    option_namespaces.SCHEDULER,
    option_subjects.GLOBAL_COUNTDOWN,
)

OPTIONS = {
    SCHEDULER_GLOBAL_COUNTDOWN,
}


class SchedulerCountdown(Option):
    key = SCHEDULER_GLOBAL_COUNTDOWN
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "int"
    store = OptionStores.SETTINGS
    default = 1
    options = None
    description = "Global count down for scheduler"
