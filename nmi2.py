import pycurl
import urllib
import urlparse
import StringIO


def doPost(query):
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
        print key,value

def doSale():
    query  = ""
    # Login Information
    query = query + "username=" + urllib.quote('jjuicewholesale') + "&"
    query += "password=" + urllib.quote('vapejjuice.com16') + "&"
    
    # Sales Information
    query += "customer_vault_id=" + urllib.quote("438771887") + "&"
    query += "amount=" + urllib.quote('{0:.2f}'.format(float("11"))) + "&"
    query += "currency=" + urllib.quote("USD") + "&"
    query += "orderid=" + urllib.quote("SAJ202") + "&"
    return doPost(query)

doSale()


