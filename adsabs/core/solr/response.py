'''
Created on Sep 19, 2012

@author: jluker
'''

import logging
from simplejson import loads,dumps
from config import config

from .solrdoc import SolrDocument, SolrFacets

log = logging.getLogger(__name__)

class SolrResponse(object):
    
    def __init__(self, raw, request=None):
        self.raw = raw
        self.request = request
        
    def search_response(self):
        resp = {
            'meta': { 'errors': None },
            'results': {
                'count': self.get_count(),
                'docs': self.get_docset(),
                'facets': self.get_facets(),
            }
        }
        return resp
    
    def record_response(self, idx=0):
        try:
            return self.get_docset()[idx]
        except IndexError:
            return None
        
    def raw_response(self):
        return self.raw
    
    def get_docset(self):
        return self.raw['response'].get('docs', [])
    
    def get_docset_objects(self):
        return [SolrDocument(x) for x in self.get_docset()]

    def get_doc_object(self, idx):
        doc = self.get_doc(idx)
        if doc:
            return SolrDocument(doc)
    
    def get_doc(self, idx):
        try:
            return self.get_docset()[idx]
        except IndexError:
            log.debug("response has no doc at idx %d" % idx)
    
    def get_facets(self):
        return self.raw.get('facet_counts', {})
    
    def get_facets_fields(self, facet_name):
        #I extract the facets from the raw response
        facets_list = self.get_facets().get('facet_fields', {}).get(config.ALLOWED_FACETS_FROM_WEB_INTERFACE.get(facet_name, None), [])
        #I split the list in tuples
        facets_tuples_list = [tuple(facets_list[i:i+2]) for i in xrange(0, len(facets_list), 2)]
        #I extract the facet parameter submitted
        query_parameters = self.get_facet_param_field(facet_name)
        return [(elem[0], elem[1], 'selected') if elem[0] in query_parameters else (elem[0], elem[1], '') for elem in facets_tuples_list]
    
    def get_facet_param_field(self, facet_name):
        """
        Returns the list of query parameters for the current facet name
        """
        return [elem[1] for elem in self.get_facet_parameters() if elem[0] == facet_name]
    
    def get_facet_parameters(self):
        """
        Returns the list of query parameters
        """
        try: 
            self.request_facet_params
        except AttributeError:
            facet_params = []
            #first I extract the query parameters excluding the default ones
            search_params = list(set(self.request.params.get('fq', [])) - set(dict(config.SOLR_MISC_DEFAULT_PARAMS).get('fq', [])))
            #I extract only the parameters of the allowed facets
            for solr_facet in config.ALLOWED_FACETS_FROM_WEB_INTERFACE:
                for elem in search_params:
                    param = elem.split(':', 1)
                    if param[0] == config.ALLOWED_FACETS_FROM_WEB_INTERFACE[solr_facet]:
                        facet_params.append((solr_facet, param[1].strip('"')))
            self.request_facet_params = facet_params
        return self.request_facet_params
    
    def get_query(self):
        return self.raw['responseHeader']['params']['q']
    
    def get_count(self):
        return int(self.raw['response']['numFound'])
    
    def get_start_count(self):
        return int(self.raw['response']['start'])
    
    def get_qtime(self):
        return self.raw['responseHeader']['QTime']
        
        