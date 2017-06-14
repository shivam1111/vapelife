#!/usr/bin/env python
# -*- coding: utf-8 -*-
from suds.client import Client
import logging
from datetime import datetime
import pytz

def return_RequestedPackageLineItem(Weight,PhysicalPackaging,GroupPackageCount,GroupNumber,unit='LB'):
    RequestedPackageLineItem = client.factory.create('RequestedPackageLineItem')
    RequestedPackageLineItem.GroupNumber = GroupNumber
    Weights = client.factory.create('Weight')
    Weights.Value = Weight
    Weights.Units = unit
    RequestedPackageLineItem.Weight=Weights
    RequestedPackageLineItem.PhysicalPackaging = PhysicalPackaging
    RequestedPackageLineItem.GroupPackageCount = GroupPackageCount
    return RequestedPackageLineItem
    
def create_Contact(contact):
    if contact == None:contact = {}
    Contact = client.factory.create('Contact')
    for i in Contact.__keylist__:
        Contact[i] = contact.get(i,None)
    return Contact

def create_Address(address):
    if address == None: address = {}
    if not address.get('StreetLines',False):
        address['StreetLines'] = []
    Address = client.factory.create('Address')
    for i in Address.__keylist__:
        Address[i] = address.get(i,None)
    return Address

def create_Party(**kwarg): #kwarg = {'account_number':<>,'contact':{},'address':{}}
    Party = client.factory.create('Party')
    Party.AccountNumber = kwarg.get('account_number',None)
    Party.Tins = kwarg.get('tin',[])
    Party.Contact = create_Contact(kwarg.get('contact',None))
    Party.Address = create_Address(kwarg.get('address',None))
    return Party
    
def return_RequestedShipment(timezones='US/Central',drop_off_type = 'REGULAR_PICKUP',service_type = 'FEDEX_GROUND',packaging_type = 'YOUR_PACKAGING',
    unit = 'LB',weight=0,currency=None,shipper_account_number=None,shipper_contact = None,shipper_address=None,
    recipient_account_number = None,recipient_contact = None,recipient_address = None,RequestedPackageLineItem = []):
    timestamps  = datetime.now(pytz.timezone(timezones)).isoformat()
    RequestedShipment = client.factory.create('RequestedShipment')
    print RequestedShipment
    RequestedShipment.ShipTimestamp = timestamps
    RequestedShipment.EdtRequestType = 'NONE'
    RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'
    DropoffType  = client.factory.create('DropoffType')
#    DropoffType
#    BUSINESS_SERVICE_CENTER = "BUSINESS_SERVICE_CENTER"
#    DROP_BOX = "DROP_BOX"
#    REGULAR_PICKUP = "REGULAR_PICKUP"
#    REQUEST_COURIER = "REQUEST_COURIER"
#    STATION = "STATION"
    RequestedShipment.RequestedPackageLineItems = RequestedPackageLineItem
    RequestedShipment.DropoffType = drop_off_type
    ServiceType = client.factory.create('ServiceType')
    ServiceType = service_type
    RequestedShipment.ServiceType = ServiceType
#    EUROPE_FIRST_INTERNATIONAL_PRIORITY = "EUROPE_FIRST_INTERNATIONAL_PRIORITY"
#    FEDEX_1_DAY_FREIGHT = "FEDEX_1_DAY_FREIGHT"
#    FEDEX_2_DAY = "FEDEX_2_DAY"
#    FEDEX_2_DAY_AM = "FEDEX_2_DAY_AM"
#    FEDEX_2_DAY_FREIGHT = "FEDEX_2_DAY_FREIGHT"
#    FEDEX_3_DAY_FREIGHT = "FEDEX_3_DAY_FREIGHT"
#    FEDEX_DISTANCE_DEFERRED = "FEDEX_DISTANCE_DEFERRED"
#    FEDEX_EXPRESS_SAVER = "FEDEX_EXPRESS_SAVER"
#    FEDEX_FIRST_FREIGHT = "FEDEX_FIRST_FREIGHT"
#    FEDEX_FREIGHT_ECONOMY = "FEDEX_FREIGHT_ECONOMY"
#    FEDEX_FREIGHT_PRIORITY = "FEDEX_FREIGHT_PRIORITY"
#    FEDEX_GROUND = "FEDEX_GROUND"
#    FEDEX_NEXT_DAY_AFTERNOON = "FEDEX_NEXT_DAY_AFTERNOON"
#    FEDEX_NEXT_DAY_EARLY_MORNING = "FEDEX_NEXT_DAY_EARLY_MORNING"
#    FEDEX_NEXT_DAY_END_OF_DAY = "FEDEX_NEXT_DAY_END_OF_DAY"
#    FEDEX_NEXT_DAY_FREIGHT = "FEDEX_NEXT_DAY_FREIGHT"
#    FEDEX_NEXT_DAY_MID_MORNING = "FEDEX_NEXT_DAY_MID_MORNING"
#    FIRST_OVERNIGHT = "FIRST_OVERNIGHT"
#    GROUND_HOME_DELIVERY = "GROUND_HOME_DELIVERY"
#    INTERNATIONAL_ECONOMY = "INTERNATIONAL_ECONOMY"
#    INTERNATIONAL_ECONOMY_FREIGHT = "INTERNATIONAL_ECONOMY_FREIGHT"
#    INTERNATIONAL_FIRST = "INTERNATIONAL_FIRST"
#    INTERNATIONAL_PRIORITY = "INTERNATIONAL_PRIORITY"
#    INTERNATIONAL_PRIORITY_FREIGHT = "INTERNATIONAL_PRIORITY_FREIGHT"
#    PRIORITY_OVERNIGHT = "PRIORITY_OVERNIGHT"
#    SAME_DAY = "SAME_DAY"
#    SAME_DAY_CITY = "SAME_DAY_CITY"
#    SMART_POST = "SMART_POST"
#    STANDARD_OVERNIGHT = "STANDARD_OVERNIGHT"    
    PackagingType = client.factory.create('PackagingType')
