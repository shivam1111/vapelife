import math
import re
import time
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import osv, fields, expression
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import psycopg2
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round, float_compare


class product_template(osv.osv):
    _inherit = "product.template"


    def _check_product_template_custom(self,cr,uid,ids,context=None):
        for product in self.browse(cr,uid,ids,context):
            if product.product_tmpl_id:
                return False
        return True
    
    def _get_default_sale_ok(self,cr,uid,context=None):
        if context.get('search_default_filter_to_sell',False):
            return True
        else: return False
    
    _defaults = {
                 'sale_ok':_get_default_sale_ok
                 }
    _columns = {
                'attribute_value_ids_custom': fields.many2many('product.attribute.value', id1='prod_id', id2='att_id', string='Attributes', readonly=True, ondelete='restrict'),
                } 
 
    
