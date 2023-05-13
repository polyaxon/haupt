from clipped.utils.enums import PEnum


class ContentTypes(str, PEnum):
    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"
    PROJECT = "project"
    RUN = "run"
