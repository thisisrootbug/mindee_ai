# -*- coding: utf-8 -*-
from odoo import models
from mindee import Client, documents
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_ocr_fetch(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('mindee_api_key')
        if not api_key:
            api_key = "b6a50b83167b66488396421dbb1d0825"
        mindee_client = Client(api_key=api_key)
        for move in self:
            for message in move.message_ids:
                for attachment in message.attachment_ids:
                    if "pdf" in attachment.display_name:
                        input_doc = mindee_client.doc_from_b64string(attachment.datas.decode(),attachment.display_name)
                        api_response = input_doc.parse(documents.TypeInvoiceV4)
                        _logger.info(api_response.document)
                        _logger.info(api_response.http_response)
                        partner_name = api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('supplier_name').get('value')
                        partner_id = self.env['res.partner'].search([("name","ilike",partner_name)],limit=1)
                        if not partner_id:
                            partner_id = self.env['res.partner'].create({
                                "name": partner_name,
                                "street": api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('supplier_address').get('value'),
                            })
                        tax = False
                        taxes = api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('taxes')
                        if taxes != []:
                            tax_rate = taxes[0].get('rate',5.0)
                            tax = self.env['account.tax'].search([("amount","=",tax_rate)],limit=1)
                            if not tax and tax_rate:
                                tax = self.env['account.tax'].create({
                                    "name": str(tax_rate)+"% Taxes",
                                    "amount": tax_rate,
                                })
                        line_items = api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('line_items')
                        if tax:
                            line_ids = [(0, 0, {"name": i.get('description'),"quantity": i.get('quantity'),"price_unit": i.get('unit_price'),"tax_ids": (6,0, [tax.id]) }) for i in line_items ]
                        else:
                            line_ids = [(0, 0, {"name": i.get('description'),"quantity": i.get('quantity'),"price_unit": i.get('unit_price')}) for i in line_items ]
                        move.write({
                            "partner_id" : partner_id.id,
                            "invoice_date" : api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('date').get('value'),
                            "invoice_date_due" : api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('date').get('value'),
                            "ref": api_response.http_response.get('document').get('inference').get('pages')[0].get('prediction').get('invoice_number').get('value'),
                            "invoice_line_ids": line_ids,
                        })
        return True
