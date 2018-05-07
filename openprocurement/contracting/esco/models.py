# -*- coding: utf-8 -*-
from uuid import uuid4
from decimal import Decimal
from zope.interface import implementer
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, FloatType, IntType, MD5Type
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable

from openprocurement.api.utils import get_now
from openprocurement.api.models import (
    plain_role, schematics_default_role,
    Value as BaseValue, Period, Model, ListType, DecimalType, SifterListType
)
from openprocurement.contracting.core.models import (
    IContract, IsoDateTimeType,
    Contract as BaseContract, Document as BaseDocument,
    get_contract,
)
from openprocurement.contracting.core.models import (
    contract_create_role as base_contract_create_role,
    contract_view_role, contract_administrator_role
)
from openprocurement.tender.esco.models import (
    ESCOValue as BaseESCOValue, to_decimal,
    view_value_role_esco as base_view_value_role_esco
)
from esculator import escp, npv


contract_create_role = base_contract_create_role + \
    whitelist('NBUdiscountRate', 'noticePublicationDate',
              'yearlyPaymentsPercentageRange', 'minValue', 'milestones',
              'fundingKind')

contract_edit_role = (whitelist(
    'title', 'title_en', 'title_ru', 'description', 'description_en',
    'description_ru', 'status', 'period', 'items', 'terminationDetails',
))
view_value_role_esco = base_view_value_role_esco + whitelist('amount_escp')


class IESCOContract(IContract):
    """ ESCO Contract marker interface """


class ESCOValue(BaseESCOValue):
    class Options:
        roles = {
            'embedded': view_value_role_esco,
            'view': view_value_role_esco,
            'create': whitelist('amount', 'amount_escp', 'amountPerformance',
                                'amountPerformance_npv', 'yearlyPaymentsPercentage',
                                'annualCostsReduction', 'contractDuration',
                                'currency', 'valueAddedTaxIncluded'),
            'edit': whitelist('amount', 'amount_escp', 'amountPerformance', 'amountPerformance_npv',
                              'yearlyPaymentsPercentage', 'annualCostsReduction', 'contractDuration',
                              'currency', 'valueAddedTaxIncluded'),
            'auction_view': whitelist('amountPerformance', 'yearlyPaymentsPercentage',
                                      'annualCostsReduction', 'contractDuration',
                                      'currency', 'valueAddedTaxIncluded'),
            'auction_post': whitelist('amount_escp', 'amountPerformance_npv',
                                      'yearlyPaymentsPercentage', 'contractDuration'),
            'active.qualification': view_value_role_esco,
            'active.awarded': view_value_role_esco,
            'complete': view_value_role_esco,
            'unsuccessful': view_value_role_esco,
            'cancelled': view_value_role_esco,
        }

    def validate_yearlyPaymentsPercentage(self, data, value):
        pass

    @serializable(serialized_name='amountPerformance', type=DecimalType(precision=-2))
    def amountPerformance_npv(self):
        """ Calculated energy service contract performance indicator """
        return to_decimal(npv(
            self.contractDuration.years,
            self.contractDuration.days,
            self.yearlyPaymentsPercentage,
            self.annualCostsReduction,
            self.__parent__.noticePublicationDate,
            self.__parent__.NBUdiscountRate))

    @serializable(serialized_name='amount', type=DecimalType(precision=-2))
    def amount_escp(self):
        return sum([milestone.value.amount for milestone in
                    self.__parent__.milestones if milestone.status != 'spare'])


class Value(BaseValue):
    amount = DecimalType(required=True, precision=-2, min_value=Decimal('0'))
    class Options:
        roles = {
            'edit': whitelist('amount')
        }


