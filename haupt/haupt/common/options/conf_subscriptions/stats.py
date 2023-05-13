from haupt.common import conf
from haupt.common.options.registry import stats

conf.subscribe(stats.StatsDefaultPrefix)
