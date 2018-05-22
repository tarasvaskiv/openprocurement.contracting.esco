# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openprocurement.api.tests.base import snitch
from openprocurement.contracting.esco.tests.base import BaseContractWebTest
from openprocurement.contracting.esco.utils import generate_milestones

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


class ContractMilestoneResourceMixin(object):
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


class ContractMilestoneResourceTest(BaseContractWebTest, ContractMilestoneResourceMixin):
    """ ESCO contract milestones resource test """

    initial_auth = ('Basic', ('broker', ''))


class ContractMilestoneResourceTestModeTest(BaseContractWebTest, ContractMilestoneResourceMixin):
    """ ESCO contract milestones resource test """

    initial_auth = ('Basic', ('broker', ''))

    def setUp(self):
        self.initial_data = deepcopy(self.initial_data)
        self.initial_data["mode"] = u"test"
        del self.initial_data['milestones']
        self.initial_data['milestones'] = generate_milestones(self.initial_data)

        super(ContractMilestoneResourceTestModeTest, self).setUp()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContractMilestoneResourceTest))
    suite.addTest(unittest.makeSuite(ContractMilestoneResourceTestModeTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
