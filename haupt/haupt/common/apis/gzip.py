from functools import wraps

from django.utils.text import compress_string

from haupt.polyconf.config_manager import PLATFORM_CONFIG


class GzipDecorator:
    """Gzip the response and set the respective header."""

    def __call__(self, func):
        @wraps(func)
        def inner(self, request, *args, **kwargs):
            response = func(self, request, *args, **kwargs)

            if (
                PLATFORM_CONFIG
                and PLATFORM_CONFIG.is_debug_mode
                and PLATFORM_CONFIG.is_monolith_service
                and not PLATFORM_CONFIG.is_test_env
            ):
                return response

            # Before we can access response.content, the response needs to be rendered.
            response = self.finalize_response(request, response, *args, **kwargs)
            response.render()  # should be rendered, before picklining while storing to cache

            compressed_content = compress_string(response.content)

            # Ensure that the compressed content is actually smaller than the original.
            if len(compressed_content) >= len(response.content):
                return response

            # Replace content with gzipped variant, update respective headers.
            response.content = compressed_content
            response["Content-Length"] = str(len(response.content))
            response["Content-Encoding"] = "gzip"

            return response

        return inner


gzip = GzipDecorator
