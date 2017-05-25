# -*- coding: utf-8 -*-
from openprocurement.contracting.api.views.tenders import (
    TenderResource as BaseTenderResource
)

from openprocurement.tender.core.utils import optendersresource


@optendersresource(name='Tender credentials',
                   path='/tenders/{tender_id}/extract_credentials',
                   description="Open Contracting compatible data exchange format. See http://ocds.open-contracting.org/standard/r/master/#tender for more info")
class TenderResource(BaseTenderResource):
    """ Tender Resource """
