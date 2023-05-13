from haupt.common import conf
from haupt.common.options.registry import core

conf.subscribe(core.Logging)
conf.subscribe(core.Debug)
conf.subscribe(core.Protocol)
conf.subscribe(core.CeleryBrokerBackend)
conf.subscribe(core.CeleryBrokerUrl)
conf.subscribe(core.SecretInternalToken)
conf.subscribe(core.HealthCheckWorkerTimeout)
conf.subscribe(core.SchedulerEnabled)
conf.subscribe(core.UiAdminEnabled)
conf.subscribe(core.UiAssetsVersion)
conf.subscribe(core.UiBaseUrl)
conf.subscribe(core.UiOffline)
conf.subscribe(core.UiEnabled)
conf.subscribe(core.UiInSandbox)
