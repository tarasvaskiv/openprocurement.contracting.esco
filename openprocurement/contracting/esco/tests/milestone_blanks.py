# -*- coding: utf-8 -*-
def listing_milestones(self):
    response = self.app.get('/contracts/{}/milestones'.format(self.contract['id']))
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    data = response.json['data']
    self.assertEqual(len(data), 16)
    sequenceNumber = 1
    for milestone in data:
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
