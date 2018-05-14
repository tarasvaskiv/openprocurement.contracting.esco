# -*- coding: utf-8 -*-
import json
import os

import openprocurement.contracting.esco.tests.base as base_test

from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

from mock import patch
from openprocurement.api.models import get_now
from openprocurement.api.tests.base import PrefixedRequestClass
from openprocurement.contracting.esco.tests.base import BaseContractWebTest, test_contract_data
from webtest import TestApp


class DumpsTestAppwebtest(TestApp):
    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = "api-sandbox.openprocurement.org"
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                        'DATA:\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8')
                    )
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write(
                        json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8')
                    )
                except:
                    pass
            self.file_obj.write("\n\n")
        return resp


class ContractResourceTest(BaseContractWebTest):

    initial_data = test_contract_data
    docservice = True

    def setUp(self):
        self.app = DumpsTestAppwebtest("config:tests.ini", relative_to=os.path.dirname(base_test.__file__))
        self.app.RequestClass = PrefixedRequestClass
        self.app.authorization = ('Basic', ('broker', ''))
        self.couchdb_server = self.app.app.registry.couchdb_server
        self.db = self.app.app.registry.db
        tender_file_path = "{}/data/tender-contract-complete.json".format(os.path.dirname(base_test.__file__))
        with open(tender_file_path, 'r') as f:
            tender_data = json.loads(f.read())
        tender_data['contracts'][0]['dateSigned'] = test_contract_data["dateSigned"]
        tender_data['contracts'][0]['period']['startDate'] = test_contract_data["period"]["startDate"]
        tender_data['contracts'][0]['period']['endDate'] = test_contract_data["period"]["endDate"]
        second_item = deepcopy(test_contract_data['items'][0])
        second_item['id'] = uuid4().hex
        tender_data['items'].append(second_item)
        self.initial_data['items'].append(second_item)
        tender_data['doc_type'] = 'Tender'
        tender_data['owner_token'] = uuid4().hex
        tender_data['_id'] = tender_data['id']
        self.db.save(tender_data)
        self.tender_id = tender_data['id']
        self.tender_token = tender_data['owner_token']
        self.contract_id = tender_data['contracts'][0]['id']
        if self.docservice:
            self.setUpDS()
            # self.app.app.registry.docservice_url = 'http://localhost'
            self.app.app.registry.docservice_url = 'http://public.docs-sandbox.openprocurement.org'

    def tearDown(self):
        self.couchdb_server.delete(self.db.name)

    def test_docs(self):
        request_path = '/contracts'

        #### Exploring basic rules
        # Empty contracts listing
        with open('docs/source/tutorial/contracts-listing-0.http', 'w') as self.app.file_obj:
            self.app.authorization = None
            response = self.app.get(request_path)
            self.assertEqual(response.status, '200 OK')
            self.app.file_obj.write("\n")

        # Contract in the tender system
        with open('docs/source/tutorial/example_contract.http', 'w') as self.app.file_obj:
            response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, self.contract_id))

        # Creating contract in contract system (i.e. simulate contracting databridge sync actions)
        self.create_contract()

        # Contract in the contract system
        # Getting contract
        self.app.authorization = None
        with open('docs/source/tutorial/contract-view.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}'.format(self.contract_id))
            self.assertEqual(response.status, '200 OK')
            contract = response.json['data']
            self.assertEqual(contract['status'], 'active')

        # Getting access
        self.app.authorization = ('Basic', ('broker', ''))
        with open('docs/source/tutorial/contract-credentials.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/credentials?acc_token={}'.format(self.contract_id, self.initial_data['tender_token'])
            )
            self.assertEqual(response.status, '200 OK')
        self.app.get(request_path)
        self.contract_token = response.json['access']['token']

        # Lets view contracts
        response = self.app.get(request_path)
        with open('docs/source/tutorial/contracts-listing-1.http', 'w') as self.app.file_obj:
            response = self.app.get(request_path)
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(len(response.json['data']), 1)

        # Modifying contract

        # Submitting contract change
        # add contract change
        with open('docs/source/tutorial/add-contract-change.http', 'w') as self.app.file_obj:
            response = self.app.post_json(
                '/contracts/{}/changes?acc_token={}'.format(self.contract_id, self.contract_token),
                {
                    'data': {
                        'rationale': u'Опис причини змін контракту',
                        'rationale_en': 'Contract change cause',
                        'rationaleTypes': ['volumeCuts', 'priceReduction']
                    }
                }
            )
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            change = response.json['data']

        # view contract change
        with open('docs/source/tutorial/view-contract-change.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}/changes/{}'.format(self.contract_id, change['id']))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data']['id'], change['id'])

        # edit change while has status pending
        with open('docs/source/tutorial/patch-contract-change.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/changes/{}?acc_token={}'.format(self.contract_id, change['id'], self.contract_token),
                {'data': {'rationale': u'Друга і третя поставка має бути розфасована'}}
            )
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            change = response.json['data']

        # add contract change document
        with open('docs/source/tutorial/add-contract-change-document.http', 'w') as self.app.file_obj:
            response = self.app.post(
                '/contracts/{}/documents?acc_token={}'.format(self.contract_id, self.contract_token),
                upload_files=[('file', 'contract_changes.doc', 'content')]
            )
            self.assertEqual(response.status, '201 Created')
            self.assertEqual(response.content_type, 'application/json')
            doc_id = response.json["data"]['id']

        with open('docs/source/tutorial/set-document-of-change.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/documents/{}?acc_token={}'.format(self.contract_id, doc_id, self.contract_token),
                {"data": {"documentOf": "change", "relatedItem": change['id']}}
            )
            self.assertEqual(response.status, '200 OK')

        # updating contract properties
        # get contract
        response = self.app.get('/contracts/{}'.format(self.contract_id))
        self.assertEqual(len(response.json['data']['milestones']), 8)

        with open('docs/source/tutorial/contracts-patch.http', 'w') as self.app.file_obj:
            custom_period_end_date = (get_now() + timedelta(days=390)).isoformat()
            response = self.app.patch_json(
                '/contracts/{}?acc_token={}'.format(self.contract_id, self.contract_token),
                {"data": {"period": {'endDate': custom_period_end_date}}}
            )
            self.assertEqual(response.status, '200 OK')

        self.assertEqual(len(response.json['data']['milestones']), 2)
        milestones = response.json['data']['milestones']
        scheduled_milestone_id = milestones[1]['id']
        self.assertEqual(response.json['data']['period']['endDate'], custom_period_end_date)

        # update item
        with open('docs/source/tutorial/update-contract-item.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/contracts/{}?acc_token={}'.format(self.contract_id, self.contract_token),
                                           {"data": {"items": [{'quantity': 2}, {}]}, })
            self.assertEqual(response.status, '200 OK')
            item2 = response.json['data']['items'][0]
            self.assertEqual(item2['quantity'], 2)

        # delete item
        with open('docs/source/tutorial/delete-contract-item.http', 'w') as self.app.file_obj:
            response = self.app.patch_json('/contracts/{}?acc_token={}'.format(self.contract_id, self.contract_token),
                {"data": {"items": [item2]}, })
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(len(response.json['data']['items']), 1)

        # Change value in scheduled milestone
        with open('docs/source/tutorial/update-contract-milestone.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/milestones/{}?acc_token={}'.format(self.contract_id, scheduled_milestone_id,
                                                                  self.contract_token),
                {'data': {'value': {'amount': 100}}}
            )
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.json['data']['value']['amount'], 100)

        # apply contract change
        with open('docs/source/tutorial/apply-contract-change.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/changes/{}?acc_token={}'.format(self.contract_id, change['id'], self.contract_token),
                {'data': {'status': 'active', 'dateSigned': get_now().isoformat()}}
            )
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')

        with open('docs/source/tutorial/view-all-contract-changes.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}/changes'.format(self.contract_id))
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(len(response.json['data']), 1)

        with open('docs/source/tutorial/view-contract.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}'.format(self.contract_id))
            self.assertEqual(response.status, '200 OK')
            self.assertIn('changes', response.json['data'])

        # Uploading documentation
        with open('docs/source/tutorial/upload-contract-document.http', 'w') as self.app.file_obj:
            response = self.app.post(
                '/contracts/{}/documents?acc_token={}'.format(self.contract_id, self.contract_token),
                upload_files=[('file', u'contract.doc', 'content')]
            )

        with open('docs/source/tutorial/contract-documents.http', 'w') as self.app.file_obj:
            response = self.app.get(
                '/contracts/{}/documents?acc_token={}'.format(self.contract_id, self.contract_token)
            )

        with open('docs/source/tutorial/upload-contract-document-2.http', 'w') as self.app.file_obj:
            response = self.app.post(
                '/contracts/{}/documents?acc_token={}'.format(self.contract_id, self.contract_token),
                upload_files=[('file', u'contract_additional_docs.doc', 'additional info')]
            )

        doc_id = response.json['data']['id']

        with open('docs/source/tutorial/upload-contract-document-3.http', 'w') as self.app.file_obj:
            response = self.app.put(
                '/contracts/{}/documents/{}?acc_token={}'.format(self.contract_id, doc_id, self.contract_token),
                upload_files=[('file', 'contract_additional_docs.doc', 'extended additional info')]
            )

        with open('docs/source/tutorial/get-contract-document-3.http', 'w') as self.app.file_obj:
            response = self.app.get(
                '/contracts/{}/documents/{}?acc_token={}'.format(self.contract_id, doc_id, self.contract_token)
            )

        # Finalize contract
        # view all contract milestones
        with open('docs/source/tutorial/contract-all-milestones.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}/milestones'.format(self.contract_id))
            self.assertEqual(len(response.json['data']), 2)

        # terminate milestones
        with open('docs/source/tutorial/terminate-contract-milestone-1.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}/milestones/{}?acc_token={}'.format(self.contract_id, milestones[0]['id'],
                                                                  self.contract_token),
                {'data': {'amountPaid': {'amount': 0}, 'status': 'met'}}
            )

        # terminate second milestone with time travel
        now = get_now()
        with patch('openprocurement.contracting.esco.validation.get_now') as mocked_get_now:
            contract_duration_years = self.initial_data['value']['contractDuration']['years']
            contract_duration_days = self.initial_data['value']['contractDuration']['days']
            mocked_get_now.return_value = \
                now.replace(year=now.year + contract_duration_years) + timedelta(days=contract_duration_days)
            response = self.app.patch_json(
                '/contracts/{}/milestones/{}?acc_token={}'.format(self.contract_id, milestones[1]['id'],
                                                                  self.contract_token),
                {'data': {'amountPaid': {'amount': 100}, 'status': 'met'}}
            )

        # view contract with completed milestones
        with open('docs/source/tutorial/contract-with-completed-milestones.http', 'w') as self.app.file_obj:
            response = self.app.get('/contracts/{}'.format(self.contract_id))
            self.assertEqual(response.json['data']['value']['amount'], response.json['data']['amountPaid']['amount'])

        # finalize contract
        with open('docs/source/tutorial/contract-termination.http', 'w') as self.app.file_obj:
            response = self.app.patch_json(
                '/contracts/{}?acc_token={}'.format(self.contract_id, self.contract_token),
                {"data": {"status": "terminated"}}
            )
            self.assertEqual(response.status, '200 OK')
