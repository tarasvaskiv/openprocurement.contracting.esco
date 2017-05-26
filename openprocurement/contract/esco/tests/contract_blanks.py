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
        u'items', u'owner', u'tender_id', u'procuringEntity', u'contractType']))
    self.assertEqual(data['id'], contract['id'])
    self.assertNotEqual(data['doc_id'], contract['id'])
    self.assertEqual(data['contractID'], contract['contractID'])