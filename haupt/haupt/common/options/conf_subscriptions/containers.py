from haupt.common import conf
from haupt.common.options.registry import containers

conf.subscribe(containers.PolyaxonInitContainer)
conf.subscribe(containers.PolyaxonSidecarContainer)
