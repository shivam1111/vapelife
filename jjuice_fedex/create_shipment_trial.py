import time
import httplib
from datetime import datetime
from collections import OrderedDict

def prepare_data():
    """Sets the data for the soap call in shipping request, this one follows
    closely the PHP samples provided by Fedex.
    """
    KEY = "pJWiO448Vp2l5Lwu"
    PASSWORD = "Thereisaway09"
    ACCOUNT_NUMBER = "510087623"
    METER_NUMBER = "118694899"

    SERVICE_TYPE = "FEDEX_GROUND"

    COMPANY_NAME = "JJUICE"
    COMPANY_PN = "9560566121"
    COMPANY_ADDRESS = "Tral Address"
    COMPANY_CITY = "Draper"
    COMPANY_ZIPCODE = "84020" 
    COMPANY_STATE = 'UT'
    COMPANY_COUNTRYCODE = "US"
    PERSON_NAME = "Joe Dieghan"
    PERSON_PN = "416-675-6417"
    CLIENT_ADDRESS = "11 Vulcan St"
    CLIENT_CITY = "Draper"
    CLIENT_ZIPCODE = "M9W 1L3"
    CLIENT_STATE = "ON"
    CLIENT_COUNTRYCODE = "CA"

    auth_det = OrderedDict([(u'UserCredential',
        OrderedDict([
            (u'Key', KEY),
            (u'Password', PASSWORD),
        ]),
    )])

    cli_det = OrderedDict([
        (u'AccountNumber', ACCOUNT_NUMBER),
        (u'MeterNumber', METER_NUMBER)
    ])

    version = OrderedDict([
        (u'ServiceId', u'ship'),
        (u'Major', u'15'),
        (u'Intermediate', u'0'),
        (u'Minor', u'0'),
    ])

    shipper = OrderedDict([
        (u'Contact', OrderedDict([
            (u'CompanyName', COMPANY_NAME),
            (u'PhoneNumber', COMPANY_PN),
        ])),
        (u'Address', OrderedDict([
            (u'StreetLines', COMPANY_ADDRESS),
            (u'City', COMPANY_CITY),
            (u'StateOrProvinceCode', COMPANY_STATE),
            (u'PostalCode', COMPANY_ZIPCODE),
            (u'CountryCode', COMPANY_COUNTRYCODE),
        ])),
    ])

    recipient = OrderedDict([
        (u'Contact', OrderedDict([
            (u'PersonName', PERSON_NAME),
            (u'PhoneNumber', PERSON_PN),
        ])),
        (u'Address', OrderedDict([
            (u'StreetLines', CLIENT_ADDRESS),
            (u'City', CLIENT_CITY),
            (u'StateOrProvinceCode', CLIENT_STATE),
            (u'PostalCode', CLIENT_ZIPCODE),
            (u'CountryCode', CLIENT_COUNTRYCODE),
        ])),
    ])

    charges_payment = OrderedDict([
        (u'PaymentType', u'SENDER'),
        (u'Payor', OrderedDict([
            (u'ResponsibleParty', OrderedDict([
                (u'AccountNumber', ACCOUNT_NUMBER)
            ]))
        ])),
    ])

    label_specification = OrderedDict([
        (u'LabelFormatType', u'COMMON2D'),
        (u'ImageType', u'PDF'),
        (u'LabelStockType', u'PAPER_4X6'),
    ])

    req_pack = OrderedDict([
        (u'SequenceNumber', u'1'),
        (u'GroupPackageCount', u'1'),
        (u'Weight', OrderedDict([
            (u'Units', u'LB'),
            (u'Value', u'50'),
        ])),
    ])


