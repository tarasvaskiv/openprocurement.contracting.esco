# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openprocurement.api.tests.base import snitch

from openprocurement.contracting.esco.tests.base import (
    test_contract_data,
    BaseWebTest,
    documents,
    BaseContractWebTest,
    BaseTerminatedContractWebTest,
    BaseContractTerminatedMilestonesWebTest,
)
from openprocurement.contracting.esco.tests.contract_blanks import (
    # ContractESCOTest
    simple_add_esco_contract,
    # ContractESCOResourceTest
    create_contract,
    create_contract_generated,
    patch_contract_NBUdiscountRate,
    patch_terminated_contract_NBUdiscountRate,
    # ContractResource4AdministratorTest
    contract_administrator_change,
    # ContractResource4BrokersTest
    patch_tender_contract,
    patch_tender_terminated_contract,
    patch_tender_contract_period,
    contract_type_check,
    esco_contract_milestones_check,
    contract_status_change_with_termination_details,
    contract_status_change_wo_termination_details,
    contract_status_change_with_not_met,
    contract_patch_milestones_value_amount,
)
from openprocurement.contracting.common.tests.contract_blanks import (
    # ContractESCOResourceTest
    empty_listing,
    listing,
    listing_changes,
    get_contract,
    not_found,
    create_contract_invalid,
    # ContractESCOWDocumentsWithDSResourceTest
    create_contract_w_documents,
    # ContractResource4BrokersTest
    contract_items_change,
    # ContractCredentialsTest
    get_credentials,
    generate_credentials,
)


class ContractTest(BaseWebTest):
    initial_data = test_contract_data

    test_simple_add_contract = snitch(simple_add_esco_contract)


class ContractResourceTest(BaseWebTest):
    """ esco contract resource test """
    initial_data = test_contract_data

    contract_type = 'esco'
    test_empty_listing = snitch(empty_listing)
    test_listing = snitch(listing)
    test_listing_changes = snitch(listing_changes)
    test_get_contract = snitch(get_contract)
    test_esco_contract_milestones_check = snitch(esco_contract_milestones_check)
    test_not_found = snitch(not_found)
    test_create_contract_invalid = snitch(create_contract_invalid)
    test_create_contract_generated = snitch(create_contract_generated)
    test_create_contract = snitch(create_contract)
    test_contract_type_check = snitch(contract_type_check)
    test_patch_contract_NBUdiscountRate = snitch(patch_contract_NBUdiscountRate)


class TerminatedContractResourceTest(BaseTerminatedContractWebTest):
    """ terminated esco contract resource test """
    initial_data = test_contract_data

    contract_type = 'esco'

    test_patch_terminated_contract_NBUdiscountRate = snitch(patch_terminated_contract_NBUdiscountRate)
    test_patch_tender_terminated_contract = snitch(patch_tender_terminated_contract)
    # TODO: Add all test which required terminated contract



class ContractWDocumentsWithDSResourceTest(BaseWebTest):
    docservice = True
    initial_data = deepcopy(test_contract_data)
    documents = deepcopy(documents)
    initial_data['documents'] = documents

    test_create_contract_w_documents = snitch(create_contract_w_documents)


class ContractResource4BrokersTest(BaseContractWebTest):
    """ esco contract resource test """
    initial_auth = ('Basic', ('broker', ''))
    pending_change = {
        'rationale': u'причина зміни укр',
        'rationale_en': 'change cause en',
        'rationaleTypes': ['itemPriceVariation']}

    test_patch_tender_contract = snitch(patch_tender_contract)
    test_contract_status_change_with_termination_details = snitch(contract_status_change_with_termination_details)
    test_contract_status_change_wo_termination_details = snitch(contract_status_change_wo_termination_details)
    test_contract_status_change_with_not_met = snitch(contract_status_change_with_not_met)
    test_contract_patch_milestones_value_amount = snitch(contract_patch_milestones_value_amount)
    # test_contract_items_change = snitch(contract_items_change)
    test_patch_tender_contract_period = snitch(patch_tender_contract_period)


class ContractResource4AdministratorTest(BaseContractWebTest):
    """ esco contract resource test """
    initial_auth = ('Basic', ('administrator', ''))
    initial_data = test_contract_data

    test_contract_administrator_change = snitch(contract_administrator_change)


class ContractCredentialsTest(BaseContractTerminatedMilestonesWebTest):
    """ esco contract credentials tests """

    initial_auth = ('Basic', ('broker', ''))
    initial_data = test_contract_data

    test_get_credentials = snitch(get_credentials)
    test_generate_credentials = snitch(generate_credentials)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContractTest))
    suite.addTest(unittest.makeSuite(ContractResourceTest))
    suite.addTest(unittest.makeSuite(TerminatedContractResourceTest))
    suite.addTest(unittest.makeSuite(ContractWDocumentsWithDSResourceTest))
    suite.addTest(unittest.makeSuite(ContractCredentialsTest))
    suite.addTest(unittest.makeSuite(ContractResource4BrokersTest))
    suite.addTest(unittest.makeSuite(ContractResource4AdministratorTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
