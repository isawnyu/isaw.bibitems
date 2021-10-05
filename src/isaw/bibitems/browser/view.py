try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from Products.Five.browser import BrowserView


class BibItemView(BrowserView):

    @staticmethod
    def url_domain(url):
        host = urlparse(url).hostname
        parts = host.split('.')
        domain = []

        for part in reversed(parts):
            if part in ('www', 'api'):
                continue
            domain.insert(0, part)
            if len(domain) >= 2 and len(part) > 3:
                break

        return '.'.join(domain)
