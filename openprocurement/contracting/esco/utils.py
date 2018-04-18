# -*- coding: utf-8 -*-
from cornice.resource import resource
from functools import partial

from openprocurement.api.traversal import get_item
from openprocurement.api.utils import error_handler
from openprocurement.contracting.api.traversal import Root


def factory(request):
    request.validated['contract_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('contract_id'):
        return root
    request.validated['contract_id'] = request.matchdict['contract_id']
    contract = request.contract
    contract.__parent__ = root
    request.validated['contract'] = request.validated['db_doc'] = contract
    if request.method != 'GET':
        request.validated['contract_src'] = contract.serialize('plain')
    if request.matchdict.get('milestone_id'):
        return get_item(contract, 'milestone', request)
    request.validated['id'] = request.matchdict['contract_id']
    return contract


milestoneresource = partial(
    resource,
    error_handler=error_handler,
    factory=factory
)
