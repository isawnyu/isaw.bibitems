from json import dumps
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from zope.component import queryUtility
from zExceptions import BadRequest
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from ..interfaces import IBibliographicURLIFetcher


class JSONBiblographyDataFetcher(BrowserView):
    data = None

    def update(self):
        url = self.request.get('url')
        if not url:
            raise BadRequest('Missing request parameter "uri"')

        transforms = getToolByName(self.context, 'portal_transforms')
        hostname = urlparse(url).hostname
        fetcher = queryUtility(IBibliographicURLIFetcher, name=hostname)
        if fetcher is None:
            self.data = {
                u"error": "Could not find biblographic fetcher for {}".format(
                    hostname
                ),
            }
            return

        self.data = fetcher.fetch(url)
        if self.data.get(u'formatted_citation'):
            self.data[u'plain'] = transforms.convertTo(
                'text/plain', self.data['formatted_citation'],
                mimetype='text/html'
            ).getData().strip()
        else:
            self.data[u'plain'] = u''

    def __call__(self):
        self.update()
        res = self.request.response
        if u"error" in self.data:
            res.setStatus(500)
        if not self.data:
            self.data[u"error"] = u"Record not found"
            res.setStatus(404)

        res.setHeader('Content-Type', 'application/json; encoding=utf-8')
        return dumps(self.data)
