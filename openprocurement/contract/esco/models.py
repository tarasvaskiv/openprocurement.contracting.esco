# -*- coding: utf-8 -*-
from zope.interface import implementer
from schematics.transforms import whitelist
from schematics.types import StringType, FloatType
from openprocurement.contracting.api.models import (
    IContract,
    Contract as BaseContract
)
from openprocurement.api.models import (
    plain_role, schematics_default_role
)
from openprocurement.contracting.api.models import (
    contract_create_role, contract_edit_role,
    contract_view_role, contract_administrator_role
)


class IESCOContract(IContract):
    """ ESCO Contract marker interface """

@implementer(IESCOContract)
class Contract(BaseContract):
    """ ESCO Contract """

    contractType = StringType(choices=['common', 'esco.EU'], default='esco.EU')
    NBUdiscountRate = FloatType(required=True, min_value=0, max_value=0.99)

    class Options:
        roles = {
            'plain': plain_role,
            'create': contract_create_role + whitelist('NBUdiscountRate'),
            'edit_active': contract_edit_role,
            'edit_terminated': whitelist(),
            'view': contract_view_role + whitelist('NBUdiscountRate'),
            'Administrator': contract_administrator_role,
            'default': schematics_default_role,
        }