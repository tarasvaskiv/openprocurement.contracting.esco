# -*- coding: utf-8 -*-
from datetime import timedelta
from openprocurement.api.utils import get_now


def listing_milestones(self):
    response = self.app.get('/contracts/{}/milestones'.format(self.contract['id']))
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    data = response.json['data']
    self.assertEqual(len(data), 7)
    sequenceNumber = 1
    for milestone in data:
        if sequenceNumber == 1:
            self.assertEqual(milestone['status'], 'pending')
        else:
            self.assertEqual(milestone['status'], 'scheduled')
        self.assertEqual(milestone['sequenceNumber'], sequenceNumber)
        sequenceNumber += 1


def get_milestone_by_id(self):
    milestone_id = self.initial_data['milestones'][1]['id']
    contract_id = self.contract['id']
    response = self.app.get(
        '/contracts/{}/milestones/{}'.format(contract_id, milestone_id)
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    initial_milestone = self.initial_data['milestones'][1]
    milestone = response.json['data']
    for key in initial_milestone.keys():
        self.assertEqual(initial_milestone[key], milestone[key])
    self.assertEqual(milestone['id'], milestone_id)
    self.assertEqual(milestone['status'], 'scheduled')
    self.assertEqual(
        milestone['amountPaid'],
        {'amount': 0, 'currency': 'UAH', 'valueAddedTaxIncluded': True}
    )
    self.assertIn('date', milestone)
    self.assertIn('dateModified', milestone)

    response = self.app.get(
        '/contracts/{}/milestones/invalid_id'.format(contract_id),
        status=404
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': u'Not Found',
                u'location': u'url',
                u'name': u'milestone_id'
            }]
        }
    )


def failed_patch_milestones(self):
    scheduled_milestone_id = self.initial_data['milestones'][2]['id']
    pending_milestone_id = self.initial_data['milestones'][0]['id']
    contract_id = self.contract['id']
    data = {'amountPaid': {'amount': 500000}}

    # Patch scheduled milestone
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, scheduled_milestone_id, self.contract_token),
        {'data': data}, status=403
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': u"Can't update milestone in current (scheduled) status",
                u'location': u'body',
                u'name': u'data'
            }]
        }
    )

    # Patch first pending milestone
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, pending_milestone_id, self.contract_token),
        {'data': data}
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    milestone = response.json['data']
    self.assertEqual(milestone['status'], 'pending')
    self.assertEqual(milestone['amountPaid']['amount'], data['amountPaid']['amount'])

    # Patch second time first pending milestone
    data['amountPaid']['amount'] = 600000
    data['status'] = 'met'
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, pending_milestone_id, self.contract_token),
        {'data': data}
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    milestone = response.json['data']
    self.assertEqual(milestone['status'], data['status'])
    self.assertEqual(milestone['amountPaid']['amount'], data['amountPaid']['amount'])

    current_milestone_sequenceNumber = milestone['sequenceNumber']

    # Check status next milestone
    next_milestone_id = self.initial_data['milestones'][1]['id']
    response = self.app.get('/contracts/{}/milestones/{}'.format(contract_id, next_milestone_id))
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    milestone = response.json['data']
    next_milestone_sequenceNumber = milestone['sequenceNumber']
    self.assertEqual(milestone['amountPaid']['amount'], 0)
    self.assertEqual(milestone['status'], 'pending')
    self.assertGreater(next_milestone_sequenceNumber, current_milestone_sequenceNumber)

    # Patch third time first met milestone
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, pending_milestone_id, self.contract_token),
        {'data': data}, status=403
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': u"Can't update milestone in current (met) status",
                u'location': u'body', u'name': u'data'
            }]
        }
    )

    # Patch second pending milestone to notMet
    data['status'] = 'notMet'
    data['amountPaid']['amount'] = 600000
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}, status=422
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': [u"Milestone can't be in status 'notMet' if amountPaid.amount greater than 0"],
                u'location': u'body',
                u'name': u'status'
            }]
        }
    )

    # Patch second pending milestone to partiallyMet
    data['status'] = 'partiallyMet'
    data['amountPaid']['amount'] = 600000
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}, status=422
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': [u"Milestone can't be in status 'partiallyMet' if amountPaid.amount not greater then 0 "
                    "or not less value.amount"],
                u'location': u'body',
                u'name': u'status'
            }]
        }
    )

    # Patch second pending milestone to met
    data['status'] = 'met'
    data['amountPaid']['amount'] = 600000
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    milestone = response.json['data']
    self.assertEqual(milestone['status'], data['status'])
    self.assertEqual(milestone['amountPaid']['amount'], data['amountPaid']['amount'])

    # Patch third pending milestone to met
    next_milestone_id = self.initial_data['milestones'][2]['id']
    data['status'] = 'met'
    data['amountPaid']['amount'] = 600000
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}, status=403
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': u"The sum of milestones amountPaid.amount can't be greater than contract.value.amount",
                u'location': u'body',
                u'name': u'data'
            }]
        }
    )

    # Patch third pending milestone to met
    del data['amountPaid']
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}, status=422
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': [u"Milestone can't be in status 'met' if amountPaid.amount less than value.amount"],
                u'location': u'body',
                u'name': u'status'
            }]

        }
    )

    # Try change period.endDate
    many_days = timedelta(days=2000)
    end_date = (get_now() + many_days).isoformat()
    data = {
        'period': {'endDate': end_date}
    }
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data},
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    self.assertIs(response.json, None)

    response = self.app.get('/contracts/{}/milestones/{}'.format(contract_id, next_milestone_id))
    milestone = response.json['data']
    self.assertNotEqual(end_date, milestone['period']['endDate'])
    self.assertEqual(milestone['period'], self.initial_data['milestones'][2]['period'])

    # Try patch milestone.value when not any pending changes
    data = {'value': {'amount': 0}}
    response = self.app.patch_json(
        '/contracts/{}/milestones/{}?acc_token={}'.format(contract_id, next_milestone_id, self.contract_token),
        {'data': data}, status=403
    )
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(
        response.json,
        {
            u'status': u'error',
            u'errors': [{
                u'description': u"Contract don't have any change in 'pending' status.",
                u'location': u'body',
                u'name': u'data'
            }]
        }
    )


def successfull_patch_milestone(self):
    pass
