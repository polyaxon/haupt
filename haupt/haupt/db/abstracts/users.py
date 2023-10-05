from django.contrib.auth.models import AbstractUser


class BaseUser(AbstractUser):
    class Meta(AbstractUser.Meta):
        abstract = True
        app_label = "db"
        db_table = "db_user"
        swappable = "AUTH_USER_MODEL"
