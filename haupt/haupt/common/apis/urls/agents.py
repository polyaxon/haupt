from haupt.common.apis.regex import OWNER_NAME_PATTERN, RUN_UUID_PATTERN

URLS_CATALOGS_AGENTS_STATE = r"^orgs/{}/agents/state/?$".format(OWNER_NAME_PATTERN)
URLS_CATALOGS_AGENTS_CRON = r"^orgs/{}/agents/cron/?$".format(OWNER_NAME_PATTERN)
URLS_ORGANIZATIONS_RUNS_DETAILS = r"^orgs/{}/runs/{}/?$".format(
    OWNER_NAME_PATTERN, RUN_UUID_PATTERN
)
