# -*- coding: utf-8 -*-
from openprocurement.api.models import schematics_default_role
from openprocurement.api.utils import (
    json_view,
    context_unpack,
    APIResource,
)

from openprocurement.contracting.api.utils import save_contract
from openprocurement.contracting.core.utils import apply_patch
from openprocurement.contracting.esco.utils import milestoneresource, filter_milestones_by_contract_period_end_date
from openprocurement.contracting.esco.validation import (
    validate_patch_milestone_data, validate_update_milestone_in_allowed_status, validate_milestones_sum_amount_paid,
    validate_update_milestone_value
)


@milestoneresource(name='esco:Contract Milestones',
                     collection_path='/contracts/{contract_id}/milestones',
                     path='/contracts/{contract_id}/milestones/{milestone_id}',
                     contractType="esco",
                     description="Contract milestones")
class ContractMilestoneResource(APIResource):

    @json_view(permission='view_contract')
    def collection_get(self):
        """Milestones Listing

        Get Milestones List
        -------------

        Example request to get milestones list:
        # TODO: add example later no model yet exist

        """
        contract = self.request.validated['contract']
        return {'data': filter_milestones_by_contract_period_end_date(contract)}

    @json_view(permission='view_contract')
    def get(self):
        """Retrieving the milestone

        Example request for retrieving the proposal:

        .. sourcecode:: http
        # TODO: add example later no model yet exist


        """

        return {'data': self.request.context.serialize("view")}

    @json_view(
        content_type="application/json", permission='edit_contract',
        validators=(
            validate_patch_milestone_data, validate_update_milestone_in_allowed_status,
            validate_update_milestone_value, validate_milestones_sum_amount_paid
        )
    )
    def patch(self):
        """Update of milestone

        Example request to change bid proposal:
        # TODO: add example later no model yet exist

        """
        contract = self.request.context.__parent__
        if self.request.validated['data']['status'] in ['met', 'notMet', 'partiallyMet'] and \
                self.request.context.sequenceNumber < 16:
            next_milestone_end_year = contract.milestones[self.request.context.sequenceNumber].period.endDate.year
            if contract.period.endDate.year >= next_milestone_end_year:
                self.request.context.__parent__.milestones[self.request.context.sequenceNumber].status = u"pending"
        if apply_patch(self.request, src=self.request.context.serialize()):
            self.LOGGER.info(
                'Updated contract milestone {}'.format(self.request.context.id),
                extra=context_unpack(self.request, {'MESSAGE_ID': 'contract_milestone_patch'})
            )
            return {'data': self.request.context.serialize("view")}
