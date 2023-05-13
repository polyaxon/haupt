from haupt.common.options.option import Option, OptionScope, OptionStores

POLYAXON_ENVIRONMENT = "POLYAXON_ENVIRONMENT"
PLATFORM_VERSION = "PLATFORM_VERSION"
PLATFORM_DIST = "PLATFORM_DIST"
PLATFORM_HOST = "PLATFORM_HOST"
CHART_VERSION = "CHART_VERSION"
ORGANIZATION_KEY = "POLYAXON_ORGANIZATION_KEY"

OPTIONS = {
    POLYAXON_ENVIRONMENT,
    PLATFORM_VERSION,
    PLATFORM_DIST,
    PLATFORM_HOST,
    CHART_VERSION,
    ORGANIZATION_KEY,
}


class PlatformEnvironmentVersion(Option):
    key = POLYAXON_ENVIRONMENT
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.SETTINGS
    default = None
    options = None


class PlatformVersion(Option):
    key = PLATFORM_VERSION
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.SETTINGS
    default = None
    options = None


class PlatformDist(Option):
    key = PLATFORM_DIST
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.SETTINGS
    default = None
    options = None


class PlatformHost(Option):
    key = PLATFORM_HOST
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = None
    options = None


class ChartVersion(Option):
    key = CHART_VERSION
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.SETTINGS
    default = None
    options = None


class OrganizationKey(Option):
    key = ORGANIZATION_KEY
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.ENV
    default = None
    options = None
