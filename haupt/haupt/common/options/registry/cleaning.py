from haupt.common.options import option_namespaces, option_subjects
from haupt.common.options.option import Option, OptionScope, OptionStores

CLEANING_INTERVALS_ACTIVITY_LOGS = "{}_{}".format(
    option_namespaces.CLEANING_INTERVALS,
    option_subjects.ACTIVITY_LOGS,
)
CLEANING_INTERVALS_NOTIFICATIONS = "{}_{}".format(
    option_namespaces.CLEANING_INTERVALS,
    option_subjects.NOTIFICATIONS,
)
CLEANING_INTERVALS_ARCHIVES = "{}_{}".format(
    option_namespaces.CLEANING_INTERVALS,
    option_subjects.ARCHIVES,
)
CLEANING_INTERVALS_DELETION = "{}_{}".format(
    option_namespaces.CLEANING_INTERVALS, option_subjects.DELETION
)


OPTIONS = {
    CLEANING_INTERVALS_ACTIVITY_LOGS,
    CLEANING_INTERVALS_NOTIFICATIONS,
    CLEANING_INTERVALS_ARCHIVES,
    CLEANING_INTERVALS_DELETION,
}


class CleaningIntervalsOption(Option):
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "int"
    store = OptionStores.SETTINGS
    options = None


class CleaningIntervalsActivityLogs(CleaningIntervalsOption):
    key = CLEANING_INTERVALS_ACTIVITY_LOGS
    default = 15
    description = "A cleaning interval for activity logs in days"


class CleaningIntervalsNotifications(CleaningIntervalsOption):
    key = CLEANING_INTERVALS_NOTIFICATIONS
    default = 30
    description = "A cleaning interval for notifications in days"


class CleaningIntervalsArchives(CleaningIntervalsOption):
    key = CLEANING_INTERVALS_ARCHIVES
    default = 30
    description = "A cleaning interval for archives in days"


class CleaningIntervalsDeletion(CleaningIntervalsOption):
    key = CLEANING_INTERVALS_DELETION
    default = 15
    description = "A cleaning interval for archives in days"
