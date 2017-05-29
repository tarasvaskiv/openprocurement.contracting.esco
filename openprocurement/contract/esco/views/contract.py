# -*- coding: utf-8 -*-
from openprocurement.contracting.api.utils import contractingresource
from openprocurement.contracting.api.views.contract import (
    ContractResource as BaseContractResource,
)


@contractingresource(name='esco.EU:Contract',
                     path='/contracts/{contract_id}',
                     contractType='esco.EU',
                     description="Contract")
class ContractResource(BaseContractResource):
    """ ESCO Contract Resource """
