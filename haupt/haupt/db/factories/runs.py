import factory

from haupt.db.abstracts.getter import get_run_model
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory


class RunFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    original = None
    pipeline = None
    is_managed = False

    class Meta:
        model = get_run_model()
