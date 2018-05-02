# -*- coding: utf-8 -*-
from email.header import Header
from openprocurement.api.utils import get_now


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

    # update docs for pending milestone is allowed
    response = self.app.put('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token),
        upload_files=[('file', 'name  name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertNotIn('name  name.doc', response.json["data"]["documentOf"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(milestone['id'], response.json["data"]["relatedItem"])
    # save this document id for later tests
    milestone_doc_id = doc_id

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

    # update doc (which was loaded earlier) of met milestone is forbidden
    response = self.app.put('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, milestone_doc_id, self.contract_token),
        upload_files=[('file', 'name  name.doc', 'content2')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't update document in current (met) milestone status"}])

    # get scheduled milestone - it's third one (1 - met, 2 - pending, 3 - scheduled)
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
    change = response.json['data']

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

    # update docs for scheduled milestone with pending change is allowed
    response = self.app.put('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token),
        upload_files=[('file', 'name name name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertNotIn('name name name.doc', response.json["data"]["documentOf"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(scheduled_milestone['id'], response.json["data"]["relatedItem"])

    # activate change
    response = self.app.patch_json('/contracts/{}/changes/{}?acc_token={}'.format(
        self.contract_id, change['id'], self.contract_token), {'data': {
            'status': 'active',
            'dateSigned': get_now().isoformat()}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')

    # update docs for scheduled milestone is not allowed without pending change
    response = self.app.put('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token),
        upload_files=[('file', 'name name name.doc', 'content2')], status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data",
         "description": "Can't update document to scheduled milestone without pending change"}])

    # can't load documents to spare milestone
    spare_milestone = self.initial_data['milestones'][-2]
    self.assertEqual(spare_milestone['status'], 'spare')

    response = self.app.patch_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {"data": {
            "documentOf": "milestone",
            "relatedItem": spare_milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't add document in current (spare) milestone status"}])


def milestone_document_json(self):
    # load document to "some id" milestone
    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'укр.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': '1234' * 8}}, status=422)
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

    # load docs to pending milestone is allowed
    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'укр.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': milestone['id']}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(milestone['id'], response.json["data"]["relatedItem"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    contract = self.db.get(self.contract_id)
    self.assertIn(key, contract['documents'][-1]["url"])
    self.assertIn('Signature=', contract['documents'][-1]["url"])
    self.assertIn('KeyID=', contract['documents'][-1]["url"])
    self.assertNotIn('Expires=', contract['documents'][-1]["url"])

    response = self.app.get('/contracts/{}/documents/{}'.format(
        self.contract_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(milestone['id'], response.json["data"]["relatedItem"])

    # update of docs of pending milestone is allowed
    response = self.app.put_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {'data': {
            'title': u'name.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword', }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(milestone['id'], response.json["data"]["relatedItem"])


    # set milestone's status to terminal - met for example
    response = self.app.patch_json('/contracts/{}/milestones/{}?acc_token={}'.format(
        self.contract_id, milestone['id'], self.contract_token), {'data': {
            "status": "met",
            "amountPaid": {"amount": 600000}}})
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'met')
    self.assertEqual(response.json['data']['amountPaid']['amount'], 600000)

    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'name name.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't add document in current (met) milestone status"}])

    # update of docs of met milestone is not allowed
    response = self.app.put_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {'data': {
            'title': u'name.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't update document in current (met) milestone status"}])

    # get scheduled milestone - it's third one (1 - met, 2 - pending, 3 - scheduled)
    response = self.app.get('/contracts/{}'.format(self.contract_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    scheduled_milestone = response.json['data']['milestones'][3]
    # make sure it's scheduled milestone!
    self.assertEqual(scheduled_milestone['status'], 'scheduled')

    # can't load documents for milestone in scheduled status w/o pending change
    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'укр.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': scheduled_milestone['id']}}, status=403)
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
    change = response.json['data']

    # now loading docs for scheduled milestone is allowed
    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'укр.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': scheduled_milestone['id']}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(scheduled_milestone['id'], response.json["data"]["relatedItem"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    key = response.json["data"]["url"].split('/')[-1].split('?')[0]
    contract = self.db.get(self.contract_id)
    self.assertIn(key, contract['documents'][-1]["url"])
    self.assertIn('Signature=', contract['documents'][-1]["url"])
    self.assertIn('KeyID=', contract['documents'][-1]["url"])
    self.assertNotIn('Expires=', contract['documents'][-1]["url"])

    response = self.app.get('/contracts/{}/documents/{}'.format(
        self.contract_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(u'укр.doc', response.json["data"]["title"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(scheduled_milestone['id'], response.json["data"]["relatedItem"])

    # update docs for scheduled milestone is allowed with pending change
    response = self.app.put_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {'data': {
            'title': u'name name.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword'}}, status=200)
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual(u'name name.doc', response.json["data"]["title"])
    self.assertIn('Signature=', response.json["data"]["url"])
    self.assertIn('KeyID=', response.json["data"]["url"])
    self.assertNotIn('Expires=', response.json["data"]["url"])
    self.assertEqual('milestone', response.json["data"]["documentOf"])
    self.assertEqual(scheduled_milestone['id'], response.json["data"]["relatedItem"])

    # activate change - now there is no pending changes
    response = self.app.patch_json('/contracts/{}/changes/{}?acc_token={}'.format(
        self.contract_id, change['id'], self.contract_token), {'data': {
            'status': 'active',
            'dateSigned': get_now().isoformat()}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')

    # update docs for scheduled milestone is not allowed without pending change
    response = self.app.put_json('/contracts/{}/documents/{}?acc_token={}'.format(
        self.contract_id, doc_id, self.contract_token), {'data': {
            'title': u'name name name.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword'}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data",
         "description": "Can't update document to scheduled milestone without pending change"}])

    # can't load documents to spare milestone
    spare_milestone = self.initial_data['milestones'][-2]
    self.assertEqual(spare_milestone['status'], 'spare')

    response = self.app.post_json('/contracts/{}/documents?acc_token={}'.format(
        self.contract_id, self.contract_token), {'data': {
            'title': u'укр.doc',
            'url': self.generate_docservice_url(),
            'hash': 'md5:' + '0' * 32,
            'format': 'application/msword',
            'documentOf': 'milestone',
            'relatedItem': spare_milestone['id']}}, status=403)
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't add document in current (spare) milestone status"}])
