import factory

from haupt.db.defs import Models
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory


class RunFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    original = None
    pipeline = None
    is_managed = False

    class Meta:
        model = Models.Run
