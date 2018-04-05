# -*- coding: utf-8 -*-
from openprocurement.api.utils import update_logging_context, raise_operation_error
from openprocurement.api.validation import validate_data
from openprocurement.contracting.esco.models import Milestone


def validate_patch_milestone_data(request):
    return validate_data(request, Milestone, True)


def validate_milestones_sum_amount_paid(request):
    amountPaid = request.validated['data'].get('amountPaid', {}).get('amount', 0)
    contract = request.context.__parent__
    milestones_amountPaids = [milestone.amountPaid.amount for milestone in contract.milestones]
    if not sum(milestones_amountPaids) + amountPaid <= contract.value.amount:
        raise_operation_error(
            request, u"The sum of milestones amountPaid.amount can't be greater than contract.value.amount"
        )


def validate_update_milestone_in_allowed_status(request):
    milestone = request.context
    changes = milestone.__parent__.changes
    pending_change = True if len(changes) > 0 and changes[-1].status == 'pending' else False
    # Modify 'scheduled' milestone allow only if available change in 'pending' status
    if pending_change and milestone.status not in ['pending', 'scheduled']:
        raise_operation_error(request, "Can't update milestone in current ({}) status".format(milestone.status))
    elif not pending_change and milestone.status != 'pending':
        raise_operation_error(request, "Can't update milestone in current ({}) status".format(milestone.status))


def validate_update_milestone_value(request):
    if 'value' not in request.json_body['data']:
        return
    milestone = request.context
    changes = milestone.__parent__.changes
    pending_change = True if len(changes) > 0 and changes[-1].status == 'pending' else False
    value = request.validated['data']['value']
    for key in value.keys():
        v = getattr(milestone.value, key)
        if v != value[key] and not pending_change:
            raise_operation_error(request, u"Contract don't have any change in 'pending' status.")
