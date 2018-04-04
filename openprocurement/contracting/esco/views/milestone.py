# -*- coding: utf-8 -*-
from openprocurement.api.models import schematics_default_role
from openprocurement.api.utils import (
    json_view,
    context_unpack,
    APIResource,
)

from openprocurement.contracting.api.utils import save_contract
from openprocurement.contracting.core.utils import apply_patch
from openprocurement.contracting.esco.utils import milestoneresource


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
        return {'data': [i.serialize("view") for i in contract.milestones]}

    @json_view(permission='view_contract')
    def get(self):
        """Retrieving the milestone

        Example request for retrieving the proposal:

        .. sourcecode:: http
        # TODO: add example later no model yet exist


        """

        return {'data': self.request.context.serialize("view")}

    @json_view(content_type="application/json", permission='edit_milestone',
               validators=())
    def patch(self):
        """Update of milestone

        Example request to change bid proposal:
        # TODO: add example later no model yet exist

        """

        if apply_patch(self.request, src=self.request.context.serialize()):
            self.LOGGER.info(
                'Updated contract milestone {}'.format(
                    self.request.context.id),
                extra=context_unpack(self.request,
                                     {
                                         'MESSAGE_ID': 'contract_milestone_patch'}))
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='edit_milestone', validators=())
    def delete(self):
        """Cancelling the milestone

        Example request for cancelling the proposal:
        # TODO: add example later no model yet exist

        """
        milestone = self.request.context
        res = milestone.serialize("view")
        self.request.validated['contract'].milestones.remove(milestone)

        # why do we need this
        self.request.validated['contract'].modified = False

        if save_contract(self.request):
            self.LOGGER.info(
                'Deleted contract milestone {}'.format(
                    self.request.context.id),
                extra=context_unpack(self.request,
                    {'MESSAGE_ID': 'contract_milestone_delete'})
            )
            return {'data': res}
