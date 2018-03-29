# -*- coding: utf-8 -*-
from zope.interface import implementer
from schematics.transforms import whitelist
from schematics.types import StringType, FloatType, IntType
from schematics.types.compound import ModelType
from schematics.types.serializable import serializable
from openprocurement.contracting.core.models import (
    IContract,
    Contract as BaseContract, Document as BaseDocument
)
from openprocurement.api.models import (
    plain_role, schematics_default_role,
    Value, Period, Model
)
from openprocurement.contracting.core.models import (
    contract_create_role, contract_edit_role,
    contract_view_role, contract_administrator_role
)
from openprocurement.tender.esco.models import ESCOValue


class IESCOContract(IContract):
    """ ESCO Contract marker interface """


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
                        relatedItem not in [i.id for i in contract.milesones]:
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
    sequenceNumber = IntType(required=True, min_number=1, max_number=16)
    status = StringType(
        required=True,
        choices=['scheduled', 'met', 'notMet', 'partiallyMet'],
        default='scheduled'
    )
    value = ModelType(Value, required=True)
    amountPaid = ModelType(
        Value,
        default={'amount': 0, 'currency': 'UAH', 'valueAddedTaxIncluded': True}
    )
    title = StringType()


@implementer(IESCOContract)
class Contract(BaseContract):
    """ ESCO Contract """

    contractType = StringType(choices=['common', 'esco'], default='esco')
    fundingKind = StringType(choices=['budget', 'other'], default='other')
    milesones = ListType(ModelType(Milestone), default=list())
    minValue = ModelType(Value, required=True)
    NBUdiscountRate = FloatType(required=True, min_value=0, max_value=0.99)
    noticePublicationDate = IsoDateTimeType()
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
