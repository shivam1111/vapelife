#!/usr/bin/env python
from openerp import models, fields, api, _
from config import fedex_config
from openerp.exceptions import except_orm,Warning
import logging
import binascii
import fedex_lists
from fedex.services.ship_service import FedexProcessShipmentRequest
import openerp.addons.decimal_precision as dp
import time
from openerp.exceptions import ValidationError
from pyPdf import PdfFileWriter, PdfFileReader
import tempfile
import base64
import os


class create_shipment(models.Model):
    _name = "create.shipment.fedex"
    _description = "Creates Shipment"
    _order="date desc"
    @api.multi
    @api.model
    def print_label(self):
        if self.label_image_type == 'PNG':
            l =  self.env['report'].get_action(self,'jjuice_fedex.report_print_label')
            return{
                     'type': 'ir.actions.report.xml',
                     'report_name': 'jjuice_fedex.report_print_label',
                     'datas': None,
                     'report_type': 'qweb-pdf',
                     'nodestroy' : True,
                     'active_ids':[self.id],
                     'context':self._context
                    }
        elif self.label_image_type == 'PDF':
            self = self.with_context(print_pdf=True)
            return {
                    'type':'ir.actions.client',
                    'tag':'print.shipment',
                    'context':self._context
                    }
    
    
    def output_add_page(self,input,output):
        pgcnt=input.getNumPages()
        for i in range(0,pgcnt):
            output.addPage(input.getPage(i))
        return output
    
    def generate_pdf_file(self,cr,uid,docids,reportname,options,context=None):
        #This method transfers the binary data and fetches state of the picking  
        res = {}
        assert len(docids) == 1 # This method handles single record at a time
        shipment = self.browse(cr,uid,docids[0],context)
        if shipment.label_image_type == 'PNG':
            report_obj = self.pool.get('report')
            pdf = report_obj.get_pdf(cr, uid, docids, reportname, data=options, context=context)
            output_base64 = pdf.encode("base64")
            res.update({
                        'base64':output_base64,
                        'picking_state':shipment.picking_state
                        })
        if shipment.label_image_type == 'PDF': #working
            output = PdfFileWriter()
            for j in shipment.package_ids:
                #Create a temp file
                with tempfile.TemporaryFile() as fd:
                    data  = base64.decodestring(j.label)
                    fd.write(data)
                    fd.seek(0)
                    input = PdfFileReader(fd)
                    output = self.output_add_page(input,output)
                    output_write,temp_path = tempfile.mkstemp()
                    with  tempfile.TemporaryFile() as file_out:
                        output.write(file_out)
                        file_out.seek(0)
                        output_base64 = file_out.read().encode("base64")
                        fd.close()
                        file_out.close()
            res.update({
                        'base64':output_base64,
                        'picking_state':shipment.picking_state
                        })            
        return res
        
    
    @api.multi
    def transfer_picking(self):
        if self.picking_id:
            res = self.picking_id.do_enter_transfer_details()
            picking_id = res.get('res_id',False)
            stock_obj =self.env['stock.transfer_details'].search([('id','=',picking_id)])
            stock_obj.number = self.tracking_number
            return res
        
    @api.model
    def _get_default_account_id(self):
        return self.env['fedex.account'].search([('is_primary','=',True)])
    
    @api.model
    def default_get(self,fields_list):
        res= super(create_shipment,self).default_get(fields_list)
        user_obj = self.env['res.users'] 
        company = user_obj._get_company()
        user = user_obj.search([('id','=',self._uid)])
        company_obj = self.env['res.company'].search([('id','=',company)])
        res.update({
                    'from_person_name':'JJuice LLC',
                    'from_company_name':company_obj.partner_id.name,
                    'from_phone_number':company_obj.phone,
                    'from_street1':company_obj.street,
                    'from_street2':company_obj.street2,
                    'from_city':company_obj.city,
                    'from_state_code':company_obj.state_id.id,
                    'from_country':company_obj.country_id.id,
                    'from_postal_code':company_obj.zip,
                    'from_residential':company_obj.partner_id.is_residential,
                    })
        return res
        
    @api.one
    @api.depends('commodity_lines',
                 'commodity_lines.quantity',
                 'commodity_lines.unit_price'
                 )    
    def _compute_total_customs(self):
        total = 0.00
        for i in self.commodity_lines:
            total = total + i.customs_value
        self.custom_value = total
            
    @api.multi
    def update_all_status(self):
        for i in self.package_ids:
            i.track_shipment()
            
    @api.depends()
    def _compute_total_cost(self):
        if self.is_shipment_rating_charge:
            self.total_cost = self.shipment_rating_charge
        else:
            total = 0.00
            for i in self.package_ids:
                total += i.cost
            self.total_cost = total
        
    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].get('create.shipment.fedex') or '/'
        return super(create_shipment,self).create(vals)
    
    @api.model
    def create_rate_request_from_shipment(self):
        rate_request = self.env['rate.fedex.request']
        rate = rate_request.create({
                             'dropoff_type':self.dropoff_type,
                             'service_type':self.service_type,
                             'packaging_type':self.packaging_type,
                             'include_duties':self.include_duties,
                             'payor':self.payor,
                             'from_country':self.from_country.id,
                             'from_postal_code':self.from_postal_code,
                             'from_residential':self.from_residential,
                             'to_country':self.to_country.id,
                             'to_postal_code':self.to_postal_code,
                             'to_residential':self.to_residential,
                             'special_services_type':self.special_services_type,
                             'cod_currency':self.cod_currency,
                             'cod_collection_type':self.cod_collection_type
                             })        
        package = self.env['fedex.package']
        
        #Creating rate request packages
        for i in self.package_ids:
            package.create({
                             'length':i.length,
                             'width':i.width,
                             'cod_amount':i.cod_amount,
                             'height':i.height,
                             'dim_units':i.dim_units,
                             'dimension':i.dimension,
                             'request_id':rate.id,
                             'weight':i.weight,
                             'units':i.units,
                             'physical_packaging':i.physical_packaging,
                             'group_package_count':1
                            })
        
        if self.to_country_code != 'US': #working
            commodity = self.env['rate.commodity.package']
            rate.customs_currency = self.custom_currency
            for i in self.commodity_lines:
                commodity.create({
                                  'request_id':rate.id,
                                  'name':i.name,
                                  'description':i.description,
                                  'number_of_peices':i.number_of_peices,
                                  'country_of_manufacture':i.country_of_manufacture.id,
                                  'quantity':i.quantity,
                                  'quantity_units':i.quantity_units,
                                  'weight':i.weight,
                                  'weight_unit':i.weight_unit,
                                  'unit_price':i.unit_price,
                                  'customs_value':i.customs_value,
                                  'harmonized_code':i.harmonized_code
                                  })
        return rate
            
    @api.one
    @api.model
    def rate_request(self):
        rate = self.create_rate_request_from_shipment()
