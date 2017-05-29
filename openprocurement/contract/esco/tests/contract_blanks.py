# -*- coding: utf-8 -*-
from uuid import uuid4
from openprocurement.contract.esco.models import Contract

# ContractTest


def simple_add_esco_contract(self):
    u = Contract(self.initial_data)
    u.contractID = "UA-C"

    assert u.id == self.initial_data['id']
    assert u.doc_id == self.initial_data['id']
    assert u.rev is None

    u.store(self.db)

    assert u.id == self.initial_data['id']
    assert u.rev is not None

    fromdb = self.db.get(u.id)

    assert u.contractID == fromdb['contractID']
    assert u.doc_type == "Contract"

    u.delete_instance(self.db)

# ContractResourceTest


def create_contract_generated(self):
    data = self.initial_data.copy()
    data.update({'id': uuid4().hex, 'doc_id': uuid4().hex, 'contractID': uuid4().hex})
    response = self.app.post_json('/contracts', {'data': data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    self.assertEqual(set(contract), set([
        u'id', u'dateModified', u'contractID', u'status', u'suppliers',
        u'contractNumber', u'period', u'dateSigned', u'value', u'awardID',
        u'items', u'owner', u'tender_id', u'procuringEntity', u'contractType', u'NBUdiscountRate']))
    self.assertEqual(data['id'], contract['id'])
    self.assertNotEqual(data['doc_id'], contract['id'])
    self.assertEqual(data['contractID'], contract['contractID'])


def patch_contract_NBUdiscountRate(self):
    response = self.app.post_json('/contracts', {"data": self.initial_data})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    tender_token = self.initial_data['tender_token']
    self.assertIn('NBUdiscountRate', response.json['data'])
    self.assertEqual(contract['NBUdiscountRate'], self.initial_data['NBUdiscountRate'])
    self.assertNotEqual(response.json['data']['NBUdiscountRate'], 0.33)

    response = self.app.patch_json('/contracts/{}/credentials?acc_token={}'.format(contract['id'], tender_token),
                                   {'data': ''})
    self.assertEqual(response.status, '200 OK')
    token = response.json['access']['token']

    # NBUdiscountRate field forbidden for patch
    response = self.app.patch_json('/contracts/{}?acc_token={}'.format(contract['id'], token),
                                   {'data': {'NBUdiscountRate': 0.33}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json, None)

    response = self.app.get('/contracts/{}'.format(contract['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['NBUdiscountRate'], self.initial_data['NBUdiscountRate'])

    # check NBUdiscountRate patch for teminated contract
    response = self.app.patch_json('/contracts/{}?acc_token={}'.format(contract['id'], token),
                                   {"data": {"status": "terminated",
                                             "amountPaid": {"amount": 100500},
                                             "terminationDetails": "sink"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'terminated')
    self.assertEqual(response.json['data']['amountPaid']['amount'], 100500)
    self.assertEqual(response.json['data']['terminationDetails'], 'sink')

    response = self.app.patch_json('/contracts/{}?acc_token={}'.format(contract['id'], token),
                                   {'data': {'NBUdiscountRate': 0.33}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')

    response = self.app.get('/contracts/{}'.format(contract['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['NBUdiscountRate'], self.initial_data['NBUdiscountRate'])