class Document(BaseDocument):
    """ Contract Document """

    documentOf = StringType(
        required=True,
        choices=['tender', 'item', 'lot', 'contract', 'change', 'milestone'],
        default='contract'
    )

    def validate_relatedItem(self, data, relatedItem):
            if not relatedItem and \
                    data.get('documentOf') in ['item', 'change', 'milestone']:
                raise ValidationError(u'This field is required.')
            if relatedItem and isinstance(data['__parent__'], Model):
                contract = get_contract(data['__parent__'])
                if data.get('documentOf') == 'change' and \
                        relatedItem not in [i.id for i in contract.changes]:
                    raise ValidationError(
                        u"relatedItem should be one of changes"
                    )
                if data.get('documentOf') == 'item' and \
                        relatedItem not in [i.id for i in contract.items]:
                    raise ValidationError(
                        u"relatedItem should be one of items"
                    )
                if data.get('documentOf') == 'milestone' and \
                        relatedItem not in [i.id for i in contract.milestones]:
                    raise ValidationError(
                        u"relatedItem should be one of milestones"
                    )


class Milestone(Model):
    """ Contract Milestone """

    id = MD5Type(required=True, default=lambda: uuid4().hex)
    date = IsoDateTimeType()
    dateModified = IsoDateTimeType()
    description = StringType()
    period = ModelType(Period)
    sequenceNumber = IntType(required=True)
    status = StringType(
        required=True,
        choices=['scheduled', 'met', 'notMet', 'partiallyMet', 'pending', 'spare'],
    )
    value = ModelType(Value, required=True)
    amountPaid = ModelType(Value)
    title = StringType()

    class Options:
        roles = {
            'view': whitelist(),
            'spare': whitelist(),
            'scheduled': schematics_default_role,
            'pending': schematics_default_role,
            'met': schematics_default_role,
            'notMet': schematics_default_role,
            'partiallyMet': schematics_default_role,
            'edit': whitelist('status', 'amountPaid', 'value', 'title', 'description')
        }

    def validate_status(self, data, status):
        if status in ['met', 'partiallyMet', 'notMet']:
            if len(data['title']) == 0:
                raise ValidationError(u"Title can't be empty in follow statuses (met, notMet, partiallyMet)")
            if len(data['description']) == 0:
                raise ValidationError(u"Description can't be empty in follow statuses (met, notMet, partiallyMet)")
        if status == 'met' and not data['amountPaid'].amount >= data['value'].amount:
            raise ValidationError(u"Milestone can't be in status 'met' if amountPaid.amount less than value.amount")
        elif status == 'notMet' and data['amountPaid'].amount > 0:
            raise ValidationError(u"Milestone can't be in status 'notMet' if amountPaid.amount greater than 0")
        elif status == 'partiallyMet' and not 0 < data['amountPaid'].amount < data['value'].amount:
            raise ValidationError(
                u"Milestone can't be in status 'partiallyMet' if amountPaid.amount not greater then 0 "
                "or not less value.amount"
            )


@implementer(IESCOContract)
class Contract(BaseContract):
    """ ESCO Contract """

    contractType = StringType(default='esco')
    fundingKind = StringType(choices=['budget', 'other'], required=True)
    milestones = SifterListType(
        ModelType(Milestone), default=list(), filter_by='status',
        filter_in_values=['scheduled', 'pending', 'met', 'notMet', 'partiallyMet']
    )
    minValue = ModelType(
        Value, required=False,
        default={'amount': 0, 'currency': 'UAH', 'valueAddedTaxIncluded': True}
    )
    NBUdiscountRate = DecimalType(
        required=True, min_value=Decimal('0'), max_value=Decimal('0.99'), precision=-5
    )
    noticePublicationDate = IsoDateTimeType()
    value = ModelType(ESCOValue)
    amountPaid = ModelType(Value)
    yearlyPaymentsPercentageRange = DecimalType(required=True)
    documents = ListType(ModelType(Document), default=list())


    class Options:
        roles = {
            'plain': plain_role,
            'create': contract_create_role,
            'edit_active': contract_edit_role,
            'edit_terminated': whitelist(),
            'view': contract_view_role + whitelist('NBUdiscountRate', 'contractType', 'milestones'),
            'Administrator': contract_administrator_role,
            'default': schematics_default_role,
        }

    @serializable(serialized_name='amountPaid', serialize_when_none=False, type=ModelType(Value))
    def contract_amountPaid(self):
        amount = sum([milestone.amountPaid.amount for milestone in
                      self.milestones if milestone.status != 'spare'])
        return Value(dict(amount=amount,
                          currency=self.value.currency,
                          valueAddedTaxIncluded=self.value.valueAddedTaxIncluded))
