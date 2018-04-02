# -*- coding: utf-8 -*-
from logging import getLogger
from pkg_resources import get_distribution
from pyramid.interfaces import IRequest

from openprocurement.api.interfaces import IContentConfigurator
from openprocurement.contracting.esco.models import IESCOContract, Contract
from openprocurement.contracting.esco.adapters import ContractESCOConfigurator

PKG = get_distribution(__package__)

LOGGER = getLogger(PKG.project_name)


def includeme(config):
    LOGGER.info('Init contracting.esco plugin.')
    config.add_contract_contractType(Contract)
    config.scan("openprocurement.contracting.esco.views")
    config.registry.registerAdapter(ContractESCOConfigurator,
                                    (IESCOContract, IRequest),
                                    IContentConfigurator)
