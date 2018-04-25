# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    get_now,
    raise_operation_error,
    update_logging_context,
)
from openprocurement.api.validation import validate_data
from openprocurement.contracting.esco.models import Milestone


# milestones
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

def validate_milestone_status_change(request):
    milestone = request.context
    data = request.validated['data']
    # can't update status from scheduled and to scheduled and to spare:)
    if milestone.status != data['status'] and (milestone.status == 'scheduled' or
                                               data['status'] == 'scheduled' or
                                               data['status'] == 'spare'):
        raise_operation_error(request, "Can't update milestone to {} status".format(data['status']))


def validate_update_milestone_in_terminated_status(request):
    milestone = request.context
    if milestone.status in ['met', 'notMet', 'partiallyMet', 'spare']:
        raise_operation_error(request, "Can't update milestone in current ({}) status".format(milestone.status))


def validate_update_milestone_in_scheduled_status(request):
    milestone = request.context
    changes = milestone.__parent__.changes
    pending_change = True if len(changes) > 0 and changes[-1].status == 'pending' else False
    if not pending_change and milestone.status == 'scheduled':
        raise_operation_error(request, "Can't update milestone in scheduled status without pending change")


def validate_update_milestone_value(request):
    milestone = request.context
    changes = milestone.__parent__.changes
    pending_change = True if len(changes) > 0 and changes[-1].status == 'pending' else False
    if not pending_change and milestone.status in ['pending', 'scheduled']:
        value = request.validated['data']['value']
        for k in value.keys():
            v = getattr(milestone.value, k)
            if v != value[k]:
                raise_operation_error(request, "Contract doesn't have any change in 'pending' status.")


def validate_update_milestone_amountPaid(request):
    milestone = request.context
    if milestone.status == 'scheduled':
        amountPaid = request.validated['data']['amountPaid']
        for k in amountPaid.keys():
            v = getattr(milestone.amountPaid, k)
            if v != amountPaid[k]:
                raise_operation_error(request, "Can't update 'amountPaid' for scheduled milestone")


def validate_pending_milestone_update_period(request):
    milestone = request.context
    # import pdb; pdb.set_trace()
    if milestone.status == 'pending' and milestone.period.startDate > get_now():
        raise_operation_error(request, "Can't update milestone before period.startDate")


# milestone documents
def validate_terminated_milestone_document_operation(request):
    data = request.validated['data']
    if "relatedItem" in data and data.get('documentOf') == 'milestone':
        for m in request.validated['contract'].milestones:
            if m.id == data['relatedItem'] and m.status in ['met', 'notMet', 'partiallyMet']:
                raise_operation_error(request, "Can't add document in current ({}) milestone status".format(m.status))


def validate_scheduled_milestone_document_operation(request):
    data = request.validated['data']
    changes = request.context.__parent__.changes
    pending_change = True if len(changes) > 0 and changes[-1].status == 'pending' else False
    if "relatedItem" in data and data.get('documentOf') == 'milestone':
        for m in request.validated['contract'].milestones:
            if m.id == data['relatedItem'] and m.status == 'scheduled' and not pending_change:
                raise_operation_error(request, "Can't add document to scheduled milestone without pending change")


def validate_terminate_contract_milestone_statuses(request):
    contract = request.context
    data = request.validated['data']
    if data['status'] != 'active' and \
            any(milestone['status'] in ['pending', 'scheduled'] for milestone in contract.milestones):
        raise_operation_error(request, "Contract have milestones in 'pending' or 'scheduled' statuses")


def validate_terminate_contract_amount_paid(request):
    data = request.validated['data']
    contract = request.context
    if data['status'] != 'active' and contract['value']['amount'] != contract['amountPaid']['amount'] and \
            not data['terminationDetails']:
        raise_operation_error(request, "terminationDetails is required.")
