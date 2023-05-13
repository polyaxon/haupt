import factory

from haupt.db.abstracts.getter import get_project_model


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("project-{}".format)

    class Meta:
        model = get_project_model()
