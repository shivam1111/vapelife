from openerp import models, fields, api, _
from ..config import fedex_config
from openerp.exceptions import except_orm,Warning
import logging
from ..fedex.services.rate_service import FedexRateServiceRequest
from .. import fedex_lists
import openerp.addons.decimal_precision as dp

class rate_fedex_request(models.TransientModel):
    _name = "rate.fedex.request"
    _description = "Rate Request from Fedex"
    
    
    @api.model
    def default_get(self,fields_list):
        res= super(rate_fedex_request,self).default_get(fields_list)
        user_obj = self.env['res.users'] 
        company = user_obj._get_company()
        company_obj = self.env['res.company'].search([('id','=',company)])
        res.update({
                    'from_country':company_obj.country_id.id,
                    'from_postal_code':company_obj.zip,
                    'from_residential':company_obj.partner_id.is_residential,
                    })
        return res    
    
    @api.multi
    def create_shipment(self):
        shipment_obj = self.env['create.shipment.fedex']
        res = self.env['fedex.account'].get_fedex_account()
        shipment = shipment_obj.create({
                             'dropoff_type':self.dropoff_type,
                             'service_type':self.service_type,
                             'packaging_type':self.packaging_type,
                             'include_duties':self.include_duties,
                             'payor':self.payor,
                             'account_id':res.get('id',False),
                             'from_country':self.from_country.id,
                             'from_postal_code':self.from_postal_code,
                             'from_residential':self.from_residential,
                             'to_country':self.to_country.id,
                             'to_postal_code':self.to_postal_code,
                             'to_residential':self.to_residential,
                             'recipient_id' : self.recipient_id.id,
                         })
        shipment.onchange_recipient_id()
        package = self.env['fedex.package.shipment']
        #Creating rate request packages
        for i in self.package_ids:
            for j in range(i.group_package_count):
                package.create({
                                 'length':i.length,
                                 'width':i.width,
                                 'height':i.height,
                                 'dim_units':i.dim_units,
                                 'dimension':i.dimension,
                                 'shipment_id':shipment.id,
                                 'weight':i.weight,
                                 'units':i.units,
                                 'physical_packaging':i.physical_packaging,
                                 'group_package_count':1
                                })
        if self.to_country_code != 'US': #working
            commodity = self.env['fedex.commodity.shipment']
            shipment.custom_currency = self.customs_currency
            for i in self.commodity_lines:
                commodity.create({
                                  'shipment_id':shipment.id,
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
        compose_form = self.env.ref('jjuice_fedex.create_shipment_form', False)
        return {
            'name': _('Create Shipment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'res_model': 'create.shipment.fedex',
            'target': 'current',
            'res_id':shipment.id,
            'context':self._context
           }            
        
    
    @api.multi
    def get_rates(self):
        response = self._get_rates_fedex()
        #response is list of tuple
        msg = ''
        if response.get('type',False) == 'error':
            self.response = response.get('msg')
        elif response.get('type',False) == 'response':
            for i in response.get('msg',False): # This will be a list of tuple [(service type,currency,price)]
                msg = msg + "Serive Type:{0} -> Net Charge:{1} {2}\n".format(i[0],i[1],i[2])
            self.response = msg
            self.rate = i[2]
        compose_form = self.env.ref('jjuice_fedex.rate_request_form', False)
        return {
            'name': _('Rate Request'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'res_model': 'rate.fedex.request',
            'target': 'new',
            'res_id':self.id,
            'nodestroy': True,
            'context':self._context
           }        
    
    @api.one
    @api.depends('commodity_lines',
                 'commodity_lines.quantity',
                 'commodity_lines.unit_price'
                 )
    def _compute_total_customs(self):
        total = 0.00
        for i in self.commodity_lines:
            total = total + i.customs_value
        self.customs_value = total
        
    @api.onchange('recipient_id')
    def onchange_recipient_id(self):
        if self.recipient_id:
            self.to_country = self.recipient_id.country_id.id
            self.to_postal_code = self.recipient_id.zip 
            self.to_residential = self.recipient_id.is_residential    
    
    
    @api.model
    def calculate_rates_for_address(self,address,items):
        product = self.env['product.product']
        if len(items) > 0:
            net_weight = 0.00
            for i in items:
                pr = product.search([('id','=',i[0])],limit=1)
                weight = pr.product_tmpl_id.weight_net or pr.vol_id.weight or 0.00
                qty = i[1]
                gross_weight = qty*weight
                net_weight+=weight
            request_id = self.create({
                    'to_country':address.get('country_id',False),
                    'to_postal_code':address.get('zip',False),
                    'package_ids':[(0,0,{
                            'weight':net_weight,
                        })]
                })
            request_id.get_rates()
            return {
                    'rate':request_id.rate,
                    'msg':request_id.response
                }
        return False
    
    @api.multi
    def _get_rates_fedex(self):
        res = self.env['fedex.account'].get_fedex_account()
        if len(self.package_ids) == 0:
            raise except_orm(_('Empty Package Lines!'),
                _('The package line items are empty'))            
        if res:
            config_object = fedex_config(
                             key=res.get('key',False),
                             password=res.get('password',False),
                             account_number=res.get('account_number',False),
                             meter_number=res.get('meter_number',False),
                             freight_account_number=res.get('freight_account_number',False),
                             use_test_server=res.get('use_test_server',False)
                             )
            
            # Set this to the INFO level to see the response from Fedex printed in stdout.
            logging.basicConfig(level=logging.DEBUG)
            rate_request = FedexRateServiceRequest(config_object.CONFIG_OBJ)
            rate_request.RequestedShipment.DropoffType = self.dropoff_type
            if not self.service_type: #Leave it blank for all services
                rate_request.RequestedShipment.ServiceType = None
            else:
                rate_request.RequestedShipment.ServiceType = self.service_type
            rate_request.RequestedShipment.PackagingType = self.packaging_type
            rate_request.RequestedShipment.EdtRequestType = self.include_duties
            rate_request.RequestedShipment.ShippingChargesPayment.PaymentType = self.payor
            #Shipper Information
            rate_request.RequestedShipment.Shipper.Address.PostalCode = self.from_postal_code
            rate_request.RequestedShipment.Shipper.Address.CountryCode = self.from_country.code
            rate_request.RequestedShipment.Shipper.Address.Residential = self.from_residential
            #Recipient Information
            rate_request.RequestedShipment.Recipient.Address.PostalCode = self.to_postal_code
            rate_request.RequestedShipment.Recipient.Address.CountryCode = self.to_country.code
            rate_request.RequestedShipment.Recipient.Address.Residential = self.to_residential
            
            # International Shipment Quote
            if self.to_country_code != 'US':
                CustomsClearanceDetail  = rate_request.create_wsdl_object_of_type('CustomsClearanceDetail')  
                CustomsClearanceDetail.CustomsValue.Currency = self.customs_currency
                CustomsClearanceDetail.CustomsValue.Amount = self.customs_value
                DutiesPayment  = rate_request.create_wsdl_object_of_type('Payment')
                DutiesPayment.PaymentType = self.payor
                DutiesPayment.Payor.ResponsibleParty.AccountNumber = res.get('account_number',False)
                DutiesPayment.Payor.ResponsibleParty.Address.PostalCode = self.from_postal_code
                DutiesPayment.Payor.ResponsibleParty.Address.CountryCode = self.from_country.code
                DutiesPayment.Payor.ResponsibleParty.Address.Residential = self.from_residential
                CustomsClearanceDetail.DutiesPayment = DutiesPayment
                CustomsClearanceDetail.ExportDetail.B13AFilingOption = self.B13AFilingOption                
                for i in self.commodity_lines:
                    commodity = rate_request.create_wsdl_object_of_type('Commodity')
                    commodity.Name = i.name
                    commodity.Description = i.description
                    commodity.NumberOfPieces = i.number_of_peices
                    commodity.CountryOfManufacture = i.country_of_manufacture.code
                    commodity.Weight.Value = i.weight
                    commodity.Weight.Units = i.weight_unit
                    commodity.Quantity = i.quantity
                    commodity.QuantityUnits = i.quantity_units
                    commodity.UnitPrice.Currency = self.customs_currency
                    commodity.UnitPrice.Amount = i.unit_price
                    commodity.CustomsValue.Currency = self.customs_currency
                    commodity.CustomsValue.Amount = i.customs_value
                    if i.harmonized_code:
                        commodity.HarmonizedCode = i.harmonized_code
                    CustomsClearanceDetail.Commodities.append(commodity)
                rate_request.RequestedShipment.CustomsClearanceDetail = CustomsClearanceDetail
            for i in self.package_ids:
                package = rate_request.create_wsdl_object_of_type('RequestedPackageLineItem')
                package_weight = rate_request.create_wsdl_object_of_type('Weight')
                # Weight, in LB.
                package_weight.Value = i.weight
                package_weight.Units = i.units
                package.Weight = package_weight
                package.PhysicalPackaging = i.physical_packaging
                package.GroupPackageCount = i.group_package_count
                if i.dimension:
                    dimensions = rate_request.create_wsdl_object_of_type('Dimensions')
                    LinearUnits = rate_request.create_wsdl_object_of_type('LinearUnits')
                    LinearUnits = i.dim_units
                    dimensions.Length = i.length
                    dimensions.Width = i.width
                    dimensions.Height = i.height
                    dimensions.Units =  LinearUnits
                    package.Dimensions = dimensions                
                rate_request.add_package(package)
                # Special Services COD
                if self.special_services_type == 'COD':
                    package.SpecialServicesRequested.SpecialServiceTypes.append('COD')
                    package.SpecialServicesRequested.CodDetail.CodCollectionAmount.Amount = i.cod_amount
                    package.SpecialServicesRequested.CodDetail.CodCollectionAmount.Currency = self.cod_currency
                    package.SpecialServicesRequested.CodDetail.CollectionType = self.cod_collection_type                
            try:    
                rate_request.send_request()
#             print "HighestSeverity:", rate_request.response.HighestSeverity
            # RateReplyDetails can contain rates for multiple ServiceTypes if ServiceType was set to None
            except Exception, e:
                return {
                        'type':'error',
                        'msg':str(e)
                        }
            msg = []
            try:
                for service in rate_request.response.RateReplyDetails:
                    for detail in service.RatedShipmentDetails:
                        for surcharge in detail.ShipmentRateDetail.Surcharges:
                            if surcharge.SurchargeType == 'OUT_OF_DELIVERY_AREA':
                                msg.append((service.ServiceType,'',surcharge.Amount.Amount))
                                msg = msg + '\n' +  "%s: ODA rate_request charge %s" % (service.ServiceType, surcharge.Amount.Amount)
                                print "%s: ODA rate_request charge %s" % (service.ServiceType, surcharge.Amount.Amount)
                    for rate_detail in service.RatedShipmentDetails:
                        msg.append((service.ServiceType,rate_detail.ShipmentRateDetail.TotalNetFedExCharge.Currency,rate_detail.ShipmentRateDetail.TotalNetCharge.Amount))
                    # If the request succeeds then we send type response and in msg we send a list of tuple [(service type,currency,price)]
                return {
                        'type':'response',
                        'msg':msg
                        }
            except Exception, e:
                return {
                        'type':'error',
                        'msg':str(e)
                        }                
                
        else:
            raise except_orm(_('Account Configuration!'),
                _("No Fedex Account has been configured")
                ) 


    ##################################VARIABLE DECLARATION##########################################################
    
    dropoff_type = fields.Selection(fedex_lists._list_drop_type,'Dropoff Type',required=True,default = 'REGULAR_PICKUP')
    service_type = fields.Selection(fedex_lists._list_service_type,'Service Type',default='FEDEX_GROUND',help="Leave it blank for all services")
    packaging_type = fields.Selection(fedex_lists._list_packaging_type,'Packaging Type',required=True,default = 'YOUR_PACKAGING')
    include_duties = fields.Selection([
                                        ('ALL','All'),
                                        ('NONE','None')
                                       ],required=True,default = 'ALL'
                                     )
    payor = fields.Selection(
                             [
                              ('RECIPIENT','Recipient'),
                              ('SENDER','Sender'),
                              ('THIRD_PARTY','Third Party')
                              ],required=True,default = 'SENDER'
                         )
    package_ids = fields.One2many('fedex.package','request_id','Package Details')
    # Fields for Ship From
    from_country = fields.Many2one('res.country','Country')
    from_postal_code = fields.Char('Postal Code')
    from_residential = fields.Boolean('Residential',default=False)
    
    # Fields for Recipient
    recipient_id = fields.Many2one('res.partner','Recipient Partner',help="This field is optional.If not filled you can manually set the address")
    to_country = fields.Many2one('res.country','Country',select=True)
    to_country_code = fields.Char(related="to_country.code",string='Country Code')
    to_postal_code = fields.Char('Postal Code')
    to_residential = fields.Boolean('Residential',default=False)
    response = fields.Text(
                           'Response')
    #International Shipment
    commodity_lines = fields.One2many('rate.commodity.package','request_id','Commodities')
    customs_value = fields.Float(compute = _compute_total_customs,string = "Total Customs Value",readonly=True,digits=dp.get_precision('Account'))
    customs_currency = fields.Selection(fedex_lists._fedex_currency,'Customs Currency',default="USD")
    B13AFilingOption = fields.Selection([('FEDEX_TO_STAMP','FedEx to Stamp'),
                                         ('FILED_ELECTRONICALLY','Filed Electronically'),
                                         ('MANUALLY_ATTACHED','Manually Attached'),
                                         ('NOT_REQUIRED','Not Required'),
                                         ('SUMMARY_REPORTING','Summary Reporting')],'B13A Filing Option',default="NOT_REQUIRED")
    
    special_services_type = fields.Selection([('COD','COD')],string = "Request Special Services")
    cod_collection_type = fields.Selection([('ANY','Any'),
                                            ('CASH','Cash'),
                                            ('COMPANY_CHECK','Company Check'),
                                            ('GUARANTEED_FUNDS','Guarunteed'),
                                            ('PERSONAL_CHECK','Personal Check')
                                            ],'Collection Type')
    cod_currency = fields.Selection(fedex_lists._fedex_currency,string = "COD Currency",default="CAD")
    rate = fields.Float("Rate")   
class rate_commodity_package(models.TransientModel):
    _name = "rate.commodity.package"
    _description = "Commodity Details"
    
    @api.onchange('name')
    def _onchange_name(self):
        self.description = self.name
        
    @api.depends('quantity','unit_price')
    def _compute_customs_value(self):
        self.customs_value = self.unit_price * self.quantity
        
    request_id = fields.Many2one('rate.fedex.request','Rate Request')
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

class fedex_package(models.TransientModel):
    _name = "fedex.package"
    _description = "Fedex Package Details"
    
    request_id = fields.Many2one('rate.fedex.request')
    weight= fields.Float('Weight',required=True,default=0)
    units = fields.Selection(fedex_lists._get_unit_weight,required=True,default = 'LB')
    physical_packaging = fields.Selection(fedex_lists._get_physical_packaging_type,'Physical Packaging',required=True,default='BOX')
    group_package_count = fields.Integer('Group Package Count',default = 1,required = True)
    cod_amount = fields.Float('COD Amount')
    dimension = fields.Boolean('Dimensions')
    length = fields.Integer('Length')
    width = fields.Integer('Width')
    height = fields.Integer('Height')
    dim_units = fields.Selection([
                                  ('IN','Inches'),
                                  ('CM','Centimeters')
                          ],'Dimensional Units',default='IN')
        