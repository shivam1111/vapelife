import pycurl,urllib,urlparse,StringIO

def doPost(query,url):
    responseIO = StringIO.StringIO()
    curlObj = pycurl.Curl()
    curlObj.setopt(pycurl.POST,1)
    curlObj.setopt(pycurl.CONNECTTIMEOUT,30)
    curlObj.setopt(pycurl.TIMEOUT,30)
    curlObj.setopt(pycurl.HEADER,0)
    curlObj.setopt(pycurl.SSL_VERIFYPEER,0)
    curlObj.setopt(pycurl.WRITEFUNCTION,responseIO.write);
    curlObj.setopt(pycurl.URL,url)
    curlObj.setopt(pycurl.POSTFIELDS,query)
    curlObj.perform()
    data = responseIO.getvalue()
    return data


def get_vault_detail(username,pwd,vault_id):
    url =  "https://secure.networkmerchants.com/api/query.php"
    query  = ""
    # Login Information
    query = query + "username=" + urllib.quote(username) + "&"
    query += "password=" + urllib.quote(pwd) + "&"
    query += "report_type=" + urllib.quote("customer_vault") + "&"
    query += "customer_vault_id=" + urllib.quote(vault_id) 
    data = doPost(query,url)
    return data


def create_vault(username,pwd,vals):
    url = "https://secure.nmi.com/api/transact.php"
    query  = ""
    query = query + "username=" + urllib.quote(username) + "&"
    query += "password=" + urllib.quote(pwd) + "&"
    query += "customer_vault=" + urllib.quote("add_customer") + "&"
    for key,val in vals.iteritems():
        if val:
            query+= key +"="+  urllib.quote(val) + "&"
    return doPost(query,url)

def delete_vault(username,pwd,vault_id):
    url = "https://secure.nmi.com/api/transact.php"
    query  = ""
    query = query + "username=" + urllib.quote(username) + "&"
    query += "password=" + urllib.quote(pwd) + "&"
    query += "customer_vault=" + urllib.quote("delete_customer") + "&" 
    query += "customer_vault_id=" + urllib.quote(vault_id)
    return doPost(query,url)    
       
def make_payment(username,pwd,vault_id,amt,ref=None):    
    url = "https://secure.nmi.com/api/transact.php"
    query  = ""
    query = query + "username=" + urllib.quote(username) + "&"
    query += "password=" + urllib.quote(pwd) + "&"
    # Sales Information
    query += "customer_vault_id=" + urllib.quote(vault_id) + "&"
    query += "amount=" + urllib.quote('{0:.2f}'.format(float(amt))) + "&"
    query += "currency=" + urllib.quote("USD") + "&"
    if ref:
        query += "orderid=" + urllib.quote(ref)   
    return doPost(query,url)                
    