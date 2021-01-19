# def invoice_export_excel_zipfile(self, inv_dtls, user_name):
    #     # create workbook
    #     wb = Workbook()
    #     # add sheet to the workbook
    #     excel_sheet = wb.active
    #     excel_sheet.title = "InvoiceDetail"
    #
    #     # define title column
    #     excel_sheet.cell(row=1, column=1).value = 'Invoice Number'
    #     excel_sheet.cell(row=1, column=2).value = 'Date'
    #     excel_sheet.cell(row=1, column=3).value = 'Due Date'
    #     excel_sheet.cell(row=1, column=4).value = 'Referrence'
    #     excel_sheet.cell(row=1, column=5).value = 'Course Time Detail'
    #     excel_sheet.cell(row=1, column=6).value = 'Customer'
    #     excel_sheet.cell(row=1, column=7).value = 'Address1'
    #     excel_sheet.cell(row=1, column=8).value = 'Address2'
    #     excel_sheet.cell(row=1, column=9).value = 'Postal Code'
    #     excel_sheet.cell(row=1, column=10).value = 'Phone'
    #     excel_sheet.cell(row=1, column=11).value = 'Email'
    #     excel_sheet.cell(row=1, column=12).value = 'UEN Number'
    #     excel_sheet.cell(row=1, column=13).value = 'Currency'
    #     excel_sheet.cell(row=1, column=14).value = "Subtotal Amount"
    #     excel_sheet.cell(row=1, column=15).value = "Tax Amount"
    #     excel_sheet.cell(row=1, column=16).value = "Total Amount"
    #
    #     # write data to excel file
    #     index = 2
    #     for inv_dtl in inv_dtls:
    #         currency_name = self.env['res.currency'].sudo().search([('id', '=', inv_dtl.currency_id.id)]).name
    #         # get data from res_partner
    #         cust_info = self.env['res.partner'].sudo().search([('id', '=', inv_dtl.partner_id.id)])
    #         cust_name = cust_info.name
    #         cust_addr1 = cust_info.street
    #         cust_addr2 = cust_info.street2
    #         cust_postalcode = cust_info.zip
    #         cust_email = cust_info.email
    #         cust_mobile = cust_info.mobile
    #         cust_uen = cust_info.l10n_sg_unique_entity_number
    #
    #         excel_sheet.cell(row=index, column=1).value = inv_dtl.name
    #         excel_sheet.cell(row=index, column=2).value = inv_dtl.invoice_date
    #         excel_sheet.cell(row=index, column=3).value = inv_dtl.invoice_date_due
    #         excel_sheet.cell(row=index, column=4).value = inv_dtl.ref
    #         excel_sheet.cell(row=index, column=5).value = inv_dtl.narration
    #         excel_sheet.cell(row=index, column=6).value = cust_name
    #         excel_sheet.cell(row=index, column=7).value = cust_addr1
    #         excel_sheet.cell(row=index, column=8).value = cust_addr2
    #         excel_sheet.cell(row=index, column=9).value = cust_postalcode
    #         excel_sheet.cell(row=index, column=10).value = cust_email
    #         excel_sheet.cell(row=index, column=11).value = cust_mobile
    #         excel_sheet.cell(row=index, column=12).value = cust_uen
    #         excel_sheet.cell(row=index, column=13).value = currency_name
    #         excel_sheet.cell(row=index, column=14).value = inv_dtl.amount_untaxed_signed
    #         excel_sheet.cell(row=index, column=15).value = inv_dtl.amount_tax_signed
    #         excel_sheet.cell(row=index, column=16).value = inv_dtl.amount_total_signed
    #         index += 1
    #
    #     # save file with password protection
    #     excel_name = f'INV_{date.today().strftime("%Y%m%d")}.xlsx'
    #     wb.save(excel_name)
    #     wb.close()
    #
    #     excel_password = f'Odoo#{date.today().strftime("%Y%m%d")}{user_name}'
    #     filename_from = f"/home/anthony/odoo-invoice-master/odoo-invoice/{excel_name}"
    #     filename_to = f"/home/anthony/odoo-invoice-master/odoo-invoice/myzip.zip"
    #     compression_level = 4
    #     pyminizip.compress(filename_from, None, filename_to, "123456", int(compression_level))


invoice_mailed = fields.Boolean("Is Mailed", default=False, copy=False, help="It indicates that the nvoice has been mailed.")

def mass_selected_invoice_approval_by_email(self):
    request_username = self.env.user.name
    inv_dtls = self
    mail_temp = self.env.ref('cq_invoice.mail_template_data_mass_invoice_approval')
    for inv_dtl in inv_dtls:
        for user in inv_dtl.assignee_user_ids:
            mail_temp.with_context(to_user=user).send_mail(inv_dtl.id, force_send=True)



<!--Add Selected Invoice for Approval-->
    <record id="action_mass_selected_invoice_for_approval_by_email" model="ir.actions.server" >
        <field name="name">Selected Invoices For Approval</field>
        <field name="model_id" ref="account.model_account_move"/>
        <field name="binding_model_id" ref="account.model_account_move" />
        <field name="binding_view_types">list</field>
        <field name="state">code</field>
        <field name="code">
            if records:
                action = records.mass_selected_invoice_approval_by_email()
        </field>
    </record>