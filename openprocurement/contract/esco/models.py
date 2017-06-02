# -*- coding: utf-8 -*-
from zope.interface import implementer
from schematics.transforms import whitelist
from schematics.types import StringType, FloatType
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable
from openprocurement.contracting.api.models import (
    IContract,
    Contract as BaseContract
)
from openprocurement.api.models import (
    plain_role, schematics_default_role,
    Value,
)
from openprocurement.contracting.api.models import (
    contract_create_role, contract_edit_role,
    contract_view_role, contract_administrator_role
)
from openprocurement.tender.esco.models import ESCOValue


class IESCOContract(IContract):
    """ ESCO Contract marker interface """


@implementer(IESCOContract)
class Contract(BaseContract):
    """ ESCO Contract """

    contractType = StringType(choices=['common', 'esco.EU'], default='esco.EU')
    NBUdiscountRate = FloatType(required=True, min_value=0, max_value=0.99)
    value = ModelType(ESCOValue)

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

    @serializable(serialized_name='amountPaid', serialize_when_none=False, type=ModelType(Value))
    def contract_amountPaid(self):
        if self.amountPaid:
            return Value(dict(amount=self.amountPaid.amount,
                              currency=self.value.currency,
                              valueAddedTaxIncluded=self.value.valueAddedTaxIncluded))
