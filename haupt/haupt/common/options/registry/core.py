from haupt.common.options.option import Option, OptionScope, OptionStores

LOGGING = "LOGGING"
DEBUG = "DEBUG"
PROTOCOL = "PROTOCOL"
CELERY_BROKER_BACKEND = "CELERY_BROKER_BACKEND"
CELERY_BROKER_URL = "CELERY_BROKER_URL"
SECRET_INTERNAL_TOKEN = "SECRET_INTERNAL_TOKEN"  # noqa
HEALTH_CHECK_WORKER_TIMEOUT = "HEALTH_CHECK_WORKER_TIMEOUT"
SCHEDULER_ENABLED = "SCHEDULER_ENABLED"
UI_ADMIN_ENABLED = "UI_ADMIN_ENABLED"
UI_ASSETS_VERSION = "UI_ASSETS_VERSION"
UI_BASE_URL = "UI_BASE_URL"
UI_OFFLINE = "UI_OFFLINE"
UI_ENABLED = "UI_ENABLED"
UI_IN_SANDBOX = "UI_IN_SANDBOX"

OPTIONS = {
    LOGGING,
    DEBUG,
    PROTOCOL,
    CELERY_BROKER_BACKEND,
    CELERY_BROKER_URL,
    SECRET_INTERNAL_TOKEN,
    HEALTH_CHECK_WORKER_TIMEOUT,
    SCHEDULER_ENABLED,
    UI_ADMIN_ENABLED,
    UI_ASSETS_VERSION,
    UI_BASE_URL,
    UI_OFFLINE,
    UI_ENABLED,
    UI_IN_SANDBOX,
}


class Logging(Option):
    key = LOGGING
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "dict"
    default = None
    options = None


class Debug(Option):
    key = DEBUG
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "dict"
    default = None
    options = None


class Protocol(Option):
    key = PROTOCOL
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = None
    options = None


class CeleryBrokerBackend(Option):
    key = CELERY_BROKER_BACKEND
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = None
    options = None


class CeleryBrokerUrl(Option):
    key = CELERY_BROKER_URL
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = None
    options = None


class SecretInternalToken(Option):
    key = SECRET_INTERNAL_TOKEN
    scope = OptionScope.GLOBAL
    is_secret = True
    is_optional = False
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = None
    options = None


class HealthCheckWorkerTimeout(Option):
    key = HEALTH_CHECK_WORKER_TIMEOUT
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "int"
    default = 4
    options = None


class SchedulerEnabled(Option):
    key = SCHEDULER_ENABLED
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "bool"
    default = True
    options = None


class UiAdminEnabled(Option):
    key = UI_ADMIN_ENABLED
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "bool"
    default = True
    options = None


class UiAssetsVersion(Option):
    key = UI_ASSETS_VERSION
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = ""
    options = None


class UiBaseUrl(Option):
    key = UI_BASE_URL
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "str"
    default = "/"
    options = None


class UiOffline(Option):
    key = UI_OFFLINE
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "bool"
    default = False
    options = None


class UiEnabled(Option):
    key = UI_ENABLED
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "bool"
    default = False
    options = None


class UiInSandbox(Option):
    key = UI_IN_SANDBOX
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.SETTINGS
    typing = "bool"
    default = False
    options = None
