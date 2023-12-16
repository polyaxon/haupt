from haupt.common.options.option import Option, OptionScope, OptionStores

POLYAXON_ENVIRONMENT = "POLYAXON_ENVIRONMENT"
PLATFORM_VERSION = "PLATFORM_VERSION"
PLATFORM_DIST = "PLATFORM_DIST"
PLATFORM_MODE = "PLATFORM_MODE"
PLATFORM_HOST = "PLATFORM_HOST"
CHART_VERSION = "CHART_VERSION"
ORGANIZATION_ID = "POLYAXON_ORGANIZATION_ID"
ORGANIZATION_NAME = "POLYAXON_ORGANIZATION_NAME"
ORGANIZATION_PLAN = "POLYAXON_ORGANIZATION_PLAN"
ORGANIZATION_LICENSE = "POLYAXON_ORGANIZATION_LICENSE"
ORGANIZATION_HMAC = "POLYAXON_ORGANIZATION_HMAC"
ORGANIZATION_KEY = "POLYAXON_ORGANIZATION_KEY"

OPTIONS = {
    POLYAXON_ENVIRONMENT,
    PLATFORM_VERSION,
    PLATFORM_DIST,
    PLATFORM_MODE,
    PLATFORM_HOST,
    CHART_VERSION,
    ORGANIZATION_ID,
    ORGANIZATION_NAME,
    ORGANIZATION_PLAN,
    ORGANIZATION_LICENSE,
    ORGANIZATION_HMAC,
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


class PlatformMode(Option):
    key = PLATFORM_MODE
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


class OrganizationId(Option):
    key = ORGANIZATION_ID
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.ENV
    default = None
    options = None


class OrganizationName(Option):
    key = ORGANIZATION_NAME
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.ENV
    default = None
    options = None


class OrganizationPlan(Option):
    key = ORGANIZATION_PLAN
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "dict"
    store = OptionStores.ENV
    default = None
    options = None


class OrganizationLicense(Option):
    key = ORGANIZATION_LICENSE
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.ENV
    default = None
    options = None


class OrganizationHmac(Option):
    key = ORGANIZATION_HMAC
    scope = OptionScope.GLOBAL
    is_secret = True
    is_optional = True
    is_list = False
    typing = "str"
    store = OptionStores.ENV
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
