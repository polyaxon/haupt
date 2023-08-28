import factory

from haupt.db.defs import Models


class ProjectFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("project-{}".format)

    class Meta:
        model = Models.Project


class ProjectVersionFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence("artifact-version-{}".format)

    class Meta:
        model = Models.ProjectVersion
