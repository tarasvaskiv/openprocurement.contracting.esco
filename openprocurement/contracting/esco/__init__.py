# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution

PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init esco contracts plugin.')
    from openprocurement.contracting.esco.models import Contract
    config.add_contract_contractType(Contract)
    config.scan("openprocurement.contract.esco.views")
