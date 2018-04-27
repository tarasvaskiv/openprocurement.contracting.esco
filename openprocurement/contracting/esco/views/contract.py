# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    context_unpack,
    json_view
)

from openprocurement.contracting.api.utils import (
    contractingresource,
    save_contract
)
from openprocurement.contracting.core.utils import apply_patch
from openprocurement.contracting.core.validation import (
    validate_patch_contract_data,
    validate_contract_update_not_in_allowed_status,
)
from openprocurement.contracting.common.views.contract import (
    ContractResource as BaseContractResource,
)
from openprocurement.contracting.esco.validation import (
    validate_terminate_contract_milestone_statuses,
    validate_terminate_contract_amount_paid,
    validate_update_contract_start_date,
    validate_update_contract_end_date
)

from openprocurement.contracting.esco.utils import update_milestones_dates_and_statuses


@contractingresource(name='esco:Contract',
                     path='/contracts/{contract_id}',
                     contractType='esco',
                     description="Contract")
class ContractResource(BaseContractResource):
    """ ESCO Contract Resource """

    @json_view(content_type="application/json", permission='edit_contract',
               validators=(validate_patch_contract_data,
                           validate_contract_update_not_in_allowed_status,
                           validate_terminate_contract_milestone_statuses,
                           validate_terminate_contract_amount_paid,
                           validate_update_contract_start_date,
                           validate_update_contract_end_date))
    def patch(self):
        """Contract Edit (partial)
        """
        if 'period' in self.request.validated['data']:
            update_milestones_dates_and_statuses(self.request)
        contract = self.request.validated['contract']
        apply_patch(self.request, save=False, src=self.request.validated['contract_src'])

        # validate_terminate_contract_without_amountPaid(self.request)

        if save_contract(self.request):
            self.LOGGER.info('Updated contract {}'.format(contract.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'contract_patch'}))
            return {'data': contract.serialize('view')}
