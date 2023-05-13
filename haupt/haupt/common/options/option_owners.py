import uuid

from collections import namedtuple
from typing import Optional


class OptionOwners(namedtuple("OptionOwners", "user project team organization")):
    @classmethod
    def get_owners(
        cls,
        user: Optional[int] = None,
        project: Optional[int] = None,
        team: Optional[int] = None,
        organization: Optional[int] = None,
    ) -> "OptionOwners":
        return cls(user=user, project=project, team=team, organization=organization)

    def to_dict(self):
        return dict(self._asdict())

    def __eq__(self, other):
        return (
            self.user == other.user
            and self.project == other.project
            and self.team == other.team
            and self.organization == other.organization
        )

    def __str__(self):
        return uuid.uuid5(
            namespace=uuid.NAMESPACE_DNS,
            name=f"user<{self.user}>:"
            f"project<{self.project}>:"
            f"team<{self.team}>:"
            f"organization<{self.organization}>",
        ).hex
