def get_if_exists(queryset, **kwargs):
    """Get a single object from the queryset, or None if it doesn't exist.

    Unlike .filter().first(), this uses .get() which:
    - Avoids unnecessary ORDER BY
    - Works with caching frameworks
    - Raises MultipleObjectsReturned on data integrity issues
    """
    try:
        return queryset.get(**kwargs)
    except queryset.model.DoesNotExist:
        return None