#     if signature:
#         req_pack['SpecialServicesRequested'] = OrderedDict([
#             (u'SpecialServiceTypes', u'SIGNATURE_OPTION'),
#             (u'SignatureOptionDetail', OrderedDict([
#                 (u'OptionType', u'DIRECT')
#             ]))
#         ])

    req_ship = OrderedDict([
        (u'ShipTimestamp', u'{0}'.format(time.strftime("%Y-%m-%dT%H:%M:%S"), datetime.now())),
        (u'DropoffType', u'REGULAR_PICKUP'),
        (u'ServiceType', SERVICE_TYPE),
        (u'PackagingType', u'YOUR_PACKAGING'),
        (u'Shipper', shipper),
        (u'Recipient', recipient),
        (u'ShippingChargesPayment', charges_payment),
    ])

    if CLIENT_COUNTRYCODE != u'US':
        # In case of international handling
        customclearance = OrderedDict([
            (u'DutiesPayment', OrderedDict([
                (u'PaymentType', u'SENDER'),
                (u'Payor', OrderedDict([
                    (u'ResponsibleParty', OrderedDict([
                        (u'AccountNumber', "510087623"),
                        (u'Address', OrderedDict([
                            (u'CountryCode', "US"),
                        ])),
                    ])),
                ])),
            ])),
            (u'DocumentContent', u'NON_DOCUMENTS'),
            (u'CustomsValue', OrderedDict([
                (u'Currency', u'USD'),
                (u'Amount', 12),
            ])),
            (u'Commodities', OrderedDict([
                (u'NumberOfPieces', u'1'),
                (u'Description', u'OndadeMar Element'),
                (u'CountryOfManufacture', "US"),
                (u'Weight', OrderedDict([
                    (u'Units', u'LB'),
                    (u'Value', "12"),
                ])),
                (u'Quantity', u'1'),
                (u'QuantityUnits', u'EA'),
                (u'UnitPrice', OrderedDict([
                    (u'Currency', u'USD'),
                    (u'Amount', 12),
                ])),
            ])),
            (u'ExportDetail', OrderedDict([
                (u'B13AFilingOption', u'NOT_REQUIRED'),
            ]))
        ])

        req_ship[u'CustomsClearanceDetail'] = customclearance

    req_ship[u'LabelSpecification'] = label_specification
    req_ship[u'PackageCount'] = u'1'
    req_ship[u'RequestedPackageLineItems'] = req_pack

    request = OrderedDict([(u'ProcessShipmentRequest', OrderedDict([
        (u'WebAuthenticationDetail', auth_det),
        (u'ClientDetail', cli_det),
        (u'Version', version),
        (u'RequestedShipment', req_ship),
    ]))])

    return request


def soap_call(inner_data):
    """Posts a soap call to Fedex Webservice Used in ShipRequest
    """
    to_send = u'''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://fedex.com/ws/ship/v15">
<SOAP-ENV:Body>{0}</SOAP-ENV:Body></SOAP-ENV:Envelope>'''.format(simple_dict_to_xml(inner_data)).encode('ascii', 'ignore')