#     FEDEX_10KG_BOX = "FEDEX_10KG_BOX"
#    FEDEX_25KG_BOX = "FEDEX_25KG_BOX"
#    FEDEX_BOX = "FEDEX_BOX"
#    FEDEX_ENVELOPE = "FEDEX_ENVELOPE"
#    FEDEX_EXTRA_LARGE_BOX = "FEDEX_EXTRA_LARGE_BOX"
#    FEDEX_LARGE_BOX = "FEDEX_LARGE_BOX"
#    FEDEX_MEDIUM_BOX = "FEDEX_MEDIUM_BOX"
#    FEDEX_PAK = "FEDEX_PAK"
#    FEDEX_SMALL_BOX = "FEDEX_SMALL_BOX"
#    FEDEX_TUBE = "FEDEX_TUBE"
#    YOUR_PACKAGING = "YOUR_PACKAGING"    
    PackagingType = packaging_type
    RequestedShipment.PackagingType = PackagingType
    Weight = client.factory.create('Weight')
    WeightUnits = client.factory.create('WeightUnits')
# (WeightUnits){
#    KG = "KG"
#    LB = "LB"
#  }
    WeightUnits = unit
    Weight.Units = WeightUnits
    Weight.Value = weight
    RequestedShipment.TotalWeight = Weight
    PreferredCurrency = currency
    RequestedShipment.PackageCount = 2
    RequestedShipment.PreferredCurrency = PreferredCurrency
    RequestedShipment.Shipper = create_Party(account_number = shipper_account_number,contact = shipper_contact,address = shipper_address)
    RequestedShipment.Recipient = create_Party(account_number = recipient_account_number,contact = recipient_contact,address = recipient_address)
    return RequestedShipment
    
def return_ConsolidationKey():
    ConsolidationKey = client.factory.create('ConsolidationKey')
    return ConsolidationKey

def return_VariableOptions(type=[]):
    VariableOptions = client.factory.create('ServiceOptionType')
    VariableOptions = type
#     FEDEX_ONE_RATE = "FEDEX_ONE_RATE"
#     FREIGHT_GUARANTEE = "FREIGHT_GUARANTEE"
#     SATURDAY_DELIVERY = "SATURDAY_DELIVERY"
#     SMART_POST_ALLOWED_INDICIA = "SMART_POST_ALLOWED_INDICIA"
#     SMART_POST_HUB_ID = "SMART_POST_HUB_ID"    
    return VariableOptions


def return_ServiceOptionType(type=[]):
    ServiceOptionType = client.factory.create('ServiceOptionType')
#     FEDEX_ONE_RATE = "FEDEX_ONE_RATE"
#     FREIGHT_GUARANTEE = "FREIGHT_GUARANTEE"
#     SATURDAY_DELIVERY = "SATURDAY_DELIVERY"
#     SMART_POST_ALLOWED_INDICIA = "SMART_POST_ALLOWED_INDICIA"
#     SMART_POST_HUB_ID = "SMART_POST_HUB_ID"
    ServiceOptionType = type
    return ServiceOptionType


def return_CarrierCodeType(types=None):
    CarrierCodeType = client.factory.create('CarrierCodeType')
#     FDXE – FedEx Express Tracking Requests
#     FDXG – FedEx Ground Tracking Requests
#     FDXC – FedEx Cargo Tracking Requests
#     FXCC – FedEx Custom Critical Tracking Requests
#     FXFR – FedEx Freight Tracking Requests
    CarrierCodeType = types
    return CarrierCodeType


