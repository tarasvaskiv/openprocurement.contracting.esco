# -*- coding: utf-8 -*-
from zope.interface import implementer
from schematics.transforms import whitelist
from schematics.types import StringType, FloatType, BooleanType
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
from openprocurement.tender.esco.models import (
    ESCOValue as BaseESCOValue
)
from openprocurement.tender.esco.utils import calculate_npv


class IESCOContract(IContract):
    """ ESCO Contract marker interface """


class ESCOValue(BaseESCOValue):
    """ ESCO Value for Contract """

    currency = StringType(required=True, default=u'UAH', max_length=3, min_length=3)  # The currency in 3-letter ISO 4217 format.
    valueAddedTaxIncluded = BooleanType(required=True, default=True)

    class Options:
        roles = {
            'create': whitelist('amount', 'yearlyPayments', 'annualCostsReduction', 'contractDuration', 'currency', 'valueAddedTaxIncluded'),
            'edit': whitelist('amount', 'yearlyPayments', 'annualCostsReduction', 'contractDuration', 'currency', 'valueAddedTaxIncluded'),
            'auction_view': whitelist('amount', 'yearlyPayments', 'annualCostsReduction', 'contractDuration', 'currency', 'valueAddedTaxIncluded'),
            'auction_post': whitelist('amount', 'yearlyPayments', 'annualCostsReduction', 'contractDuration', 'currency', 'valueAddedTaxIncluded'),
        }

    @serializable
    def amount(self):
        """ Calculated energy service contract perfomance indicator """
        return calculate_npv(self.__parent__.NBUdiscountRate,
                             self.annualCostsReduction,
                             self.yearlyPayments,
                             self.contractDuration)



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
