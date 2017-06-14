from openerp.fields import Binary
import boto3,botocore
import urlparse,os,base64,hashlib,logging
from openerp.exceptions import except_orm

_logger = logging.getLogger(__name__)

class BinaryS3Field(Binary):
    def _data_get(self,record):
        read=None
        key_name = self.key_name or record._table
        try:
            root_bucket = record.env['ir.config_parameter'].sudo().get_param('root_bucket','jjuice-django')
            assert root_bucket, "Sorry the root bucket is not available" 
            access_key_id = record.env['ir.config_parameter'].sudo().get_param('aws_access_id')
            secret_access_key = record.env['ir.config_parameter'].sudo().get_param('aws_secret_key')
            assert access_key_id and secret_access_key, "Invalid Credentials"
            s3_conn = get_s3_client(access_key_id,secret_access_key)
            for i in  record:
                exists = lookup(s3_conn,root_bucket,os.path.join(key_name,str(i.id)))
                if exists:        
                    bin_value  = s3_conn.get_object(Bucket=root_bucket, Key = os.path.join(key_name,str(i.id)))
                    read = base64.b64encode(bin_value.get('Body').read())
                    record._cache[self] = read
        except AssertionError as e:
            raise except_orm('Error',e)
    
    def _data_set(self,record):
        key_name = self.key_name or record._table
        try:
            root_bucket = record.env['ir.config_parameter'].sudo().get_param('root_bucket','jjuice-django')
            assert root_bucket, "Sorry the root bucket is not available" 
            access_key_id = record.env['ir.config_parameter'].sudo().get_param('aws_access_id')
            secret_access_key = record.env['ir.config_parameter'].sudo().get_param('aws_secret_key')
            assert access_key_id and secret_access_key, "Invalid Credentials"
            # Establish Connection
            s3_conn = get_s3_client(access_key_id,secret_access_key)
            if record._cache[self]:
                bin_value = record._cache[self].decode('base64')
            else:
                delete_conn_object_bucket(s3_conn,key_name,record.id,root_bucket)
                return
            # Checking whether configured folder exist
            # For checking if folder is present it has to end with forward slash        
            exists = lookup(s3_conn,root_bucket,os.path.join(key_name,'')) # adding slash safely(s3_conn,bucket,key='/'):
            if not exists:
                s3_conn.put_object(Bucket=root_bucket, Key = os.path.join(key_name,''),Body='')
            s3_conn.put_object(Bucket=root_bucket, Key = os.path.join(key_name,str(record.id)),Body=bin_value)
        except AssertionError as e:
            raise except_orm('Error',e)
    compute = _data_get
    inverse = _data_set
    store=False


def get_url(bucket_location,bucket,key,fname):
    return os.path.join(bucket_location,bucket,key,fname)

def get_bucket_location(access_key_id,secret_access_key,bucket):
    # This method just takes in bucket name and then joins accesss key and id with bucket to create a standard url
    # accepted by other method
    # accpeted location is -: amazons3://access_key_id:secret_access_key@jjuice-django
    return ('').join(['amazons3://',access_key_id,":",secret_access_key,"@",bucket])

def get_s3_client(access_key_id,secret_access_key):
    s3_conn = boto3.client(
        's3',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )
    return s3_conn

def lookup(s3_conn,bucket,key='/'):
    # checks is a bucket exists or not
    try:
        result = s3_conn.get_object(
            Bucket=bucket,
            Key=key # this will add a forward slash if not present
            )
        return True
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        _logger.exception(e)
        return False

def put_object_bucket(location,key,value):
    # location = amazons3://access_key_id:secret_access_key@bucket
    # Example = amazons3://access_key_id:secret_access_key@jjuice-django
    # value = content of the file
    # key = folder path inside bucket
    
    loc_parse = urlparse.urlparse(location)
    assert loc_parse.scheme == 'amazons3', \
        "This method is intended only for amazons3://"

    access_key_id = loc_parse.username
    secret_key = loc_parse.password

    if not access_key_id or not secret_key:
        assert False, \
            "Must define access_key_id and secret_access_key in amazons3:// scheme"
        
    s3_conn = get_s3_client(access_key_id,secret_key)
    bin_value = value.decode('base64')
    fname = hashlib.sha1(bin_value).hexdigest()
    # Checking whether configured folder exist
    # For checking if folder is present it has to end with forward slash
    exists = lookup(s3_conn,loc_parse.hostname,os.path.join(key,'')) # adding slash safely
    if exists:
        s3_conn.put_object(Bucket=loc_parse.hostname, Key = '/'.join([key,fname]),Body=bin_value)
    else:
        assert False, \
            "Probably the root bucket path or key does not exist or invalid"
    return fname

def get_object_bucket(location,key,fname):
    read = None
    if fname:
        loc_parse = urlparse.urlparse(location)
        assert loc_parse.scheme == 'amazons3', \
            "This method is intended only for amazons3://"
    
        access_key_id = loc_parse.username
        secret_key = loc_parse.password
    
        if not access_key_id or not secret_key:
            assert False, \
                "Must define access_key_id and secret_access_key in amazons3:// scheme"
            
        s3_conn = get_s3_client(access_key_id,secret_key)
        exists = lookup(s3_conn,loc_parse.hostname,'/'.join([key,fname])) 
        if exists:
            bin_value  = s3_conn.get_object(Bucket=loc_parse.hostname, Key = '/'.join([key,fname]))
            read = base64.b64encode(bin_value.get('Body').read())
    return read

def delete_conn_object_bucket(s3_conn,key,fname,root_bucket):
    delete = None
    if fname:
        delete = s3_conn.delete_object(Bucket=root_bucket, Key = os.path.join(key,str(fname)))
    return delete

def delete_object_bucket(key,fname,access_key_id,secret_access_key,root_bucket):
    delete = None
    if fname:
        s3_conn = get_s3_client(access_key_id,secret_access_key)             
        exists = lookup(s3_conn,root_bucket,os.path.join(key,str(fname))) 
        if exists:
            delete = delete_conn_object_bucket(s3_conn,key,fname,root_bucket)
    return delete    
