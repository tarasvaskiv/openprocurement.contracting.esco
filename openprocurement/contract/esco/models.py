# -*- coding: utf-8 -*-
from zope.interface import implementer
from schematics.types import StringType
from openprocurement.contracting.api.models import (
    IContract,
    Contract as BaseContract
)


class IESCOContract(IContract):
    """ ESCO Contract marker interface """

@implementer(IESCOContract)
class Contract(BaseContract):
    """ Contract """

    contractType = StringType(choices=['common', 'esco.EU'], default='esco.EU')
