# -*- coding: utf-8 -*-
from openprocurement.contracting.api.utils import (
    contractingresource,
)
from openprocurement.contracting.api.views.contract import (
    ContractsResource as BaseContractsResource,
    ContractResource as BaseContractResource,
    ContractCredentialsResource as BaseContractCredentialsResource
)


@contractingresource(name='esco.EU:Contract',
                     path='/contracts/{contract_id}',
                     description="Contract")
class ContractResource(BaseContractsResource):
    """ ESCO Contract Resource """
