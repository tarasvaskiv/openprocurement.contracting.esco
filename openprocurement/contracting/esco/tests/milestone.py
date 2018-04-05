# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import snitch
from openprocurement.contracting.esco.tests.base import BaseContractWebTest

from openprocurement.contracting.esco.tests.milestone_blanks import (
    listing_milestones,
    get_milestone_by_id,
)


class ContractMilestoneResourceTest(BaseContractWebTest):
    """ ESCO contract milestones resource test """

    initial_auth = ('Basic', ('broker', ''))

    test_listing_milestones = snitch(listing_milestones)
    test_get_milestone_by_id = snitch(get_milestone_by_id)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContractMilestoneResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
