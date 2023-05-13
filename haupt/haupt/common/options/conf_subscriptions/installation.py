from haupt.common import conf
from haupt.common.options.registry import installation

conf.subscribe(installation.PlatformEnvironmentVersion)
conf.subscribe(installation.PlatformVersion)
conf.subscribe(installation.PlatformDist)
conf.subscribe(installation.PlatformHost)
conf.subscribe(installation.ChartVersion)
conf.subscribe(installation.OrganizationKey)
