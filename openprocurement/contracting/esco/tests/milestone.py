# -*- coding: utf-8 -*-
import unittest

from openprocurement.api.tests.base import snitch
from openprocurement.contracting.esco.tests.base import BaseContractWebTest

from openprocurement.contracting.esco.tests.milestone_blanks import (
    listing_milestones,
    get_milestone_by_id,
    patch_milestones_status_change,
    patch_milestone,
    patch_milestone_description,
    patch_milestone_title,
    pending_status_update,
    scheduled_status_update,
    met_status_update,
    notMet_status_update,
    partiallyMet_status_update,
)


class ContractMilestoneResourceTest(BaseContractWebTest):
    """ ESCO contract milestones resource test """

    initial_auth = ('Basic', ('broker', ''))

    test_listing_milestones = snitch(listing_milestones)
    test_get_milestone_by_id = snitch(get_milestone_by_id)
    test_patch_milestones_status_change = snitch(patch_milestones_status_change)
    test_pending_status_update = snitch(pending_status_update)
    test_scheduled_status_update = snitch(scheduled_status_update)
    test_met_status_update = snitch(met_status_update)
    test_notMet_status_update = snitch(notMet_status_update)
    test_partiallyMet_status_update = snitch(partiallyMet_status_update)
    test_patch_milestone = snitch(patch_milestone)
    test_patch_milestone_description = snitch(patch_milestone_description)
    test_patch_milestone_title = snitch(patch_milestone_title)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContractMilestoneResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
