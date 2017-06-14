import time
import httplib
from datetime import datetime
from collections import OrderedDict
from constance import config

# You can use soap_call(prepare_data())
# With proper parameters to make a call to ShipService Version 15

def soap_call(inner_data):
    """Posts a soap call to Fedex Webservice Used in ShipRequest
    """
    to_send = u'''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://fedex.com/ws/ship/v15">
<SOAP-ENV:Body>{0}</SOAP-ENV:Body></SOAP-ENV:Envelope>'''.format(simple_dict_to_xml(inner_data)).encode('ascii', 'ignore')

    server = 'ws.fedex.com'
    if settings.CONFIG_FEDEX.use_test_server:
        server = 'wsbeta.fedex.com'
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


def prepare_data(
    name,
    address,
    phonenumber,
    city,
    state,
    zip_code,
    country,
    shipping_method,
    signature,
    cost,
    cart_id,
):
    """Sets the data for the soap call in shipping request, this one follows
    closely the PHP samples provided by Fedex.
    """
    KEY = settings.CONFIG_FEDEX.key
    PASSWORD = settings.CONFIG_FEDEX.password
    ACCOUNT_NUMBER = settings.CONFIG_FEDEX.account_number
    METER_NUMBER = settings.CONFIG_FEDEX.meter_number

    SERVICE_TYPE = shipping_method

    COMPANY_NAME = config.COMPANY_NAME_INTEGRATION_SERVICES
    COMPANY_PN = config.ODM_PHONE_NUMBER
    COMPANY_ADDRESS = config.ODM_WAREHOUSE_ADDRESS
    COMPANY_CITY = config.ODM_WAREHOUSE_CITY
    COMPANY_ZIPCODE = config.ODM_WAREHOUSE_ZIP_CODE
    COMPANY_STATE = config.ODM_WAREHOUSE_STATE
    COMPANY_COUNTRYCODE = config.ODM_WAREHOUSE_COUNTRY
    PERSON_NAME = name
    PERSON_PN = phonenumber
    CLIENT_ADDRESS = address
    CLIENT_CITY = city
    CLIENT_ZIPCODE = zip_code
    CLIENT_STATE = state
    CLIENT_COUNTRYCODE = country

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


    if signature:
        req_pack['SpecialServicesRequested'] = OrderedDict([
            (u'SpecialServiceTypes', u'SIGNATURE_OPTION'),
            (u'SignatureOptionDetail', OrderedDict([
                (u'OptionType', u'DIRECT')
            ]))
        ])

    req_ship = OrderedDict([
        (u'ShipTimestamp', u'{0}'.format(time.strftime("%Y-%m-%dT%H:%M:%S"), datetime.now())),
        (u'DropoffType', u'REGULAR_PICKUP'),
        (u'ServiceType', SERVICE_TYPE),
        (u'PackagingType', u'YOUR_PACKAGING'),
        (u'Shipper', shipper),
        (u'Recipient', recipient),
        (u'ShippingChargesPayment', charges_payment),
    ])

    if country != u'US':
        # In case of international handling
        customclearance = OrderedDict([
            (u'DutiesPayment', OrderedDict([
                (u'PaymentType', u'SENDER'),
                (u'Payor', OrderedDict([
                    (u'ResponsibleParty', OrderedDict([
                        (u'AccountNumber', settings.CONFIG_FEDEX.account_number),
                        (u'Address', OrderedDict([
                            (u'CountryCode', config.ODM_WAREHOUSE_COUNTRY),
                        ])),
                    ])),
                ])),
            ])),
            (u'DocumentContent', u'NON_DOCUMENTS'),
            (u'CustomsValue', OrderedDict([
                (u'Currency', u'USD'),
                (u'Amount', cost),
            ])),
            (u'Commodities', OrderedDict([
                (u'NumberOfPieces', u'1'),
                (u'Description', u'OndadeMar Element'),
                (u'CountryOfManufacture', config.ODM_WAREHOUSE_COUNTRY),
                (u'Weight', OrderedDict([
                    (u'Units', u'LB'),
                    (u'Value', config.DEFAULT_SHIPPING_WEIGHT),
                ])),
                (u'Quantity', u'1'),
                (u'QuantityUnits', u'EA'),
                (u'UnitPrice', OrderedDict([
                    (u'Currency', u'USD'),
                    (u'Amount', cost),
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
