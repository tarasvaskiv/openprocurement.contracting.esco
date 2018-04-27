# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import timedelta

from mock import patch

from openprocurement.api.utils import get_now


def no_items_contract_change(self):
    data = deepcopy(self.initial_data)
    del data['items']
    response = self.app.post_json('/contracts', {"data": data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    self.assertEqual(contract['status'], 'active')
    self.assertNotIn('items', contract)
    tender_token = data['tender_token']

    response = self.app.patch_json('/contracts/{}/credentials?acc_token={}'.format(contract['id'], tender_token),
                                   {'data': ''})
    self.assertEqual(response.status, '200 OK')
    token = response.json['access']['token']

    response = self.app.post_json('/contracts/{}/changes?acc_token={}'.format(contract['id'], token),
                                  {'data': {'rationale': u'причина зміни укр',
                                            'rationaleTypes': ['qualityImprovement']}})
    self.assertEqual(response.status, '201 Created')
    change = response.json['data']
    self.assertEqual(change['status'], 'pending')

    response = self.app.patch_json('/contracts/{}/changes/{}?acc_token={}'.format(contract['id'], change['id'], token),
                                   {'data': {'status': 'active', 'dateSigned': get_now().isoformat()}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')

    # terminate all scheduled milestones in met
    now = get_now()
    # time travel to contract.period.endDate
    with patch('openprocurement.contracting.esco.validation.get_now') as mocked_get_now:
        contract_duration_years = self.initial_data['value']['contractDuration']['years']
        contract_duration_days = self.initial_data['value']['contractDuration']['days']
        mocked_get_now.return_value = \
            now.replace(year=now.year + contract_duration_years) + timedelta(days=contract_duration_days)
        for milestone in contract['milestones']:
            if milestone['status'] not in ['notMet', 'partiallyMet', 'met']:
                response = self.app.patch_json('/contracts/{}/milestones/{}?acc_token={}'.format(
                    contract['id'], milestone['id'], token), {'data': {
                        "amountPaid": {"amount": milestone['value']['amount']}, 'status': 'met'}})

    response = self.app.patch_json('/contracts/{}?acc_token={}'.format(contract['id'], token),
                                   {"data": {"status": "terminated"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'terminated')

    response = self.app.get('/contracts/{}'.format(contract['id']))
    self.assertNotIn('items', response.json['data'])
