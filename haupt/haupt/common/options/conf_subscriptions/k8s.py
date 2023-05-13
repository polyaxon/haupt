from haupt.common import conf
from haupt.common.options.registry import k8s

conf.subscribe(k8s.K8sNamespace)
conf.subscribe(k8s.K8sInCluster)