#         {'msg': [(FEDEX_GROUND, USD, 99.6)], 'type': 'response'}
        res = rate._get_rates_fedex()
        status = ''
        if res.get('type',False) == 'response':
            for i in res.get('msg',[]):
                status = status + i[0] + " = " + i[1] + " %s\n"%i[2]
        elif res.get('type',False) == 'error':
            status = res.get('msg','')
        self.rate_status = status

    @api.onchange('recipient_id')
    def onchange_recipient_id(self):
        if self.recipient_id:
            self.to_person_name = self.recipient_id.name
            self.to_company_name = self.recipient_id.is_company and self.recipient_id.name or self.recipient_id.parent_id.name
            self.to_phone_number = self.recipient_id.phone
            self.to_street1 = self.recipient_id.street
            self.to_street2 = self.recipient_id.street2
            self.to_city = self.recipient_id.city
            self.to_state_code = self.recipient_id.state_id.id
            self.to_country = self.recipient_id.country_id.id
            self.to_postal_code = self.recipient_id.zip 
            self.to_residential = self.recipient_id.is_residential
    
    @api.multi    
    def track_shipment(self):
        track = self.env['track.fedex.shipment'].create({
                                                         'number':self.tracking_number
                                                         })
        status = ''
        msg = track.track_shipment_number()
        if msg.get('type',False) == 'error':
            self.status = "Error Code:%s"%msg.get('code',False) + "\n" + msg.get('msg','')
        elif msg.get('type',False) == 'response':
            for i in msg.get('msg',[]):
                 status = i[1]
            self.status = status
        
    @api.multi
    def retry_shipment(self):
        self.state = 'draft'
    
    @api.multi
    def review_confirm_shipment(self):
        compose_form = self.env.ref('jjuice_fedex.create_shipment_form2', False)
        return {
            'name': _('Confirm Shipment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'res_model': 'create.shipment.fedex',
            'target': 'new',
            'nodestroy':True,
            'res_id':self.id,
            'context':self._context
           }                    
            
    @api.multi
    def create_shipment(self):
        if len(self.package_ids) == 0:
            raise except_orm(_('Empty Package Lines!'),
                _('The package line items are empty'))
        if self.account_id:
            config_object = fedex_config(
                             key=self.account_id.key,
                             password=self.account_id.password,
                             account_number=self.account_id.account_number,
                             meter_number=self.account_id.meter_number,
                             freight_account_number=self.account_id.freight_account_number,
                             use_test_server=self.account_id.user_test_server,
                             )
            
            # Set this to the INFO level to see the response from Fedex printed in stdout.
            logging.basicConfig(level=logging.DEBUG)
            shipment = FedexProcessShipmentRequest(config_object.CONFIG_OBJ)
            shipment.RequestedShipment.DropoffType = self.dropoff_type
            shipment.RequestedShipment.ServiceType = self.service_type
            shipment.RequestedShipment.PackagingType = self.packaging_type
            # Shipper contact info.
            shipment.RequestedShipment.Shipper.Contact.PersonName = self.from_person_name
            shipment.RequestedShipment.Shipper.Contact.CompanyName = self.from_company_name
            shipment.RequestedShipment.Shipper.Contact.PhoneNumber = self.from_phone_number
            
            # Shipper address.
            from_address = []
            if self.from_street1:
                from_address.append(self.from_street1)
            if self.from_street2:
                from_address.append(self.from_street2)                
            if self.from_street3:
                from_address.append(self.from_street3)                                
            shipment.RequestedShipment.Shipper.Address.StreetLines = from_address
            shipment.RequestedShipment.Shipper.Address.City = self.from_city
            shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = self.from_state_code.code
            shipment.RequestedShipment.Shipper.Address.PostalCode = self.from_postal_code
            shipment.RequestedShipment.Shipper.Address.CountryCode = self.from_country.code
            shipment.RequestedShipment.Shipper.Address.Residential = self.from_residential
            
            # Recipient contact info.
            shipment.RequestedShipment.Recipient.Contact.PersonName = self.to_person_name
            shipment.RequestedShipment.Recipient.Contact.CompanyName = self.to_company_name
            shipment.RequestedShipment.Recipient.Contact.PhoneNumber = self.to_phone_number
            
            # Recipient address
            to_address = []
            if self.to_street1:
                to_address.append(self.to_street1)
            if self.to_street2:
                to_address.append(self.to_street2)                
            if self.to_street3:
                to_address.append(self.to_street3)                                            
            
            #Recipient
            shipment.RequestedShipment.Recipient.Address.StreetLines = to_address
            shipment.RequestedShipment.Recipient.Address.City = self.to_city
            shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = self.to_state_code.code
            shipment.RequestedShipment.Recipient.Address.PostalCode = self.to_postal_code
            shipment.RequestedShipment.Recipient.Address.CountryCode = self.to_country.code
            shipment.RequestedShipment.Recipient.Address.Residential = self.to_residential
            
            #Sold TO
            shipment.RequestedShipment.SoldTo.Contact.PersonName = self.to_person_name
            shipment.RequestedShipment.SoldTo.Contact.CompanyName = self.to_company_name
            shipment.RequestedShipment.SoldTo.Contact.PhoneNumber = self.to_phone_number
            shipment.RequestedShipment.SoldTo.Address.StreetLines = to_address
            shipment.RequestedShipment.SoldTo.Address.City = self.to_city
            shipment.RequestedShipment.SoldTo.Address.StateOrProvinceCode = self.to_state_code.code
            shipment.RequestedShipment.SoldTo.Address.PostalCode = self.to_postal_code
            shipment.RequestedShipment.SoldTo.Address.CountryCode = self.to_country.code
            shipment.RequestedShipment.SoldTo.Address.Residential = self.to_residential            
            
            shipment.RequestedShipment.EdtRequestType = self.include_duties
            shipment.RequestedShipment.ShippingChargesPayment.Payor.ResponsibleParty.AccountNumber = self.account_id.account_number
            shipment.RequestedShipment.ShippingChargesPayment.PaymentType = self.payor
            shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
            shipment.RequestedShipment.LabelSpecification.ImageType = self.label_image_type
            shipment.RequestedShipment.LabelSpecification.LabelStockType = self.label_stock_type
            shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = self.label_printing_orientation
            master_tracking_number = False # False for master document
            TrackingIdType = False # False for master document
            sequence_no = 0
            ir_attachment = self.env['ir.attachment']
            
            # Special Services COD
#             if self.special_services_type == 'COD':
#                 shipment.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes.append("COD")
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.CodCollectionAmount.Amount = self.cod_amount
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.CodCollectionAmount.Currency = self.cod_currency
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.CollectionType = self.cod_collection_type
#                 if self.cod_collection_type != 'CASH':
#                     shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Contact.PersonName = self.institution_person_name or ''
#                     shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Contact.CompanyName = self.institution_company_name or ''
#                     shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Contact.PhoneNumber = self.institution_phone_number or ''
#                     shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.StreetLines.append(self.institution_street or '')
#                     shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.StreetLines.append(self.institution_street2 or '')
#                     if self.institution_city:
#                         shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.City = self.institution_city
#                     if self.institution_state_code:
#                         shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.StateOrProvinceCode = self.institution_state_code.code
#                     if self.institution_postal_code:
#                         shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.PostalCode = self.institution_postal_code
#                     if self.institution_country:
#                         shipment.RequestedShipment.SpecialServicesRequested.CodDetail.FinancialInstitutionContactAndAddress.Address.CountryCode = self.institution_country.code
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.RemitToName = self.remit_name    
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.AddTransportationChargesDetail.ChargeBasis = "NET_CHARGE"
#                 shipment.RequestedShipment.SpecialServicesRequested.CodDetail.AddTransportationChargesDetail.ChargeBasisLevel = "CURRENT_PACKAGE"
            
            if self.to_country_code != 'US': #working
                CustomsClearanceDetail  = shipment.create_wsdl_object_of_type('CustomsClearanceDetail')
                DutiesPayment  = shipment.create_wsdl_object_of_type('Payment')
                DutiesPayment.PaymentType = self.payor
                DutiesPayment.Payor.ResponsibleParty.AccountNumber = self.account_id.account_number
                DutiesPayment.Payor.ResponsibleParty.Address.StreetLines = from_address
                DutiesPayment.Payor.ResponsibleParty.Address.City = self.from_city
                DutiesPayment.Payor.ResponsibleParty.Address.StateOrProvinceCode = self.from_state_code.code
                DutiesPayment.Payor.ResponsibleParty.Address.PostalCode = self.from_postal_code
                DutiesPayment.Payor.ResponsibleParty.Address.CountryCode = self.from_country.code
                DutiesPayment.Payor.ResponsibleParty.Address.Residential = self.from_residential
                CustomsClearanceDetail.DutiesPayment = DutiesPayment
                CustomsClearanceDetail.DocumentContent = self.document_type            
                CustomsClearanceDetail.CustomsValue.Currency =self.custom_currency
                CustomsClearanceDetail.CustomsValue.Amount = self.custom_value
                CustomsClearanceDetail.ExportDetail.B13AFilingOption = self.B13AFilingOption
                broker_detail = shipment.create_wsdl_object_of_type("BrokerDetail")
                if self.is_broker:
                    broker_detail.Type = self.broker_type
                    broker_party = shipment.create_wsdl_object_of_type("Party")
                    if self.broker_account_number:
                        broker_party.AccountNumber = self.broker_account_number
                    if self.broker_name:
                        broker_party.Contact.PersonName = self.broker_name
                    if self.broker_company_name:
                        broker_party.Contact.CompanyName = self.broker_company_name
                    if self.broker_phone_number:
                        broker_party.Contact.PhoneNumber = self.broker_phone_number
                    broker_address = []
                    if self.broker_street:
                        broker_address.append(self.broker_street)
                    if self.broker_street2:
                        broker_address.append(self.broker_street2)                
                    broker_party.Address.StreetLines = broker_address
                    if self.broker_city:
                        broker_party.Address.City = self.broker_city
                    if self.broker_state_code:
                        broker_party.Address.StateOrProvinceCode = self.broker_state_code.code
                    if self.broker_postal_code:
                        broker_party.Address.PostalCode = self.broker_postal_code
                    if self.broker_country:
                        broker_party.Address.CountryCode = self.broker_country.code
                    broker_detail.Broker = broker_party
                CustomsClearanceDetail.Brokers.append(broker_detail)
                commodity_list = []
                CommercialInvoice = shipment.create_wsdl_object_of_type('CommercialInvoice')
                CommercialInvoice.Comments = self.commercial_invoice_comment
                CommercialInvoice.FreightCharge.Amount = self.freight_amount
                CommercialInvoice.FreightCharge.Currency = self.freight_currency
                CommercialInvoice.TaxesOrMiscellaneousCharge.Amount = self.tax_miscellaneous_amount
                CommercialInvoice.TaxesOrMiscellaneousCharge.Currency = self.tax_miscellaneous_currency
                CommercialInvoice.TaxesOrMiscellaneousChargeType = self.tax_miscellaneous_type
                CommercialInvoice.PackingCosts.Amount = self.packing_amount
                CommercialInvoice.PackingCosts.Currency = self.packing_currency
                CommercialInvoice.HandlingCosts.Amount = self.handling_amount
                CommercialInvoice.HandlingCosts.Currency = self.handling_currency
                CommercialInvoice.SpecialInstructions = self.special_instructions
                CommercialInvoice.DeclarationStatement = self.declaration_statement
                CommercialInvoice.PaymentTerms = self.payment_terms
                CommercialInvoice.Purpose = self.purpose_of_shipment
                CustomerReference = shipment.create_wsdl_object_of_type("CustomerReference")
                CustomerReference.CustomerReferenceType = self.customer_reference
                CustomerReference.Value = self.customer_reference_value
                CommercialInvoice.CustomerReferences.append(CustomerReference)
                CommercialInvoice.OriginatorName = self.originator_name
                CommercialInvoice.TermsOfSale = self.terms_of_sale
                CustomsClearanceDetail.CommercialInvoice = CommercialInvoice
                shipment.RequestedShipment.ShippingDocumentSpecification.ShippingDocumentTypes="COMMERCIAL_INVOICE"
                shipment.RequestedShipment.ShippingDocumentSpecification.CommercialInvoiceDetail.Format.ImageType = "PDF"
                shipment.RequestedShipment.ShippingDocumentSpecification.CommercialInvoiceDetail.Format.StockType = "PAPER_LETTER"
                CustomsClearanceDetail.ImporterOfRecord.Contact.PersonName = self.to_person_name
                CustomsClearanceDetail.ImporterOfRecord.Contact.CompanyName = self.to_company_name
                CustomsClearanceDetail.ImporterOfRecord.Contact.PhoneNumber = self.to_phone_number
                CustomsClearanceDetail.ImporterOfRecord.Address.StreetLines = to_address
                CustomsClearanceDetail.ImporterOfRecord.Address.City = self.to_city
                CustomsClearanceDetail.ImporterOfRecord.Address.StateOrProvinceCode = self.to_state_code
                CustomsClearanceDetail.ImporterOfRecord.Address.PostalCode = self.to_postal_code
                CustomsClearanceDetail.ImporterOfRecord.Address.CountryCode = self.to_country_code
                for i in self.commodity_lines:
                    commodity = shipment.create_wsdl_object_of_type('Commodity')
                    commodity.Name = i.name
                    commodity.Description = i.description
                    commodity.NumberOfPieces = i.number_of_peices
                    commodity.CountryOfManufacture = i.country_of_manufacture.code
                    commodity.Weight.Value = i.weight
                    commodity.Weight.Units = i.weight_unit
                    commodity.Quantity = i.quantity
                    commodity.QuantityUnits = i.quantity_units
                    commodity.UnitPrice.Currency = self.custom_currency
                    commodity.UnitPrice.Amount = i.unit_price
                    commodity.CustomsValue.Currency = self.custom_currency
                    commodity.CustomsValue.Amount = i.customs_value
                    if i.harmonized_code:
                        commodity.HarmonizedCode = i.harmonized_code
                    CustomsClearanceDetail.Commodities.append(commodity)
                shipment.RequestedShipment.CustomsClearanceDetail = CustomsClearanceDetail
            if len(self.package_ids) > 1:
                shipment.RequestedShipment.PackageCount = len(self.package_ids)
            for i in self.package_ids:
                sequence_no +=  1
                package = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                if len(self.package_ids) > 1:
                    package.SequenceNumber = sequence_no
                package_weight = shipment.create_wsdl_object_of_type('Weight')
                # Weight, in LB.
                package_weight.Value = i.weight
                package_weight.Units = i.units
                package.Weight = package_weight
                package.PhysicalPackaging = i.physical_packaging
                if i.dimension:
                    dimensions = shipment.create_wsdl_object_of_type('Dimensions')
                    LinearUnits = shipment.create_wsdl_object_of_type('LinearUnits')
                    LinearUnits = i.dim_units
                    dimensions.Length = i.length
                    dimensions.Width = i.width
                    dimensions.Height = i.height
                    dimensions.Units =  LinearUnits
                    package.Dimensions = dimensions
                if master_tracking_number:
                    shipment.RequestedShipment.RequestedPackageLineItems = []
                    TrackingId = shipment.create_wsdl_object_of_type('TrackingId')
                    TrackingId.TrackingIdType = TrackingIdType
                    TrackingId.TrackingNumber = master_tracking_number
                    shipment.RequestedShipment.MasterTrackingId = TrackingId
                shipment.add_package(package)
                # Special Services COD
                if self.special_services_type == 'COD':
                    package.SpecialServicesRequested.SpecialServiceTypes.append('COD')
                    package.SpecialServicesRequested.CodDetail.CodCollectionAmount.Amount = i.cod_amount
                    package.SpecialServicesRequested.CodDetail.CodCollectionAmount.Currency = self.cod_currency
                    package.SpecialServicesRequested.CodDetail.CollectionType = self.cod_collection_type
#                     package.SpecialServicesRequested.CodDetail.AddTransportationChargesDetail.ChargeBasis = "NET_CHARGE"
#                     package.SpecialServicesRequested.CodDetail.AddTransportationChargesDetail.ChargeBasisLevel = "CURRENT_PACKAGE"
#                     package.SpecialServicesRequested.CodDetail.AddTransportationChargesDetail.RateTypeBasis = "LIST"
                    package.SpecialServicesRequested.CodDetail.RemitToName = self.remit_name
                
                try:
                    shipment.send_request() 
                    print "This is stoped"
                except Exception,e:
#                     print shipment.client.last_sent().str()
                    self.state = 'fail'
                    wiz = self.env['fedex.message'].create({
                                                'name':e
                                                })
                    compose_form = self.env.ref('jjuice_fedex.fedex_message_form', False)
                    return {
                        'name': _('Status'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'views': [(compose_form.id, 'form')],
                        'view_id': compose_form.id,
                        'res_model': 'fedex.message',
                        'target': 'new',
                        'res_id':wiz.id,
                        'nodestroy': True,
                        'context':self._context
                       }
                try:
                    if sequence_no == 1:
                        self.tracking_number = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                        master_tracking_number = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                        TrackingIdType = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingIdType
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
    #                 label_binary_data = binascii.a2b_base64(ascii_label_data)
    #                 ascii_label_data  = label_binary_data
                    label_extension = fedex_lists._label_image_extension.get(self.label_image_type,False)
                    label_name =  time.strftime("%Y-%m-%d")+"_"+(self.to_person_name or 'unavailable')+"_"+(self.tracking_number or 'unavailable')
                    label_name = label_name + label_extension
                    ir_attachment.create({
                                          'name':label_name,
                                          'type':'binary',
                                          'datas':ascii_label_data,
                                          'res_model':'create.shipment.fedex',
                                          'res_id':self.id,
                                          'res_name':sequence_no,
                                          'mimetype':'image/png',
                                          'file_type':'image/png',
                                          'datas_fname':self.name+label_extension
                                          })
                    i.doc_name = label_name
                    i.label = ascii_label_data
                    i.tracking_number = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                    
                    print shipment.client.last_sent().str()
                    # Net shipping costs.
                    if 'PackageRating' in shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0]:
                        i.cost = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount                
                    # COd Return Label
                    if self.special_services_type == 'COD':
                        i.cod_return_label = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].CodReturnDetail.Label.Parts[0].Image
                        i.cod_return_label_name = "COD_Return_label"+str(sequence_no)+label_extension
                    
                    self.date = time.strftime("%Y-%m-%d")
                    self.state='done'
                    self.total_package_count = shipment.RequestedShipment.PackageCount
                    if 'ShipmentDocuments' in shipment.response.CompletedShipmentDetail:
                        for i in shipment.response.CompletedShipmentDetail.ShipmentDocuments:
                            self.commerical_invoice = i.Parts[0].Image
                            self.commercial_invoice_name = 'Commercial_Invoice_' +self.name+ ".pdf"
                    if 'ShipmentRating' in shipment.response.CompletedShipmentDetail:
                        self.is_shipment_rating_charge = True
                        self.shipment_rating_charge = shipment.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails[0].TotalNetCharge.Amount    
                    
                except Exception,e:
                    wiz = self.env['fedex.message'].create({
                                                'name':e
                                                })
                    compose_form = self.env.ref('jjuice_fedex.fedex_message_form', False)
                    return {
                        'name': _('Status'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'views': [(compose_form.id, 'form')],
                        'view_id': compose_form.id,
                        'res_model': 'fedex.message',
                        'target': 'new',
                        'res_id':wiz.id,
                        'nodestroy': True,
                        'context':self._context
                       }
        return True
    
    @api.one
    @api.constrains('to_country','commodity_lines')
    def _check_international_shipment(self):
        if not self.env.context.get('override',False):
            for i in self: 
                if i.to_country.code != 'US':
                    if len(i.commodity_lines) <= 0:
                        raise ValidationError("Enter Commodity Details for International Shipment")
    
    
    name = fields.Char('Doc No.')
    date = fields.Date('Shipment Creation Date',default = lambda self:time.strftime("%Y-%m-%d"))
    commerical_invoice = fields.Binary('Commerical Invoice')
    commercial_invoice_name = fields.Char('Commercial Invoice Name')
    picking_id = fields.Many2one('stock.picking','Picking')
    picking_note = fields.Text(related='picking_id.note',string='Order Notes')
    picking_state = fields.Selection(related='picking_id.state',string="State")
    tracking_number=fields.Char('Master Tracking Number')
    status = fields.Text('Status',help = "Shows the last updated Status. The status has to be updated manually")
    rate_status = fields.Text('Estimated Cost',readonly=True)
    state = fields.Selection(
                             [
                              ('draft','Draft'),
                              ('done','Done'),
                              ('fail','Fail')
                              ],'State',default='draft',required=True)
    account_id = fields.Many2one('fedex.account','Fedex Account',default = _get_default_account_id,required=True)
    dropoff_type = fields.Selection(fedex_lists._list_drop_type,'Dropoff Type',required=True,default = 'REGULAR_PICKUP')
    service_type = fields.Selection(fedex_lists._list_service_type,'Service Type',default='FEDEX_GROUND',help="Leave it blank for all services")
    packaging_type = fields.Selection(fedex_lists._list_packaging_type,'Packaging Type',required=True,default = 'YOUR_PACKAGING')
    payor = fields.Selection(
                             [
                              ('RECIPIENT','Recipient'),
                              ('SENDER','Sender'),
                              ('THIRD_PARTY','Third Party')
                              ],required=True,default = 'SENDER'
                         )
    include_duties = fields.Selection([
                                    ('ALL','All'),
                                    ('NONE','None')
                                   ],required=True,default = 'ALL'
                                 )
    label_image_type = fields.Selection(fedex_lists._label_image_type,'Label Image Type',default='PDF',required=True)
    label_stock_type = fields.Selection(fedex_lists._page_type,'Label Paper Type',default = 'PAPER_8.5X11_BOTTOM_HALF_LABEL')
    label_printing_orientation = fields.Selection([
                                                   ('BOTTOM_EDGE_OF_TEXT_FIRST','Bottom Edge of text first'),
                                                   ('TOP_EDGE_OF_TEXT_FIRST','Top Edge of text first')
                                                   ],'Label Printing Orientation',default = 'BOTTOM_EDGE_OF_TEXT_FIRST')
    total_package_count = fields.Integer('Total Package Count',default = 0,readonly=True)
    package_ids = fields.One2many('fedex.package.shipment','shipment_id','Package Details')
    
    # Fields for Ship From
    from_person_name = fields.Char('Name',required=True)
    from_company_name = fields.Char('Company Name')
    from_phone_number = fields.Char('Phone Number',required=True)
    from_street1 = fields.Char('Street',required=True)
    from_street2 = fields.Char('Street2')
    from_street3 = fields.Char('Street3')
    from_city = fields.Char('City')
    from_state_code = fields.Many2one('res.country.state','State/Province')
    from_country = fields.Many2one('res.country','Country')
    from_postal_code = fields.Char('Postal Code')
    from_residential = fields.Boolean('Residential',default=False)
    
    # Fields for Recipient
    recipient_id = fields.Many2one('res.partner','Recipient Partner',help="This field is optional.If not filled you can manually set the address")
    to_person_name = fields.Char('Customer Name',required=True)
    to_company_name = fields.Char('Company Name')
    to_phone_number = fields.Char('Phone Number',required=True)
    to_street1 = fields.Char('Street',required=True)
    to_street2 = fields.Char('Street2')
    to_street3 = fields.Char('Street3')
    to_city = fields.Char('City')
    to_state_code = fields.Many2one('res.country.state','State/Province')    
    to_country = fields.Many2one('res.country','Country')
    to_country_code = fields.Char(related="to_country.code")
    custom_value = fields.Float(compute = _compute_total_customs,string = "Total Customs Value",readonly=True,digits=dp.get_precision('Account'))
    custom_currency = fields.Selection([('USD','USD')],default = "USD",string = "Custom's Currency")
    document_type = fields.Selection([('DERIVED','Derived'),
                                      ('DOCUMENTS_ONLY','Documents Only'),
                                      ('NON_DOCUMENTS','Non Documents'),
                                      ],'Document Content',default = 'NON_DOCUMENTS')
    to_postal_code = fields.Char('Postal Code')
    to_residential = fields.Boolean('Residential',default=False)
    total_cost = fields.Float(compute = _compute_total_cost,string = "Total Cost",readonly=True,digits=dp.get_precision('Account'))
    shipment_rating_charge = fields.Float('Shipment Rating Charge')
    is_shipment_rating_charge = fields.Boolean("Is shipment rating charge applied")
    
    # International Shipment
    broker_type = fields.Selection([('EXPORT','Export'),('IMPORT','Import')],'Broker Type',default = "IMPORT")
    broker_account_number = fields.Char('Broker Account Number')
    broker_name = fields.Char('Name')
    broker_company_name = fields.Char('Broker Company Name')
    broker_phone_number = fields.Char('Broker Phone Number')
    is_broker = fields.Boolean('Broker')
    broker_street = fields.Char('Street')
    broker_street2 = fields.Char('Street')
    broker_city = fields.Char('City')
    broker_postal_code = fields.Char('Zip')
    broker_country = fields.Many2one('res.country','Country')
    broker_state_code = fields.Many2one('res.country.state','State/Province')
    commodity_lines = fields.One2many('fedex.commodity.shipment','shipment_id',"Commodities")
    B13AFilingOption = fields.Selection([('FEDEX_TO_STAMP','FedEx to Stamp'),
                                         ('FILED_ELECTRONICALLY','Filed Electronically'),
                                         ('MANUALLY_ATTACHED','Manually Attached'),
                                         ('NOT_REQUIRED','Not Required'),
                                         ('SUMMARY_REPORTING','Summary Reporting')],'B13A Filing Option',default="NOT_REQUIRED")
    ## Commercial Invoice
    commercial_invoice_comment = fields.Text('Comment',placeholder="Any comments that need to be communicated about this shipment.")
    freight_amount = fields.Float('Freight Charge',help="Any freight charges that are associated with this shipment.")
    freight_currency = fields.Selection(fedex_lists._fedex_currency,'Freight Currency',default="USD")
    tax_miscellaneous_amount = fields.Float('Tax/Miscellaneous Charge',help = "Any taxes or miscellaneous charges(other than Freight charges or Insurance charges) that are associated with this shipment.")
    tax_miscellaneous_currency = fields.Selection(fedex_lists._fedex_currency,'Tax/Miscellaneous Charge Currency',default="USD")
    tax_miscellaneous_type = fields.Selection([('COMMISSIONS','Commissions'),
                                               ('DISCOUNTS','Discounts'),
                                               ('HANDLING_FEES','Handling Fees'),
                                               ('ROYALTIES_AND_LICENSE_FEES','Royalty and License Fees'),
                                               ('TAXES','Taxes'),
                                               ('OTHER','Other')
                                               ],'Tax/Miscellaneous Charge Type',help="Specifies which kind of charge is being recorded in the preceding field.",default = "TAXES")
    packing_amount = fields.Float('Packing Costs',help="Any packing costs that are associated with this shipment")
    packing_currency = fields.Selection(fedex_lists._fedex_currency,'Packing Cost Currency',default="USD")
    handling_amount = fields.Float("Handling Cost",help="Any handling costs that are associated with this shipment.")
    handling_currency = fields.Selection(fedex_lists._fedex_currency,'Handling Cost Currency',default="USD")
    special_instructions = fields.Text('Special Instructions')
    declaration_statement = fields.Text('Declaration Statement',default = "I hereby declare that goods have been exported")
    payment_terms  = fields.Text('Payment Terms')
    purpose_of_shipment = fields.Selection([('GIFT','Gift'),
                                            ('NOT_SOLD','Not Sold'),
                                            ('PERSONAL_EFFECTS','Personal Effects'),
                                            ('REPAIR_AND_RETURN','Repair and Return'),
                                            ('SAMPLE','Sample'),
                                            ('SOLD','Sold')],'Purpose of Shipment',default="SOLD",help="The reason for the shipment. Note: SOLD is not a valid purpose for a Proforma Invoice.")
    customer_reference = fields.Selection([('BILL_OF_LADING','Bill of Landing'),
                                           ('CUSTOMER_REFERENCE','Customer Reference'),
                                           ('DEPARTMENT_NUMBER','Department Number'),
                                           ('ELECTRONIC_PRODUCT_CODE','Electronic Product Code'),
                                           ('INTRACOUNTRY_REGULATORY_REFERENCE','Intra-Country Regulatory Reference'),
                                           ('INVOICE_NUMBER','Invoice Number'),
                                           ('P_O_NUMBER','PO Number'),
                                           ('RMA_ASSOCIATION','RMA Association'),
                                           ('SHIPMENT_INTEGRITY','Shipment Integrity'),
                                           ('STORE_NUMBER','Store Number')],"Customer Reference",default="INVOICE_NUMBER",help="Identifies which reference type (from the package's customer references) is to be used as the source for the reference on this OP-900.")
    customer_reference_value = fields.Char('Customer Reference Value')
    originator_name = fields.Char('Originator Name',help="Name of the International Expert that completed the Commercial Invoice different from Sender.")
    terms_of_sale = fields.Selection([('CFR_OR_CPT','Cost and Freight/Carriage Paid TO'),
                                      ('CIF_OR_CIP','Cost Insurance and Freight/Carraige Insurance Paid'),
                                      ('DAP','DAP'),
                                      ('DAT','DAT'),
                                      ('DDP','Delivered Duty Paid'),
                                      ('DDU','Delivered Duty Unpaid'),
                                      ('EXW','Ex Works'),
                                      ('FOB_OR_FCA','Free On Board/Free Carrier')
                                      ],'Terms of Sale',default="DDP")
    ## NAFTA details
    nafta_preference_criterion = fields.Selection([('A','A'),('B','B'),('C','C'),('D','D'),('E','E'),('F','F')],'NAFTA Preference Criterion',help="Defined by NAFTA regulations.")
    nafta_producer_determination_code = fields.Selection([('NO_1','NO_1'),
                                                          ('NO_2','NO_2'),
                                                          ('NO_3','NO_3'),
                                                          ('YES','YES')
                                                          ],'NAFTA Producer Determination Code',help="See instructions for NAFTA Certificate of Origin for code definitions.")
    producer_id = fields.Char('Producer ID')
    net_cost_method = fields.Selection([
                                        ('NC','NC'),('NO','No')
                                        ],'NAFTA Net Cost Method Code')
    
    date_range_from = fields.Date('Beginning Date')
    date_range_to = fields.Date('End Date')
    
    ## COD
    special_services_type = fields.Selection([('COD','COD')],string = "Request Special Services")
    cod_amount = fields.Float('COD Amount')
    cod_currency = fields.Selection(fedex_lists._fedex_currency,string = "COD Currency",default="CAD")
    cod_collection_type = fields.Selection([('ANY','Any'),
                                            ('CASH','Cash'),
                                            ('COMPANY_CHECK','Company Check'),
                                            ('GUARANTEED_FUNDS','Guarunteed'),
                                            ('PERSONAL_CHECK','Personal Check')
                                            ],'Collection Type')
    institution_person_name = fields.Char('Financial Institution Person Name')
    institution_company_name = fields.Char('Financial Institution Company Name')
    institution_phone_number = fields.Char('Financial Institution Phone Number')
    institution_street = fields.Char('Financial Institution Address')
    institution_street2 = fields.Char('Financial Institution Address')
    institution_city = fields.Char('Financial Institution City')
    institution_state_code = fields.Many2one('res.country.state','Financial Institution State')
    institution_postal_code = fields.Char('Financial Institution Postal Code')
    institution_country= fields.Many2one('res.country','Financial Institution Country')
    remit_name = fields.Char('Remit to Name')
    
    
    

class fedex_commodity_shipment(models.Model):
    _name="fedex.commodity.shipment"
    _description = "Fedex International Commodity"
    
    @api.depends('quantity','unit_price')
    def _compute_customs_value(self):
        self.customs_value = self.unit_price * self.quantity    
    
    @api.one
    @api.onchange('name')
    def onchange_name(self):
        self.description = self.name
    
    shipment_id = fields.Many2one('create.shipment.fedex','Shipment')
    name = fields.Char('Name',required=True)
    description = fields.Text('Description',help="Min. 3 Chars required",required=True)
    number_of_peices = fields.Integer(string = "Number of Pieces",help="Non Negative Integer.Required. The total number of packages within the shipment that contain this commodity (can be less than or equal to PackageCount).")
    country_of_manufacture = fields.Many2one("res.country",string = "Country of Manufacture",help="Country of Manufacture,Code of the country in which the commodity contents were produced or manufactured in their final form.",default = "USD")
    quantity = fields.Integer("Quantity",help="None Negative Integer. Total quantity of an individual commodity within this shipment (used in conjunction with QuantityUnits)")
    quantity_units = fields.Selection([('EA','Each'),
                                       ('DZ','Dozen')],'Quantity Units',default = 'EA',help="(for example: EA = each; DZ = dozen) of each commodity in the shipment.")
    weight = fields.Float('Weight',help="Total weight of this commodity")
    weight_unit = fields.Selection([('KG','Kg'),('LB','Pounds')],'Weight Units',default = "LB")
    unit_price = fields.Float('Unit Price')
    customs_value = fields.Float(compute = _compute_customs_value,string ='Total Amount',help='Should be commodity unit price times quantity',readonly=True,digits=dp.get_precision('Account'))
    harmonized_code = fields.Char('Harmonized Code',help="Required for efficient clearance of the commodity.Please look at the code from FedEx Site")
    

    
class fedex_package_shipment(models.Model):
    _name = "fedex.package.shipment"
    _description = "Fedex Package Details"
    
    @api.multi
    def dublicate_line(self):
        for i in range(self.group_package_count-1):
            self.copy()

    @api.multi
    def track_shipment(self):
        track = self.env['track.fedex.shipment'].create({
                                                         'number':self.tracking_number
                                                         })
        status = ''
        msg = track.track_shipment_number()
        if msg.get('type',False) == 'error':
            self.status = "Error Code:%s"%msg.get('code',False) + "\n" + msg.get('msg','')
        elif msg.get('type',False) == 'response':
            for i in msg.get('msg',[]):
                status = i[1]
            self.status = status
                
    group_package_count = fields.Integer('Package Count',required=True,default=1,copy=False)
    status = fields.Text('Tracking Status',copy=False)
    doc_name = fields.Char('Document Name',copy=False)
    cod_return_label = fields.Binary('COD Return Label')
    cod_return_label_name = fields.Char('COD Return Label Name')
    tracking_number = fields.Char('Tracking Number',copy=False)
    shipment_id = fields.Many2one('create.shipment.fedex')
    special_services_type = fields.Selection(related="shipment_id.special_services_type")
    weight= fields.Float('Weight',required=True,default=0)
    units = fields.Selection(fedex_lists._get_unit_weight,required=True,default = 'LB')
    physical_packaging = fields.Selection(fedex_lists._get_physical_packaging_type,'Physical Packaging',required=True,default='BOX')
    cost = fields.Float('Cost',copy=False)
    parent_state = fields.Selection(related="shipment_id.state",store = True)
    dimension = fields.Boolean('Dimensions',default=True)
    length = fields.Integer('Length')
    width = fields.Integer('Width')
    height = fields.Integer('Height')
    label = fields.Binary('Label',copy=False)
    dim_units = fields.Selection([
                                  ('IN','Inches'),
                                  ('CM','Centimeters')
                                  ],'Dimensional Units',default='IN')
    cod_amount = fields.Float('COD Amount',help="Amount to be collected on COD")
    