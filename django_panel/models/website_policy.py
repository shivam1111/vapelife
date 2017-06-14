from openerp import models, fields, api, _
from helpers import BinaryS3Field,delete_object_bucket,get_bucket_location
from openerp.exceptions import except_orm

class website_policy(models.Model):
    _name = "website.policy"
    _description="Website Policy"
    _order = "sequence"

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
        return super(website_policy,self).unlink()
    
    sequence = fields.Integer('Sequence') 
    name = fields.Char('Name',required=True)
    file_name = fields.Char('File Name')
    description = fields.Text('Description')
    datas = BinaryS3Field(string="Image",key_name=False)