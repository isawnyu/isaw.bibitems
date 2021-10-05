import requests
from pyzotero import zotero
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from zope.interface import implementer
from . import logger
from .interfaces import IBibliographicURLIFetcher


@implementer(IBibliographicURLIFetcher)
class ZoteroWebParser(object):
    library_id = None
    library_type = None
    item_id = None

    def fetch(self, uri):
        o = urlparse(uri)
        if o.hostname != 'www.zotero.org':
            return {u"error": u"Only URIs in the www.zotero.org domain can be fetched."}

        user_agent = 'ISAWBibItems/(+https://github.com/isawnyu/isaw.bibitems)'
        self.request_headers = {
            'user-agent': user_agent,
            'cache-control': 'no-cache'
        }

        try:
            response = requests.get(uri, headers=self.request_headers)
        except requests.exceptions.RequestException:
            logger.exception('Error fetching Zotero web page: {}'.format(uri))
            return {u"error": u"Could not fetch web page {}.".format(uri)}
        if response.status_code >= 400:
            return {u"error": u"Could not fetch web page {} (HTTP Error {}).".format(uri, response.status_code)}

        zuri = response.url
        if zuri != uri:
            # a redirect has occurred
            o = urlparse(zuri)

        path_parts = o.path.split('/')
        if path_parts[1] == 'groups':
            self.library_type = 'group'
            self.library_id = path_parts[2]
        else:
            self.library_type = 'user'
            self.library_id = path_parts[1]

        if 'items' in path_parts:
            self.item_id = path_parts[path_parts.index('items') + 1]
        else:
            return {u"error": u"Could not parse Zotero item id from URI {}".format(zuri)}

        data = self._zotero_api_result()
        result = {}
        if data.get('data'):
            info = data['data']
            result[u'short_title'] = info['shortTitle']
            result[u'title'] = info['title']
            result[u'formatted_citation'] = data['formatted']
            result[u'access_uri'] = info['url']
            result[u'bibliographic_uri'] = data['links']['alternate']['href']
            authors = result[u'authors'] = []
            editors = result[u'editors'] = []
            contributors = result[u'contributors'] = []
            for item in info.get('creators', []):
                if 'lastName' in item:
                    name = {'lastName': item['lastName'],
                            'firstName': item['firstName']}
                elif 'name' in item:
                    name = {'name': item.get('name')}

                if item['creatorType'] == 'author':
                    authors.append(name)
                elif item['creatorType'] == 'editor':
                    editors.append(name)
                elif item['creatorType'] == 'contributor':
                    contributors.append(name)

            result[u'publisher'] = info.get(u'publisher')
            result[u'isbn'] = info.get(u'ISBN')
            result[u'issn'] = info.get(u'ISSN')
            result[u'doi'] = info.get(u'DOI')
            result[u'date_of_publication'] = info.get(u'date')
            result[u'text'] = info.get('abstractNote')
            result[u'parent_title'] = (
                info.get('blogTitle') or info.get('bookTitle') or
                info.get('dictionaryTitle') or info.get('encyclopediaTitle') or
                info.get('forumTitle') or info.get('proceedingsTitle') or
                info.get('publicationTitle') or info.get('websiteTitle')
            )
            result[u'volume'] = info.get('volume')
            result[u'range'] = info.get('pages')

        if isinstance(result.get(u'formatted_citation'), list):
            result[u'formatted_citation'] = result[u'formatted_citation'][0]

        return result

    def _zotero_api_result(self):
        api = zotero.Zotero(self.library_id, self.library_type)
        results = api.item(self.item_id, format='json')
        formatted = api.item(self.item_id, content='bib')
        results['formatted'] = formatted

        return results
