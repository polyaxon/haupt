import factory

from haupt.db.defs import Models
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from polyaxon.schemas import ManagedBy


class RunFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    original = None
    pipeline = None
    managed_by = ManagedBy.USER

    class Meta:
        model = Models.Run
