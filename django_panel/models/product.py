from openerp import models, fields, api, _
from helpers import BinaryS3Field,delete_object_bucket,get_bucket_location
from openerp.exceptions import except_orm
import json

class product_product(models.Model):
    _inherit = "product.product"
    _description = "Adding S3 Object"


    @api.multi
    def get_product_availability(self):
        res = {}
        for i in self:
            res.update({
                i.id:{'virtual_available':i.virtual_available}
            })
        return json.dumps(res)


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
        return super(product_attribute_value,self).unlink()

    file_name = fields.Char(string = "File Name")
    datas = BinaryS3Field(string = "Image",key_name = False)
        