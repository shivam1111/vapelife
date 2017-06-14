# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from helpers import BinaryS3Field,delete_object_bucket,get_bucket_location

class django_panel_settings(osv.osv_memory):
    _name = 'django.panel.settings'
    _inherit = 'res.config.settings'
    
    def set_default_aws_access_id(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'aws_access_id', (myself.aws_access_id or '').strip(), groups=['base.group_system'], context=None)

    def get_default_aws_access_id(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        aws_access_id = params.get_param(cr, uid, 'aws_access_id',default='',context=context)        
        return dict(aws_access_id=aws_access_id)

    def set_default_website_url(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'website_url', (myself.website_url or '').strip(), groups=['base.group_system'], context=None)

    def get_default_website_url(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        website_url = params.get_param(cr, uid, 'website_url',default='',context=context)
        return dict(website_url=website_url)

    def set_default_website_username(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'website_username', (myself.website_username or '').strip(), groups=['base.group_system'], context=None)

    def get_default_website_username(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        website_username = params.get_param(cr, uid, 'website_username',default='',context=context)
        return dict(website_username=website_username)

    def set_default_website_pwd(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'website_pwd', (myself.website_pwd or '').strip(), groups=['base.group_system'], context=None)

    def get_default_website_pwd(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        website_pwd = params.get_param(cr, uid, 'website_pwd',default='',context=context)
        return dict(website_pwd=website_pwd)

    def set_default_aws_secret_key(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'aws_secret_key', (myself.aws_secret_key or '').strip(), groups=['base.group_system'], context=None)

    def get_default_aws_secret_key(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        aws_secret_key = params.get_param(cr, uid, 'aws_secret_key',default='',context=context)        
        return dict(aws_secret_key=aws_secret_key) 
    
#     def set_default_website_banner_key(self,cr,uid,ids,context=None):
#         params = self.pool.get('ir.config_parameter')
#         myself = self.browse(cr,uid,ids[0],context=context)
#         params.set_param(cr, uid, 'website_banner_key', (myself.website_banner_key or '').strip(), groups=['base.group_system'], context=None)
# 
#     def get_default_website_banner_key(self,cr,uid,ids,context=None):
#         params = self.pool.get('ir.config_parameter')
#         website_banner_key = params.get_param(cr, uid, 'website_banner_key',default='',context=context)        
#         return dict(website_banner_key=website_banner_key)                                                                                                   

    def set_default_root_bucket(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'root_bucket', (myself.root_bucket or '').strip(), groups=['base.group_system'], context=None)
 
    def get_default_root_bucket(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        root_bucket = params.get_param(cr, uid, 'root_bucket',default='',context=context)        
        return dict(root_bucket=root_bucket)                                                                                                   

    def set_default_aws_base_url(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'aws_base_url', (myself.aws_base_url or '').strip(), groups=['base.group_system'], context=None)
 
    def get_default_aws_base_url(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        aws_base_url = params.get_param(cr, uid, 'aws_base_url',default='',context=context)        
        return dict(aws_base_url=aws_base_url)                                                                                                   

#     def set_default_website_policy_key(self,cr,uid,ids,context=None):
#         params = self.pool.get('ir.config_parameter')
#         myself = self.browse(cr,uid,ids[0],context=context)
#         params.set_param(cr, uid, 'website_policy_key', (myself.website_policy_key or '').strip(), groups=['base.group_system'], context=None)
# 
#     def get_default_website_policy_key(self,cr,uid,ids,context=None):
#         params = self.pool.get('ir.config_parameter')
#         website_policy_key = params.get_param(cr, uid, 'website_policy_key',default='',context=context)        
#         return dict(website_policy_key=website_policy_key)

    def set_default_meta_keywords(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'meta_keywords', (myself.meta_keywords or '').strip(), groups=['base.group_system'], context=None)

    def get_default_meta_keywords(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        meta_keywords = params.get_param(cr, uid, 'meta_keywords',default='',context=context)        
        return dict(meta_keywords=meta_keywords)                                                                                                       

    def set_default_meta_description(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'meta_description', (myself.meta_description or '').strip(), groups=['base.group_system'], context=None)

    def get_default_meta_description(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        meta_description = params.get_param(cr, uid, 'meta_description',default='',context=context)        
        return dict(meta_description=meta_description)

    def set_default_site_name(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        myself = self.browse(cr,uid,ids[0],context=context)
        params.set_param(cr, uid, 'site_name', (myself.site_name or '').strip(), groups=['base.group_system'], context=None)

    def get_default_site_name(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        site_name = params.get_param(cr, uid, 'site_name',default='',context=context)        
        return dict(site_name=site_name)                                                                                                                
                                                                                                              
    def set_default_attribute_value_ids(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        params = self.pool.get('ir.config_parameter')
        attribute_value_ids = map(lambda x:x.id,myself.attribute_value_ids)
        params.set_param(cr, uid, 'attribute_value_ids', (attribute_value_ids), groups=['base.group_system'], context=None)                                                                                      
    
    def get_default_attribute_value_ids(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        try:
            attribute_value_ids = params.get_param(cr, uid, 'attribute_value_ids',default='[]',context=context)
            return dict(attribute_value_ids=[(6,0,eval(attribute_value_ids))])
        except Exception as e:
            raise osv.except_osv('Error','Please check the value of Volumes not available for Retailers. It is invalid!')        
    
    def set_default_mailing_list_id(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        params = self.pool.get('ir.config_parameter')
        params.set_param(cr, uid, 'mailing_list_id', (myself.mailing_list_id.id), groups=['base.group_system'], context=None)                                                                                      
    
    def get_default_mailing_list_id(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        mailing_list_id = params.get_param(cr, uid, 'mailing_list_id',default=[],context=context)
        try:
            return dict(mailing_list_id=eval(mailing_list_id))
        except Exception as e:
            return []
     
    def _get_domain_volume(self,context=None):
        # We have access to self.env in this context.
        ids = self.env.ref('jjuice.attribute_vol').id
        return [('attribute_id','=', ids)]

    def set_default_attributes_available_ids(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        params = self.pool.get('ir.config_parameter')
        attributes_available_ids = map(lambda x:x.id,myself.attributes_available_ids)
        params.set_param(cr, uid, 'attributes_available_ids', (attributes_available_ids), groups=['base.group_system'], context=None)                                                                                      
    
    def get_default_attributes_available_ids(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        try:
            attributes_available_ids = params.get_param(cr, uid, 'attributes_available_ids',default='[]',context=context)
            return dict(attributes_available_ids=[(6,0,eval(attributes_available_ids))])
        except Exception as e:
            raise osv.except_osv('Error','Please check the value of Volumes available for website display . It is invalid!')        

    def set_default_aboutus_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('aboutus_banner','=',True),('id','!=',myself.aboutus_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.aboutus_banner.id,{'aboutus_banner':True})
    
    def get_default_aboutus_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('aboutus_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(aboutus_banner=s3_object_ids[0])
        else:
            return dict(aboutus_banner=False)

    def set_default_checkout_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('checkout_banner','=',True),('id','!=',myself.checkout_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.checkout_banner.id,{'checkout_banner':True})
    
    def get_default_checkout_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('checkout_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(checkout_banner=s3_object_ids[0])
        else:
            return dict(checkout_banner=False)        

    def set_default_contactus_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('contactus_banner','=',True),('id','!=',myself.contactus_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.contactus_banner.id,{'contactus_banner':True})
    
    def get_default_contactus_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('contactus_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(contactus_banner=s3_object_ids[0])
        else:
            return dict(contactus_banner=False)        

    def set_default_customerreview_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('customerreview_banner','=',True),('id','!=',myself.customerreview_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.customerreview_banner.id,{'customerreview_banner':True})
    
    def get_default_customerreview_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('customerreview_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(customerreview_banner=s3_object_ids[0])
        else:
            return dict(customerreview_banner=False)                

    def set_default_promo_business_ids(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        params = self.pool.get('ir.config_parameter')
        promo_business_ids = map(lambda x:x.id,myself.promo_business_ids)
        params.set_param(cr, uid, 'promo_business_ids', (promo_business_ids), groups=['base.group_system'], context=None)                                                                                      
    
    def get_default_promo_business_ids(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        try:
            promo_business_ids = params.get_param(cr, uid, 'promo_business_ids',default='[]',context=context)
            return dict(promo_business_ids=[(6,0,eval(promo_business_ids))])
        except Exception as e:
            raise osv.except_osv('Error','Please check the value of business promotions. It is invalid!')                    
    
    def set_default_promo_non_business_ids(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        params = self.pool.get('ir.config_parameter')
        promo_non_business_ids = map(lambda x:x.id,myself.promo_non_business_ids)
        params.set_param(cr, uid, 'promo_non_business_ids', (promo_non_business_ids), groups=['base.group_system'], context=None)                                                                                      
    
    def get_default_promo_non_business_ids(self,cr,uid,ids,context=None):
        params = self.pool.get('ir.config_parameter')
        try:
            promo_non_business_ids = params.get_param(cr, uid, 'promo_non_business_ids',default='[]',context=context)
            return dict(promo_non_business_ids=[(6,0,eval(promo_non_business_ids))])
        except Exception as e:
            raise osv.except_osv('Error','Please check the value of Volumes not available for Retailers. It is invalid!')                            

    def set_default_privacy_policy_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('privacy_policy_banner','=',True),('id','!=',myself.privacy_policy_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.privacy_policy_banner.id,{'privacy_policy_banner':True})
    
    def get_default_privacy_policy_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('privacy_policy_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(privacy_policy_banner=s3_object_ids[0])
        else:
            return dict(privacy_policy_banner=False)        
    
    def set_default_terms_conditions_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('terms_conditions_banner','=',True),('id','!=',myself.terms_conditions_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.terms_conditions_banner.id,{'terms_conditions_banner':True})
    
    def get_default_terms_conditions_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('terms_conditions_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(terms_conditions_banner=s3_object_ids[0])
        else:
            return dict(terms_conditions_banner=False)                

    def set_default_search_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('search_banner','=',True),('id','!=',myself.search_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.search_banner.id,{'search_banner':True})
    
    def get_default_search_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('search_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(search_banner=s3_object_ids[0])
        else:
            return dict(search_banner=False)

    def set_default_shipping_returns_policy_banner(self,cr,uid,ids,context=None):
        myself = self.browse(cr,uid,ids[0],context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr,uid,[('shipping_returns_policy_banner','=',True),('id','!=',myself.shipping_returns_policy_banner.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr,uid,i)
        s3_object.write(cr,uid,myself.shipping_returns_policy_banner.id,{'shipping_returns_policy_banner':True})
    
    def get_default_shipping_returns_policy_banner(self,cr,uid,ids,context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr,uid,[('shipping_returns_policy_banner','=',True)],limit=1)
        if s3_object_ids:
            return dict(shipping_returns_policy_banner=s3_object_ids[0])
        else:
            return dict(shipping_returns_policy_banner=False)

    def set_default_contactus_banner_500340(self, cr, uid, ids, context=None):
        myself = self.browse(cr, uid, ids[0], context=context)
        s3_object = self.pool.get('s3.object')
        existing_banner_ids = s3_object.search(cr, uid, [("contactus_banner_500340", '=', True),
                                                         ('id', '!=', myself.contactus_banner_500340.id)])
        if existing_banner_ids:
            for i in existing_banner_ids:
                s3_object.unlink(cr, uid, i)
        s3_object.write(cr, uid, myself.contactus_banner_500340.id, {'contactus_banner_500340': True})

    def get_default_contactus_banner_500340(self, cr, uid, ids, context=None):
        s3_object_ids = self.pool.get('s3.object').search(cr, uid, [('contactus_banner_500340', '=', True)],
                                                          limit=1)
        if s3_object_ids:
            return dict(contactus_banner_500340=s3_object_ids[0])
        else:
            return dict(contactus_banner_500340=False)

    _columns = {
            'site_name':fields.char("Site Name"),
            'aws_access_id' : fields.char("AWS Access ID"),
            'aws_secret_key' : fields.char('AWS Secret Key'),
            'root_bucket':fields.char("Root Bucket"),
#             'website_banner_key' : fields.char("Website Banner Bucket Key"),
#             'website_policy_key' : fields.char("Website Policy Bucket Key"),
#             'volume_key':fields.char("Volumes Bucket Key"),
            'aws_base_url':fields.char("S3 Base URL",help="This is required so that when determining the url we do not have to send extra request to determine the location of the bucket"),
            'meta_keywords':fields.text("Meta Keywords"),
            'meta_description':fields.text('Meta Description'),
            'attribute_value_ids':fields.many2many('product.attribute.value','django_panel_settings_attribute_value',column1='django_panel_settings_id',column2='attribute_value_id',
                                                   string = "Volumes available to Normal Website Visitors",domain=_get_domain_volume,
                                                   ),
            'mailing_list_id':fields.many2one('mail.mass_mailing.list','News Letter Mailing List'),
            'attributes_available_ids':fields.many2many('product.attribute.value','django_panel_settings_attribute_value_available',column1='django_panel_settings_id',column2='attribute_value_id',
                                                   string = "Volumes available to Businesses",domain=_get_domain_volume,
                                                   ),
            'shipping_returns_policy_banner':fields.many2one('s3.object',string="Shipping & Returns Policy Banner"),
            'aboutus_banner':fields.many2one('s3.object',string="About Us Banner"),
            'checkout_banner':fields.many2one('s3.object',string="Checkout Banner"),
            'terms_conditions_banner':fields.many2one('s3.object',string="Terms & Conditions Banner"),
            'privacy_policy_banner':fields.many2one('s3.object',string="Privacy Policy Banner"),
            'search_banner':fields.many2one('s3.object',string = "Search Banner"),
            'contactus_banner':fields.many2one('s3.object',string="Contact Us Banner"),
            'contactus_banner_500340': fields.many2one('s3.object', string="Contact Us Banner (500x340)"),
            'customerreview_banner':fields.many2one('s3.object',string="Customer Review Banner"),
            'promo_business_ids':fields.many2many('website.policy','django_panel_settings_website_policy',column1='django_panel_settings_id',column2='policy_id',
                                                   string = "Business Promotions"),
            'promo_non_business_ids':fields.many2many('website.policy','django_panel_settings_non_business_website_policy',column1='django_panel_settings_id',column2='policy_id',
                                                   string = "Non Business Promotions"),
            'website_url':fields.char('Website URL'),
            'website_username':fields.char('Website Username'),
            'website_pwd': fields.char('Website Password'),
        }