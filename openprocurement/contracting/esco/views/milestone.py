# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    json_view,
    context_unpack,
    APIResource,
)

from openprocurement.contracting.api.utils import contractingresource, \
    save_contract, apply_patch


@contractingresource(name='esco:Contract Milestones',
                     collection_path='/contracts/{contract_id}/milestones',
                     path='/contracts/{contract_id}/milestones/{milestone_id}',
                     contractType="esco",
                     description="Contract milestones")
class ContractMilestoneResource(APIResource):

    @json_view(content_type="application/json", permission='create_milestone',
               validators=())
    def collection_post(self):
        """Registration of new milestone

        Creating new Milestone
        -------------------------
        # TODO: add example later no model yet exist
        Example request to create milestone:

        """

        contract = self.request.validated['contract']
        milestone = self.request.validated['milestone']
        contract.milestones.append(milestone)

        if save_contract(self.request):
            self.LOGGER.info(
                'Created contract milestone {}'.format(milestone.id),
                extra=context_unpack(self.request, {
                    'MESSAGE_ID': 'contract_milestone_create'},
                                     {'milestone_id': milestone.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url(
                '{}:Contract Milestones'.format(contract.contractType),
                contract_id=contract.id, milestone_id=milestone['id'])
            return {'data': milestone.serialize('view')}

    @json_view(permission='view_milestone', validators=())
    def collection_get(self):
        """Milestones Listing

        Get Milestones List
        -------------

        Example request to get milestones list:
        # TODO: add example later no model yet exist

        """
        contract = self.request.validated['contract']
        return {
            'data': [i.serialize("view") for i
                     in contract.milestones]}

    @json_view(permission='view_milestone')
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
