from flask import Blueprint, request

from aleph import authz
from aleph.core import url_for
from aleph.views.util import jsonify, Pager
from aleph.search.queries import document_query
from aleph.search import search_documents

blueprint = Blueprint('search', __name__)


def add_urls(doc):
    doc['archive_url'] = url_for('data.package',
                                 collection=doc.get('collection'),
                                 package_id=doc.get('id'))
    doc['manifest_url'] = url_for('data.manifest',
                                  collection=doc.get('collection'),
                                  package_id=doc.get('id'))
    return doc


@blueprint.route('/api/1/query')
def query():
    authorized = authz.request_collections('read')
    query = document_query(request.args, authorized=authorized)
    pager = Pager(search_documents(query),
                  results_converter=lambda ds: [add_urls(d) for d in ds])
    return jsonify(pager)