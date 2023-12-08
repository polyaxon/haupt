from haupt.common import conf
from haupt.common.options.registry import installation

conf.subscribe(installation.PlatformEnvironmentVersion)
conf.subscribe(installation.PlatformVersion)
conf.subscribe(installation.PlatformDist)
conf.subscribe(installation.PlatformMode)
conf.subscribe(installation.PlatformHost)
conf.subscribe(installation.ChartVersion)
conf.subscribe(installation.OrganizationId)
conf.subscribe(installation.OrganizationName)
conf.subscribe(installation.OrganizationPlan)
conf.subscribe(installation.OrganizationLicense)
conf.subscribe(installation.OrganizationHmac)
conf.subscribe(installation.OrganizationKey)
