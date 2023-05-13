from haupt.common.options.option import Option, OptionScope, OptionStores

K8S_NAMESPACE = "K8S_NAMESPACE"
K8S_IN_CLUSTER = "K8S_IN_CLUSTER"

OPTIONS = {K8S_NAMESPACE, K8S_IN_CLUSTER}


class K8sNamespace(Option):
    key = K8S_NAMESPACE
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    typing = "str"
    store = OptionStores.SETTINGS
    default = None
    options = None


class K8sInCluster(Option):
    key = K8S_IN_CLUSTER
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    typing = "bool"
    store = OptionStores.SETTINGS
    default = None
    options = None