#     server = 'ws.fedex.com'
#     if settings.CONFIG_FEDEX.use_test_server:
    server = 'wsbeta.fedex.com'
    to_send='''
<SOAP-ENV:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://fedex.com/ws/ship/v17" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <ns0:Body>
      <ns1:ProcessShipmentRequest>
         <ns1:WebAuthenticationDetail>
            <ns1:UserCredential>
               <ns1:Key>tPsZ5Om5Pk518EgX</ns1:Key>
               <ns1:Password>WPxWUSvqev3gEqTRdkDxn4pQv</ns1:Password>
            </ns1:UserCredential>
         </ns1:WebAuthenticationDetail>
         <ns1:ClientDetail>
            <ns1:AccountNumber>510087143</ns1:AccountNumber>
            <ns1:MeterNumber>118695518</ns1:MeterNumber>
         </ns1:ClientDetail>
         <ns1:Version>
            <ns1:ServiceId>ship</ns1:ServiceId>
            <ns1:Major>17</ns1:Major>
            <ns1:Intermediate>0</ns1:Intermediate>
            <ns1:Minor>0</ns1:Minor>
         </ns1:Version>
         <ns1:RequestedShipment>
            <ns1:ShipTimestamp>2016-01-08T03:03:35.662873</ns1:ShipTimestamp>
            <ns1:DropoffType>REGULAR_PICKUP</ns1:DropoffType>
            <ns1:ServiceType>FEDEX_GROUND</ns1:ServiceType>
            <ns1:PackagingType>YOUR_PACKAGING</ns1:PackagingType>
            <ns1:TotalWeight>
               <ns1:Units>LB</ns1:Units>
               <ns1:Value>12.0</ns1:Value>
            </ns1:TotalWeight>
            <ns1:Shipper>
               <ns1:Contact>
                  <ns1:PersonName>Joe Dieghan</ns1:PersonName>
                  <ns1:CompanyName>JJuice</ns1:CompanyName>
                  <ns1:PhoneNumber>801-331-8919</ns1:PhoneNumber>
               </ns1:Contact>
               <ns1:Address>
                  <ns1:StreetLines>12411 South 265 West</ns1:StreetLines>
                  <ns1:StreetLines>Suite C</ns1:StreetLines>
                  <ns1:City>Draper</ns1:City>
                  <ns1:StateOrProvinceCode>UT</ns1:StateOrProvinceCode>
                  <ns1:PostalCode>84020</ns1:PostalCode>
                  <ns1:CountryCode>US</ns1:CountryCode>
                  <ns1:Residential>false</ns1:Residential>
               </ns1:Address>
            </ns1:Shipper>
            <ns1:Recipient>
               <ns1:Contact>
                  <ns1:PersonName>Hung</ns1:PersonName>
                  <ns1:CompanyName>iBliss</ns1:CompanyName>
                  <ns1:PhoneNumber>416-675-6417</ns1:PhoneNumber>
               </ns1:Contact>
               <ns1:Address>
                  <ns1:StreetLines>11 Vulcan St</ns1:StreetLines>
                  <ns1:City>Etobicoke</ns1:City>
                  <ns1:StateOrProvinceCode>ON</ns1:StateOrProvinceCode>
                  <ns1:PostalCode>M9W 1L3</ns1:PostalCode>
                  <ns1:CountryCode>CA</ns1:CountryCode>
                  <ns1:Residential>false</ns1:Residential>
               </ns1:Address>
            </ns1:Recipient>
            <ns1:SoldTo>
               <ns1:Contact>
                  <ns1:PersonName>Hung</ns1:PersonName>
                  <ns1:CompanyName>iBliss</ns1:CompanyName>
                  <ns1:PhoneNumber>416-675-6417</ns1:PhoneNumber>
               </ns1:Contact>
               <ns1:Address>
                  <ns1:StreetLines>11 Vulcan St</ns1:StreetLines>
                  <ns1:City>Etobicoke</ns1:City>
                  <ns1:StateOrProvinceCode>ON</ns1:StateOrProvinceCode>
                  <ns1:PostalCode>M9W 1L3</ns1:PostalCode>
                  <ns1:CountryCode>CA</ns1:CountryCode>
                  <ns1:Residential>false</ns1:Residential>
               </ns1:Address>
            </ns1:SoldTo>
            <ns1:ShippingChargesPayment>
               <ns1:PaymentType>RECIPIENT</ns1:PaymentType>
               <ns1:Payor>
                  <ns1:ResponsibleParty>
                     <ns1:AccountNumber>510087143</ns1:AccountNumber>
                     <ns1:Address>
                        <ns1:CountryCode>US</ns1:CountryCode>
                     </ns1:Address>
                  </ns1:ResponsibleParty>
               </ns1:Payor>
            </ns1:ShippingChargesPayment>
            <ns1:CustomsClearanceDetail>
               <ns1:DutiesPayment>
                  <ns1:PaymentType>RECIPIENT</ns1:PaymentType>
                  <ns1:Payor>
                     <ns1:ResponsibleParty>
                        <ns1:AccountNumber>510087143</ns1:AccountNumber>
                        <ns1:Address>
                           <ns1:StreetLines>12411 South 265 West</ns1:StreetLines>
                           <ns1:StreetLines>Suite C</ns1:StreetLines>
                           <ns1:City>Draper</ns1:City>
                           <ns1:StateOrProvinceCode>UT</ns1:StateOrProvinceCode>
                           <ns1:PostalCode>84020</ns1:PostalCode>
                           <ns1:CountryCode>US</ns1:CountryCode>
                           <ns1:Residential>false</ns1:Residential>
                        </ns1:Address>
                     </ns1:ResponsibleParty>
                  </ns1:Payor>
               </ns1:DutiesPayment>
               <ns1:DocumentContent>NON_DOCUMENTS</ns1:DocumentContent>
               <ns1:CustomsValue>
                  <ns1:Currency>USD</ns1:Currency>
                  <ns1:Amount>100.0</ns1:Amount>
               </ns1:CustomsValue>
               <ns1:CommercialInvoice>
                  <ns1:Comments>False</ns1:Comments>
                  <ns1:FreightCharge>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>0.0</ns1:Amount>
                  </ns1:FreightCharge>
                  <ns1:TaxesOrMiscellaneousCharge>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>0.0</ns1:Amount>
                  </ns1:TaxesOrMiscellaneousCharge>
                  <ns1:TaxesOrMiscellaneousChargeType>TAXES</ns1:TaxesOrMiscellaneousChargeType>
                  <ns1:PackingCosts>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>0.0</ns1:Amount>
                  </ns1:PackingCosts>
                  <ns1:HandlingCosts>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>0.0</ns1:Amount>
                  </ns1:HandlingCosts>
                  <ns1:SpecialInstructions>False</ns1:SpecialInstructions>
                  <ns1:DeclarationStatement>I hereby declare that goods have been exported</ns1:DeclarationStatement>
                  <ns1:PaymentTerms>False</ns1:PaymentTerms>
                  <ns1:Purpose>SOLD</ns1:Purpose>
                  <ns1:CustomerReferences>
                     <ns1:CustomerReferenceType>INVOICE_NUMBER</ns1:CustomerReferenceType>
                     <ns1:Value>False</ns1:Value>
                  </ns1:CustomerReferences>
                  <ns1:OriginatorName>False</ns1:OriginatorName>
                  <ns1:TermsOfSale>DDP</ns1:TermsOfSale>
               </ns1:CommercialInvoice>
               <ns1:Commodities>
                  <ns1:Name>Vapejjuice</ns1:Name>
                  <ns1:NumberOfPieces>1</ns1:NumberOfPieces>
                  <ns1:Description>Vapejjuice</ns1:Description>
                  <ns1:CountryOfManufacture>US</ns1:CountryOfManufacture>
                  <ns1:Weight>
                     <ns1:Units>LB</ns1:Units>
                     <ns1:Value>10.0</ns1:Value>
                  </ns1:Weight>
                  <ns1:Quantity>10</ns1:Quantity>
                  <ns1:QuantityUnits>EA</ns1:QuantityUnits>
                  <ns1:UnitPrice>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>10.0</ns1:Amount>
                  </ns1:UnitPrice>
                  <ns1:CustomsValue>
                     <ns1:Currency>USD</ns1:Currency>
                     <ns1:Amount>100.0</ns1:Amount>
                  </ns1:CustomsValue>
               </ns1:Commodities>
               <ns1:ExportDetail>
                  <ns1:B13AFilingOption>NOT_REQUIRED</ns1:B13AFilingOption>
               </ns1:ExportDetail>
            </ns1:CustomsClearanceDetail>
            <ns1:LabelSpecification>
               <ns1:LabelFormatType>COMMON2D</ns1:LabelFormatType>
               <ns1:ImageType>PNG</ns1:ImageType>
               <ns1:LabelStockType>PAPER_4X6</ns1:LabelStockType>
               <ns1:LabelPrintingOrientation>BOTTOM_EDGE_OF_TEXT_FIRST</ns1:LabelPrintingOrientation>
            </ns1:LabelSpecification>
            <ns1:ShippingDocumentSpecification>
               <ns1:ShippingDocumentTypes>COMMERCIAL_INVOICE</ns1:ShippingDocumentTypes>
               <ns1:CommercialInvoiceDetail>
                  <ns1:Format>
                     <ns1:ImageType>PDF</ns1:ImageType>
                     <ns1:StockType>PAPER_LETTER</ns1:StockType>
                  </ns1:Format>
               </ns1:CommercialInvoiceDetail>
            </ns1:ShippingDocumentSpecification>
            <ns1:RateRequestTypes>ACCOUNT</ns1:RateRequestTypes>
            <ns1:EdtRequestType>NONE</ns1:EdtRequestType>
            <ns1:PackageCount>1</ns1:PackageCount>
            <ns1:RequestedPackageLineItems>
               <ns1:Weight>
                  <ns1:Units>LB</ns1:Units>
                  <ns1:Value>12.0</ns1:Value>
               </ns1:Weight>
               <ns1:Dimensions>
                  <ns1:Length>12</ns1:Length>
                  <ns1:Width>12</ns1:Width>
                  <ns1:Height>12</ns1:Height>
                  <ns1:Units>IN</ns1:Units>
               </ns1:Dimensions>
               <ns1:PhysicalPackaging>BOX</ns1:PhysicalPackaging>
            </ns1:RequestedPackageLineItems>
         </ns1:RequestedShipment>
      </ns1:ProcessShipmentRequest>
   </ns0:Body>
</SOAP-ENV:Envelope>
'''
    webservice = httplib.HTTPS(server)
    webservice.putrequest('POST', '/web-services/ship')
    webservice.putheader('Host', server)
    webservice.putheader('User-Agent', 'Python post')
    webservice.putheader('Content-type', 'text/xml; charset="UTF-8"')
    webservice.putheader('Content-length', '%d' % len(to_send))
    webservice.putheader('SOAPAction', '""')
    webservice.endheaders()
    webservice.send(to_send)

    statuscode, statusmessage, header = webservice.getreply()
    res = webservice.getfile().read()
    return res

def simple_dict_to_xml(in_dict):
    """Converts a simple dict to an xml using they key for the element and the
    content as the value, prepends ns1: to send a soap request
    """
    result = u''
    for key, val in in_dict.iteritems():
        if key == u'':
            raise 'Keys are mandatory'
        result += u'<ns1:{0}>'.format(key)
        if isinstance(val, OrderedDict):
            result += simple_dict_to_xml(val)
        else:
            result += u'{0}'.format(val)
        result += u'</ns1:{0}>'.format(key)
    return result

inner_data = prepare_data()
res  = soap_call(inner_data)
print res