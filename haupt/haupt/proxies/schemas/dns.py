from haupt import settings


def get_dns_config(dns_prefix=None, dns_backend=None, dns_cluster=None):
    dns_prefix = dns_prefix or settings.PROXIES_CONFIG.dns_prefix
    dns_backend = dns_backend or settings.PROXIES_CONFIG.dns_backend
    dns_cluster = dns_cluster or settings.PROXIES_CONFIG.dns_custom_cluster
    if not dns_prefix:
        dns_prefix = "{}.kube-system".format(dns_backend)
    return "{dns_prefix}.svc.{dns_cluster}".format(
        dns_prefix=dns_prefix, dns_cluster=dns_cluster
    )


def get_resolver():
    if settings.PROXIES_CONFIG.dns_use_resolver:
        dns_config = get_dns_config()
        return "resolver {} valid=5s;".format(dns_config)
    return ""
