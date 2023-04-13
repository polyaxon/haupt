#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.core.validators import RegexValidator
from django.utils.regex_helper import _lazy_re_compile

try:
    from django.utils.safestring import mark_safe
except ImportError:
    raise ImportError("This module depends on django.")


from clipped.utils.strings import slugify as core_slugify


def slugify(value: str) -> str:
    return core_slugify(value, mark_safe)


slug_dots_re = _lazy_re_compile(r"^[-a-zA-Z0-9_.]+\Z")
validate_slug_with_dots = RegexValidator(
    slug_dots_re,
    # Translators: "letters" means latin letters: a-z and A-Z.
    "Enter a valid “value” consisting of letters, numbers, underscores, hyphens, or dots.",
    "invalid",
)