def return_VersionId(ServiceId,Major,Intermediate,Minor):
    VersionId = client.factory.create('VersionId')
    VersionId.ServiceId = ServiceId
    VersionId.Major = Major
    VersionId.Intermediate = Intermediate
    VersionId.Minor = Minor
    return VersionId
    
def return_TransactionDetail(CustomerTransactionId,LanguageCode=None,LocaleCode=None):
    TransactionDetail = client.factory.create('TransactionDetail')
    TransactionDetail.CustomerTransactionId = CustomerTransactionId
    Localization = client.factory.create('Localization')
    Localization.LanguageCode = LanguageCode
    Localization.LocaleCode = LocaleCode
    TransactionDetail.Localization = Localization
    return TransactionDetail

def return_credential_detail(key,password,client):
    WebAuthenticationDetail = client.factory.create('WebAuthenticationDetail')
    ParentCredential = client.factory.create('WebAuthenticationCredential')
    ParentCredential.Key = key
    ParentCredential.Password = password
    WebAuthenticationDetail.UserCredential = ParentCredential
    return WebAuthenticationDetail
    
def return_ClientDetail(AccountNumber,MeterNumber,client,IntegratorId=None,Region=None):
    ClientDetail = client.factory.create('ClientDetail')
    ClientDetail.AccountNumber = AccountNumber
    ClientDetail.MeterNumber = MeterNumber
    if IntegratorId:
        ClientDetail.IntegratorId = IntegratorId
    if Region:
        ExpressRegionCode = client.factory.create('ExpressRegionCode')
        ExpressRegionCode.value = Region
        ClientDetail.Region = Region
        #possible values 
#         APAC = "APAC"
#          CA = "CA"
#          EMEA = "EMEA"
#          LAC = "LAC"
#          US = "US"
    return ClientDetail
    
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
url = 'file:wsdl/RateService_v18.wsdl'
client = Client(url,cache=None)
WebAuthenticationDetail =  return_credential_detail('pJWiO448Vp2l5Lwu','MJNnRP77zoRGMarukZiEXBlsU',client)
ClientDetail = return_ClientDetail('510087623','118694899',client,'123','US')
TransactionDetail = return_TransactionDetail('transaction_number','EN','US')
VersionId = return_VersionId('crs','18','0','0')
CarrierCodeType = return_CarrierCodeType('FDXE')
VariableOptions = return_ServiceOptionType(['FEDEX_ONE_RATE'])
ConsolidationKey =  return_ConsolidationKey()
RequestedPackageLineItem = []
RequestedPackageLineItem.append(return_RequestedPackageLineItem('23','BOX','2','1'))
RequestedShipment = return_RequestedShipment(shipper_account_number='510087623',shipper_contact={
                                                                             'PersonName':'Shivam Goyal',
                                                                             'CompanyName':'JJUICE',
                                                                             'PhoneNumber':'9560566121',
                                                                             'EMailAddress':'shivam1111@gmail.com'
                                                                             },shipper_address={
                                                                                                'StreetLines':['12411 South 265 West','Suite C'],
                                                                                                'City':'Draper',
                                                                                                'StateOrProvinceCode':'UT',
                                                                                                'PostalCode':'84020',
                                                                                                'CountryCode':'US',
                                                                                                'CountryName':'United States of America',
                                                                                                'Residential':False
                                                                                                },recipient_account_number=None,recipient_contact={
                                                                             'PersonName':"Phillips 66 (Lucky's) (Orem,UT)",
                                                                             'CompanyName':'JG',
                                                                             'PhoneNumber':'9560566121',
                                                                             'EMailAddress':'shivam.goyal@jginfosystems.com'
                                                                             },recipient_address={
                                                                                                'StreetLines':['1520 S. State St'],
                                                                                                'City':'Orem',
                                                                                                'StateOrProvinceCode':'UT',
                                                                                                'PostalCode':'84097',
                                                                                                'CountryCode':'US',
                                                                                                'CountryName':'United States of America',
                                                                                                'Residential':False
                                                                                                },RequestedPackageLineItem = RequestedPackageLineItem)
l = client.service.getRates(WebAuthenticationDetail = WebAuthenticationDetail,ClientDetail = ClientDetail,
Version = VersionId,
TransactionDetail = TransactionDetail,
ReturnTransitAndCommit = False,
CarrierCodes = CarrierCodeType,
VariableOptions = VariableOptions,
ConsolidationKey = ConsolidationKey,
RequestedShipment = RequestedShipment)
# print l
# print RequestedShipment
