###########################################################
#                                                         #
#  D I S C L A I M E R                                    #
#                                                         #
#  WARNING: ANY USE BY YOU OF THE SAMPLE CODE PROVIDED    #
#  IS AT YOUR OWN RISK.                                   #
#                                                         #
#  The code is  provided  "as is" without                 #
#  warranty of any kind, either express or implied,       #
#  including but not limited to the implied warranties    #
#  of merchantability and/or fitness for a particular     #
#  purpose.                                               #
#                                                         #
#                                                         #
###########################################################



import pycurl
import urllib
import urlparse
import StringIO


class gwapi():

    def __init__(self):
        self.login= dict()
        self.order = dict()
        self.billing = dict()
        self.shipping = dict()
        self.responses = dict()

    def setLogin(self,username,password):
        self.login['password'] = password
        self.login['username'] = username

    def setOrder(self, orderid, orderdescription, tax, shipping, ponumber,ipadress):
        self.order['orderid'] = orderid;
        self.order['orderdescription'] = orderdescription
        self.order['shipping'] = '{0:.2f}'.format(float(shipping))
        self.order['ipaddress'] = ipadress
        self.order['tax'] = '{0:.2f}'.format(float(tax))
        self.order['ponumber'] = ponumber


    def setBilling(self,
            firstname,
            lastname,
            company,
            address1,
            address2,
            city,
            state,
            zip,
            country,
            phone,
            fax,
            email,
            website):
        self.billing['firstname'] = firstname
        self.billing['lastname']  = lastname
        self.billing['company']   = company
        self.billing['address1']  = address1
        self.billing['address2']  = address2
        self.billing['city']      = city
        self.billing['state']     = state
        self.billing['zip']       = zip
        self.billing['country']   = country
        self.billing['phone']     = phone
        self.billing['fax']       = fax
        self.billing['email']     = email
        self.billing['website']   = website

    def setShipping(self,firstname,
            lastname,
            company,
            address1,
            address2,
            city,
            state,
            zipcode,
            country,
            email):
        self.shipping['firstname'] = firstname
        self.shipping['lastname']  = lastname
        self.shipping['company']   = company
        self.shipping['address1']  = address1
        self.shipping['address2']  = address2
        self.shipping['city']      = city
        self.shipping['state']     = state
        self.shipping['zip']       = zipcode
        self.shipping['country']   = country
        self.shipping['email']     = email


    def doSale(self,amount, ccnumber, ccexp, cvv=''):

        query  = ""
        # Login Information

        query = query + "username=" + urllib.quote(self.login['username']) + "&"
        query += "password=" + urllib.quote(self.login['password']) + "&"
        # Sales Information
        query += "ccnumber=" + urllib.quote(ccnumber) + "&"
        query += "ccexp=" + urllib.quote(ccexp) + "&"
        query += "amount=" + urllib.quote('{0:.2f}'.format(float(amount))) + "&"
        if (cvv!=''):
            query += "cvv=" + urllib.quote(cvv) + "&"
        # Order Information
        for key,value in self.order.iteritems():
            query += key +"=" + urllib.quote(str(value)) + "&"

        # Billing Information
        for key,value in self.billing.iteritems():
            query += key +"=" + urllib.quote(str(value)) + "&"

        # Shipping Information
        for key,value in self.shipping.iteritems():
            query += key +"=" + urllib.quote(str(value)) + "&"

        query += "type=sale"
        return self.doPost(query)



    def doPost(self,query):
        responseIO = StringIO.StringIO()
        curlObj = pycurl.Curl()
        curlObj.setopt(pycurl.POST,1)
        curlObj.setopt(pycurl.CONNECTTIMEOUT,30)
        curlObj.setopt(pycurl.TIMEOUT,30)
        curlObj.setopt(pycurl.HEADER,0)
        curlObj.setopt(pycurl.SSL_VERIFYPEER,0)
        curlObj.setopt(pycurl.WRITEFUNCTION,responseIO.write);

        curlObj.setopt(pycurl.URL,"https://secure.nmi.com/api/transact.php")

        curlObj.setopt(pycurl.POSTFIELDS,query)

        curlObj.perform()

        data = responseIO.getvalue()
        temp = urlparse.parse_qs(data)
        for key,value in temp.iteritems():
            self.responses[key] = value[0]
        return self.responses['response']

# NOTE: your username and password should replace the ones below
gw = gwapi()
gw.setLogin("demo", "password");

gw.setBilling("John","Smith","Acme, Inc.","123 Main St","Suite 200", "Beverly Hills",
        "CA","90210","US","555-555-5555","555-555-5556","support@example.com",
        "www.example.com")
gw.setShipping("Mary","Smith","na","124 Shipping Main St","Suite Ship", "Beverly Hills",
        "CA","90210","US","support@example.com")
gw.setOrder("1234","Big Order",1, 2, "PO1234","65.192.14.10")

r = gw.doSale("5.00","4111111111111111","1212",'999')
print gw.responses['response']

if (int(gw.responses['response']) == 1) :
    print "Approved"
elif (int(gw.responses['response']) == 2) :
    print "Declined"
elif (int(gw.responses['response']) == 3) :
    print "Error"