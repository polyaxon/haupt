from haupt import settings


def _get_indent(indent):
    return (
        settings.PROXIES_CONFIG.nginx_indent_char
        * settings.PROXIES_CONFIG.nginx_indent_width
        * indent
    )


def get_config(options, indent=0, **kwargs):
    _options = options.format(**kwargs)
    config = []
    for p in _options.split("\n"):
        config.append("{}{}".format(_get_indent(indent), p))

    return clean_config(config)


def clean_config(config):
    return "\n".join(config).replace("    \n", "")
