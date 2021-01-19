import io
import os
import xlrd
import base64

from datetime import date, datetime
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from odoo.osv import osv


class CQImportPaymentPaynow(models.Model):
    _name = 'cq.import.payment.paynow'
    _description = 'Cq.Paynow.Payment.Model'

    _rec_name = "name_display"
    paynow_field_binary_import = fields.Binary(string="Paynow Field Binary Import")
    paynow_field_binary_name = fields.Char(string="Paynow Field Binary Name")
    paynow_detail_ids = fields.One2many('cq.master.file', 'import_id', string='Paynow Detail')
    name_display = fields.Char(string="Display Name", default="Import Paynow Payment", store=False)

    def _check_format_excel(self, file_name):
        """Check format of import file"""
        if not file_name:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    def action_create_data(self):
        val = []
        paynow_payment_obj = self.env['account.payment']

        # get reconciliation rule by query
        # query = """SELECT arm.* FROM account_reconcile_model as arm
        #                           INNER JOIN account_journal_account_reconcile_model_rel as ajc ON ajc.account_reconcile_model_id = arm.id
        #                           INNER JOIN account_journal as aj ON aj.id = ajc.account_journal_id
        #                           WHERE aj.code = 'cc'"""
        # self.env.cr.execute(query)
        # reconciliation_rule = self.env.cr.dictfetchall()
        # match_amount = reconciliation_rule[0].get('match_total_amount_param')

        for paynow_detail_id in self.paynow_detail_ids:
            # paynow_claim_amount = float(paynow_detail_id.credit_amount)
            # get invoice list that not match with any payment
            # query = """SELECT * FROM account_move WHERE id not in (SELECT invoice_id from account_invoice_payment_rel)
            #                         AND amount_total > 0
            #                         AND (%s/amount_total)*100 >= %s """
            # self.env.cr.execute(query, (paynow_claim_amount, float(match_amount),))
            # result = self.env.cr.dictfetchall()

            # extract Paynow Name for transaction description 02
            transaction_desc_02_rm_space = ' '.join(paynow_detail_id.transaction_desc_02.split())
            paynow_payment_name = transaction_desc_02_rm_space.partition("OTHER")[2]
            paynow_payment_name = paynow_payment_name.partition("SGD")[0]
            paynow_payment_name = ' '.join(paynow_payment_name.split())

            # mapping res_partner name with name which slice from transaction description 02
            # invoice = self.mapping_partner_invoice(result, paynow_payment_name)

            # filter by journal code
            journal_id = self.env['account.journal'].sudo().search([('code', '=', 'cc')]).id
            # filter by currency code
            currency_id = self.env['res.currency'].sudo().search([('name', '=', 'SGD')]).id
            # filter by payment method id
            payment_method_id = self.env['account.payment.method'].sudo().search([('payment_type', '=', 'inbound'), ('code', '=', 'manual')]).id
            # paynow payment reference
            paynow_payment_refer = f"{paynow_detail_id.payment_date},{paynow_detail_id.payment_value_date},{paynow_detail_id.transaction_desc_01}," \
                            f"{paynow_detail_id.transaction_desc_02},{paynow_detail_id.credit_amount}"

            # Add value to list then insert to account_payment
            # if invoice:
            #     val.append({
            #         'name': paynow_payment_name,
            #         'move_name': invoice.get('name'),
            #         'state': "posted",
            #         'payment_type': "inbound",
            #         'amount': paynow_detail_id.credit_amount,
            #         'payment_date': paynow_detail_id.payment_value_date,
            #         'partner_type': "customer",
            #         'journal_id': journal_id,
            #         'currency_id': currency_id,
            #         'payment_reference': paynow_payment_refer,
            #         'payment_method_id': payment_method_id,
            #         'invoice_ids': [(4, invoice.get('id'), 0)],
            #         'partner_id': invoice.get('partner_id')
            #
            #     })
            #     paynow_payment = paynow_payment_obj.create(val)
            #     paynow_detail_id.write({
            #         "status": "reconciled",
            #         "invoice_id": invoice.get('id'),
            #         "partner_id": invoice.get('partner_id'),
            #         "payment_id": paynow_payment.id
            #     })
            #
            # else:
            #     # Mapping payment with partner and keep status new
            #     partner_id = self.mapping_partner(paynow_payment_name)
            #     val.append({
            #         'name': paynow_payment_name,
            #         'state': "posted",
            #         'payment_type': "inbound",
            #         'amount': paynow_detail_id.credit_amount,
            #         'payment_date': paynow_detail_id.payment_value_date,
            #         'partner_type': "customer",
            #         'journal_id': journal_id,
            #         'currency_id': currency_id,
            #         'payment_reference': paynow_payment_refer,
            #         'payment_method_id': payment_method_id,
            #         'partner_id': partner_id
            #     })
            #     paynow_payment = paynow_payment_obj.create(val)
            #     # update info to master file record
            #     paynow_detail_id.write({
            #         "status": "reconciled",
            #         "partner_id": partner_id,
            #         "payment_id": paynow_payment.id
            #     })
            val.append({
                'name': paynow_payment_name,
                'state': "posted",
                'payment_type': "inbound",
                'amount': paynow_detail_id.credit_amount,
                'payment_date': paynow_detail_id.payment_value_date,
                'partner_type': "customer",
                'journal_id': journal_id,
                'currency_id': currency_id,
                'payment_reference': paynow_payment_refer,
                'payment_method_id': payment_method_id
            })
            paynow_payment = paynow_payment_obj.create(val)
            paynow_detail_id.write({
                "payment_id": paynow_payment.id
            })
        return{
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    """
    IMPORT DATA DETAIL
    """
    def action_import_paynow_payment(self):
        if self.paynow_field_binary_import is None:
            raise except_orm('Warning!', 'Please select a Paynow file to import')
        try:
            if not self._check_format_excel(self.paynow_field_binary_name):
                raise osv.except_osv("Warning!", ("Wrong format file. File must in type .xls or .xlsx"))
            paynow_data = base64.decodestring(self.paynow_field_binary_import)
            excel = xlrd.open_workbook(file_contents=paynow_data)
            sheet = excel.sheet_by_index(0)
            index = 1
            """
            READ FILE
            """
            while index < sheet.nrows:
                # if index == 1:
                #     payment_account_details = sheet.cell(index, 1).value
                # if index == 2:
                #     # ////////////////STRING TO DATE
                #     statement_from_date = sheet.cell(index, 1).value
                #     if statement_from_date:
                #         statefrom_date = statement_from_date.split('/')[2] + '-' + statement_from_date.split('/')[1] + '-' + statement_from_date.split('/')[0]
                #         statement_from_date = datetime.strptime(statefrom_date, '%Y-%m-%d')
                #     else:
                #         statement_from_date = None
                #
                #     # ////////////////STRING TO DATE
                #     statement_to_date = sheet.cell(index, 3).value
                #     if statement_to_date:
                #         to_date = statement_to_date.split('/')[2] + '-' + statement_to_date.split('/')[1] + '-' + statement_to_date.split('/')[0]
                #         statement_to_date = datetime.strptime(to_date, '%Y-%m-%d')
                #     else:
                #         statement_to_date = None

                if index > 2:
                    # ////////////////STRING TO DATE
                    payment_date = sheet.cell(index, 0).value
                    if payment_date:
                        paym_date = payment_date.split('-')[2] + '-' + payment_date.split('-')[1] + '-' + payment_date.split('-')[0]
                        payment_date = datetime.strptime(paym_date, '%Y-%b-%d').strftime('%Y-%m-%d')
                    else:
                        payment_date = None

                    # ////////////////STRING TO DATE
                    payment_value_date = sheet.cell(index, 1).value
                    if payment_value_date:
                        paym_value_date = payment_value_date.split('-')[2] + '-' + payment_value_date.split('-')[1] + '-' + payment_value_date.split('-')[0]
                        payment_value_date = datetime.strptime(paym_value_date, '%Y-%b-%d').strftime('%Y-%m-%d')
                    else:
                        payment_value_date = None

                    transaction_desc_01 = str(sheet.cell(index, 2).value)
                    transaction_desc_02 = str(sheet.cell(index, 3).value)
                    debit_amount = sheet.cell(index, 4).value if sheet.cell(index, 4).value else 0.00
                    credit_amount = sheet.cell(index, 5).value if sheet.cell(index, 5).value else 0.00

                    """
                    CREATE DETAIL
                    """
                    self.paynow_detail_ids.create({
                        'pnw_date': payment_date,
                        'pnw_value_date': payment_value_date,
                        'pnw_trans_desc1': transaction_desc_01,
                        'pnw_trans_desc2': transaction_desc_02,
                        'pnw_debit': debit_amount,
                        'pnw_credit': credit_amount,
                        'status': 'new',
                        'import_file_name': self.paynow_field_binary_name,
                        'import_date_time': datetime.now(),
                        'import_id': self.id
                    })
                index = index + 1
            self.paynow_field_binary_import = None
            self.paynow_field_binary_name = None
        except ValueError as err:
            raise osv.except_osv("Warning!", (err))

    # @staticmethod
    # def compute_mapping_name(partner_name: str, paynow_name: str):
    #     if partner_name == paynow_name:
    #         return True
    #     partner_name_lt = partner_name.split()
    #     partner_name_lt.sort()
    #     paynow_name_lt = paynow_name.split()
    #     paynow_name_lt.sort()
    #     if all(item in partner_name_lt for item in paynow_name_lt) or all(item in paynow_name_lt for item in partner_name_lt):
    #         return True
    #     return False
    #
    # def mapping_partner_invoice(self, list_invoice, paynow_name):
    #     for item in list_invoice:
    #         # get partner_id from invoice of account_move table
    #         partner_id = item.get('partner_id')
    #         partner_info = self.env['res.partner'].sudo().search([('id', '=', partner_id)])[0]
    #
    #         # compare res_partner name with name which slice from trans_desc_02
    #         partner_name = partner_info.name.lower()
    #         paynow_payment_name = paynow_name.lower()
    #
    #         # checking mapping result
    #         is_mapping = self.compute_mapping_name(partner_name, paynow_payment_name)
    #         if is_mapping:
    #             return item
    #         else:
    #             continue
    #     return None
    #
    # def mapping_partner(self, paynow_name):
    #     list_partner = self.env['res.partner'].sudo().search([])
    #     # get paynow name from name which slice transaction desc 02
    #     paynow_payment_name = paynow_name.lower()
    #     for item in list_partner:
    #         if item.name:
    #             is_mapping = self.compute_mapping_name(item.name.lower(), paynow_payment_name)
    #             if is_mapping:
    #                 return item.id
    #         else:
    #             continue
    #     # if not mapping with any partner, create new partner
    #     partner = self.env['res.partner'].create({
    #         "name": paynow_name
    #     })
    #     return partner.id


class MasterFile(models.Model):
    _name = 'cq.master.file'
    _description = 'CQ Master File'

    import_id = fields.Many2one('cq.import.payment.paynow', string='Import')
    invoice_id = fields.Many2one('account.move', string='Invoice', track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='always')
    payment_id = fields.Many2one('account.payment', string='Payment', track_visibility='always')
    status = fields.Selection([
        ('new', 'New'),
        ('reconciled', 'Reconciled'),
        ('canceled', 'Canceled')
    ], default='new', string='Status', readonly=False)
    import_file_name = fields.Char(string='File Name')
    import_date_time = fields.Datetime(string='Import Date Time')
    cc_individual_name = fields.Char(string='Individual Name')
    cc_claim_id = fields.Char(string='Claim ID')
    cc_nric = fields.Char(string='Individual NRIC')
    cc_course_ref_num = fields.Char(string='Course Reference Number')
    cc_course_name = fields.Char(string='Course Name')
    cc_course_start_date = fields.Date(string='Course Start Date')
    cc_disburse_date = fields.Date(string='Disbursement Date')
    cc_claim_amount = fields.Float(string='Claim Amount', digits=(10, 2))
    cc_payout_request_id = fields.Char(string='Payout Request ID')
    pnw_date = fields.Date(string='Paynow Date')
    pnw_value_date = fields.Date(string='Paynow Value Date')
    pnw_trans_desc1 = fields.Char(string='Paynow Trans Desc1')
    pnw_trans_desc2 = fields.Char(string='Paynow Trans Desc2')
    pnw_debit = fields.Float(string='Paynow Debit', digits=(10, 2))
    pnw_credit = fields.Float(string='Paynow Crefdit', digits=(10, 2))
    sfc_trans_datetime = fields.Datetime(string='SkillsFuture Credit Trans Date')
    sfc_trans_id = fields.Char(sting='Trans ID')
    sfc_last4 = fields.Char()
    sfc_status = fields.Char()
    sfc_amount = fields.Float(digits=(10, 2))
    sfc_currency = fields.Char()
    sfc_payment_mode = fields.Char()
    sfc_merchant_ref = fields.Char()
    sfc_bill_firstname = fields.Char()
    sfc_bill_lastname = fields.Char()
    sfc_phone = fields.Char()
    sfc_email = fields.Char()
    sfc_street = fields.Char()
    sfc_floor = fields.Char()
    sfc_post_code = fields.Char()
    sfc_state = fields.Char()
    sfc_country = fields.Char()
    sfc_product = fields.Char()
    sfc_product_desc = fields.Char()
    sfc_order_note = fields.Char()
