from haupt.db.abstracts.bookmarks import BaseBookmark


class Bookmark(BaseBookmark):
    class Meta(BaseBookmark.Meta):
        app_label = "db"
        db_table = "db_bookmark"
