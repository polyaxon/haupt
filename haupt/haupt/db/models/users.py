from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        app_label = "db"
        db_table = "db_user"
        swappable = "AUTH_USER_MODEL"
