import factory

from haupt.db.defs import Models


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("project-{}".format)

    class Meta:
        model = Models.Project
