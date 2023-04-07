# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from mindee import Client, documents
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
import json

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_ocr_fetch(self):
        mindee_client = Client(api_key="b6a50b83167b66488396421dbb1d0825")
        for move in self:
            for message in move.message_ids:
                for attachment in message.attachment_ids:
                    if "pdf" in attachment.display_name:
                        _logger.info("message : "+message.display_name)
                        _logger.info("attachment : "+attachment.display_name)
                        _logger.info(attachment.datas)
                        input_doc = mindee_client.doc_from_b64string(attachment.datas.decode(),attachment.display_name)
                        _logger.info(input_doc)
                        api_response = input_doc.parse(documents.TypeInvoiceV4)
                        _logger.info(api_response.http_response)
                        _logger.info(api_response.document)
                        partner_name = api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('supplier_name').get('value')
                        partner_id = self.env['res.partner'].search([("name","=",partner_name)],limit=1)
                        if not partner_id:
                            partner_id = self.env['res.partner'].create({
                                "name": partner_name,
                                "contact_address": api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('supplier_address').get('value'),
                            })
                        line_items = api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('line_items')
                        line_ids = [(0, 0, {"name": i.get('description'),"quantity": i.get('quantity'),"price_unit": i.get('unit_price') }) for i in line_items ]
                        move.write({
                            "partner_id" : partner_id.id,
                            "invoice_date" : api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('date').get('value'),
                            "invoice_date_due" : api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('date').get('value'),
                            "ref": api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('invoice_number').get('value'),
                            "invoice_line_ids": line_ids,
                        })
        return True
