from openerp import models, fields, api, _
from helpers import BinaryS3Field,delete_object_bucket,get_bucket_location
from openerp.exceptions import except_orm
import urlparse,hashlib

class s3_object(models.Model):
    _name = "s3.object"
    _description = "Single S3 Object"
    _rec_name = "file_name"
    
    @api.multi
    def unlink(self):
        for rec in self:
            try:
                root_bucket = self.env['ir.config_parameter'].get_param('root_bucket','jjuice-django')
                assert root_bucket, "Sorry the root bucket is not available" 
                access_key_id = self.env['ir.config_parameter'].get_param('aws_access_id')
                secret_access_key = self.env['ir.config_parameter'].get_param('aws_secret_key')
                assert access_key_id and secret_access_key, "Invalid Credentials"
                delete_object_bucket(self._table,self.id,access_key_id,secret_access_key,root_bucket)
            except AssertionError as e:
                raise except_orm('Error',e)
        return super(s3_object,self).unlink()
    
    file_name = fields.Char(string = "File Name")
    datas = BinaryS3Field(string = "Image",key_name = False)    
    sequence = fields.Integer(string="Sequence")
    attribute_id = fields.Many2one('product.attribute.value','Attribute')
    flavor_id = fields.Many2one('product.flavors','Flavor')
    is_featured_item = fields.Boolean("Featured Item")
    aboutus_banner = fields.Boolean('Is About us Banner ?')
    contactus_banner = fields.Boolean('Is Contact us Banner ?')
    customerreview_banner = fields.Boolean('Is Customer Review us Banner ?')
    privacy_policy_banner = fields.Boolean("Is Privacy Policy Banner")
    terms_conditions_banner = fields.Boolean("Is Terms & Conditions Banner ?")
    search_banner = fields.Boolean('Is Search Banner?')
    checkout_banner = fields.Boolean('Is Checkout Banner?')
    shipping_returns_policy_banner = fields.Boolean('Is Shipping & Returns Policy Banner ?')
    contactus_banner_500340 = fields.Boolean('Is Contact Us Image (500x340) ?')