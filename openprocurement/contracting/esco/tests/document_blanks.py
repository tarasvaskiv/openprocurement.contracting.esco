# -*- coding: utf-8 -*-
from email.header import Header


# ContractDocumentResourceTest


def contract_milestone_document(self):
    response = self.app.patch_json('/contracts/{}?acc_token={}'.format(
        self.contract_id, self.contract_token), {"data": {"status": "active"}})
    self.assertEqual(response.status, '200 OK')

    # load document to contract
    response = self.app.post('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), upload_files=[('file', str(Header(u'укр.doc', 'utf-8')), 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual(response.json["data"]["documentOf"], "contract")
    self.assertNotIn("documentType", response.json["data"])

    # try to make it milestone's document
    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {"documentOf": "milestone"}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "relatedItem", "description": ["This field is required."]}])

    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
            "documentOf": "milestone",
            "relatedItem": '1234' * 8}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "relatedItem", "description": ["relatedItem should be one of milestones"]}])

    # get correct milestone id
    response = self.app.get('/contracts/{}'.format(self.contract_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    milestone = response.json['data']['milestones'][0]
    # make sure it's pending milestone!
    self.assertEqual(milestone['status'], 'pending')

    # loading documents to pending milestone is allowed
    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
            "documentOf": "milestone",
            "relatedItem": milestone['id']}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["documentOf"], 'milestone')
    self.assertEqual(response.json["data"]["relatedItem"], milestone['id'])

    # set milestone's status to terminal - met for example
    response = self.app.patch_json('/contracts/{}/milestones/{}?acc_token={}'.format(
    	self.contract_id, milestone['id'], self.contract_token), {'data': {
    		"status": "met",
    		"amountPaid": {"amount": 600000}}})
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'met')
    self.assertEqual(response.json['data']['amountPaid']['amount'], 600000)

    # can't load documents for milestone in met status
    response = self.app.post('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), upload_files=[('file', str(Header(u'next.doc', 'utf-8')), 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'next.doc', response.json["data"]["title"])
    self.assertEqual(response.json["data"]["documentOf"], "contract")
    self.assertNotIn("documentType", response.json["data"])

    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
    		"documentOf": "milestone",
    		"relatedItem": milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't add document in current (met) milestone status"}])

    # get scheduled milestone - it's third one (1 - met, 2 - pending, else - scheduled)
    response = self.app.get('/contracts/{}'.format(self.contract_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    scheduled_milestone = response.json['data']['milestones'][3]
    # make sure it's scheduled milestone!
    self.assertEqual(scheduled_milestone['status'], 'scheduled')

    # can't load documents for milestone in scheduled status w/o pending change
    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
            "documentOf": "milestone",
            "relatedItem": scheduled_milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", 
         "description": "Can't add document to scheduled milestone without pending change"}])

    # create pending change
    response = self.app.post_json('/contracts/{}/changes?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'rationale': u'причина зміни укр',
            'rationale_en': 'change cause en',
            'rationaleTypes': ['itemPriceVariation']}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']['status'], 'pending')   

    # now loading docs for scheduled milestone is allowed
    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
            "documentOf": "milestone",
            "relatedItem": scheduled_milestone['id']}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(response.json["data"]["documentOf"], 'milestone')
    self.assertEqual(response.json["data"]["relatedItem"], scheduled_milestone['id'])
