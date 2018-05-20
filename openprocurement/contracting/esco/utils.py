# -*- coding: utf-8 -*-
import os
from calendar import isleap
from decimal import Decimal
from copy import deepcopy
from pytz import timezone
from iso8601 import parse_date
from datetime import datetime, timedelta
from uuid import uuid4
from cornice.resource import resource
from functools import partial

from openprocurement.api.traversal import get_item
from openprocurement.api.utils import error_handler
from openprocurement.contracting.api.traversal import Root

from esculator.calculations import discount_rate_days, payments_days, calculate_payments

def factory(request):
    request.validated['contract_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('contract_id'):
        return root
    request.validated['contract_id'] = request.matchdict['contract_id']
    contract = request.contract
    contract.__parent__ = root
    request.validated['contract'] = request.validated['db_doc'] = contract
    if request.method != 'GET':
        request.validated['contract_src'] = contract.serialize('plain')
    if request.matchdict.get('milestone_id'):
        return get_item(contract, 'milestone', request)
    request.validated['id'] = request.matchdict['contract_id']
    return contract


milestoneresource = partial(
    resource,
    error_handler=error_handler,
    factory=factory
)

TZ = timezone(os.environ['TZ'] if 'TZ' in os.environ else 'Europe/Kiev')


def to_decimal(fraction):
    return str(Decimal(fraction.numerator) / Decimal(fraction.denominator))


def generate_milestones(contract):
    days_per_year = 365
    npv_calculation_duration = 20
    announcement_date = parse_date(contract['noticePublicationDate'])

    contract_start_date = parse_date(contract['period']['startDate'])
    contract_end_date = parse_date(contract['period']['endDate'])

    contract_duration_years = contract['value']['contractDuration']['years']
    contract_duration_days = contract['value']['contractDuration']['days']
    yearly_payments_percentage = contract['value']['yearlyPaymentsPercentage']
    annual_cost_reduction = contract['value']['annualCostsReduction']

    days_for_discount_rate = discount_rate_days(announcement_date, days_per_year, npv_calculation_duration)
    days_with_payments = payments_days(
        contract_duration_years, contract_duration_days, days_for_discount_rate, days_per_year,
        npv_calculation_duration
    )

    payments = calculate_payments(
        yearly_payments_percentage, annual_cost_reduction, days_with_payments, days_for_discount_rate
    )

    milestones = []
    years_before_contract_start = contract_start_date.year - announcement_date.year

    last_milestone_sequence_number = 16 + years_before_contract_start

    for sequence_number in xrange(1, last_milestone_sequence_number + 1):
        date_modified = datetime.now(TZ)

        milestone = {
            'id': uuid4().hex,
            'sequenceNumber': sequence_number,
            'date': date_modified.isoformat(),
            'dateModified': date_modified.isoformat(),
            'amountPaid': {
                "amount": 0,
                "currency": contract['value']['currency'],
                "valueAddedTaxIncluded": contract['value']['valueAddedTaxIncluded']
            },
            'value': {
                "amount": to_decimal(payments[sequence_number - 1]),
                "currency": contract['value']['currency'],
                "valueAddedTaxIncluded": contract['value']['valueAddedTaxIncluded']
            },
        }

        if sequence_number == 1:
            milestone_start_date = announcement_date
            milestone_end_date = datetime(announcement_date.year + sequence_number, 1, 1, tzinfo=TZ)
            milestone['status'] = 'pending'
        elif sequence_number == last_milestone_sequence_number:
            milestone_start_date = datetime(announcement_date.year + sequence_number - 1, 1, 1, tzinfo=TZ)
            milestone_end_date = datetime(
                announcement_date.year + sequence_number - 1, contract_start_date.month, contract_start_date.day,
                tzinfo=TZ
            )
        else:
            milestone_start_date = datetime(announcement_date.year + sequence_number - 1, 1, 1, tzinfo=TZ)
            milestone_end_date = datetime(announcement_date.year + sequence_number, 1, 1, tzinfo=TZ)

        if contract_end_date.year >= milestone_start_date.year and sequence_number != 1:
            milestone['status'] = 'scheduled'
        elif contract_end_date.year < milestone_start_date.year:
            milestone['status'] = 'spare'

        if contract_end_date.year == announcement_date.year + sequence_number - 1:
            milestone_end_date = datetime(
                announcement_date.year + sequence_number - 1, contract_end_date.month, contract_end_date.day, tzinfo=TZ
            )

        milestone['period'] = {
            'startDate': milestone_start_date.isoformat(),
            'endDate': milestone_end_date.isoformat()
        }
        title = "Milestone #{} of year {}".format(sequence_number, milestone_start_date.year)
        milestone['title'] = title
        milestone['description'] = title
        milestones.append(milestone)

    return milestones


def get_contract_max_endDate(contract_period_startDate):
    day = contract_period_startDate.day - 1 if contract_period_startDate.day == 29 \
                                               and contract_period_startDate.month == 2 \
                                               and not isleap(contract_period_startDate.year + 15) \
        else contract_period_startDate.day
    return contract_period_startDate.replace(contract_period_startDate.year + 15, day=day)



def update_milestones_dates_and_statuses(request):
    """
    Update milestones endDates and statuses, due changed contract period
    endDate. Milestones are copied from request.validated['data']['milestones']
    If endDate is increased, some spare milestones need to be opened (status
    is changed to scheduled).
    If endDate is decreased, some scheduled milestones need to be changed to
    spare.

    :param request
    :return: None
    :rtype: None
    """
    contract = request.context
    new_contract_end_date = parse_date(request.validated['data']['period']['endDate'])
    milestones = request.context.milestones  # real milestones
    target_milestones = deepcopy(request.validated['contract_src']['milestones'])
    for number, m in enumerate(milestones):
        if m.status in ['met', 'notMet', 'partiallyMet']:
            continue
        # stretch milestone period endDate
        if m.period.startDate <= contract.period.endDate <= m.period.endDate:
            if number + 1 < len(milestones):
                target_milestones[number]['period']['endDate'] = \
                    milestones[number+1].period.startDate.isoformat()
            else:
                target_milestones[number]['period']['endDate'] = get_contract_max_endDate(contract.period.startDate
                                                                                          ).isoformat()
                if contract.mode:
                    days_diff = (get_contract_max_endDate(contract.period.startDate) - contract.period.startDate).days
                    target_milestones[number]['period']['endDate'] = contract.period.startDate + timedelta(
                        seconds=days_diff)
        # shrink milestone period endDate
        if target_milestones[number]['period']['startDate']\
                <= request.validated['data']['period']['endDate'] <=\
                target_milestones[number]['period']['endDate']:
            target_milestones[number]['period']['endDate'] = new_contract_end_date
        #  increase endDate, need open (spare-> scheduled) new milestones
        if new_contract_end_date > contract.period.endDate:
            if m.period.startDate <= new_contract_end_date:
                if m.status == 'spare':
                    target_milestones[number]['status'] = 'scheduled'
        #  decrease endDate need to hide (scheduled -> spare) milestones
        else:
            if m.period.endDate > new_contract_end_date:
                if m.status == 'scheduled':
                    target_milestones[number]['status'] = 'spare'
                if m.period.startDate <= new_contract_end_date:
                    if m.status != 'pending':
                        target_milestones[number]['status'] = 'scheduled'

    request.validated['data']['milestones'] = target_milestones
