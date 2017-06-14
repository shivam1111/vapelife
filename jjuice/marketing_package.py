from openerp import models, fields, api,_
import openerp.addons.decimal_precision as dp

class marketing_package(models.Model):
    _name = "marketing.package"
    _description= "Marketing packages"
    
    def call_from_javascript(self,cr,uid,ids,context=None):
        return True
     
    
    @api.multi
    def get_marketing_package(self):
        res = []
        for package in self:
            line_ids = []
            res.append({
                            'name':package.name,
                            'id':package.id,
                            'total':package.amount_total,
                            'line_ids':map(lambda x:{'id':x.id,
                                                     'price':x.price,
                                                     'qty':x.qty,
                                                     'discount':x.discount,
                                                     'product_id':x.product_id.id,
                                                     'name':x.product_id.name,
                                                     'subtotal':x.price_subtotal,
                                                     },package.line_ids)
                            })
        return res
    
    @api.one
    @api.depends('line_ids.price_subtotal', 'line_ids')
    def _compute_amount(self):
        total = 0.00
        for i in self.line_ids:
            total = total + i.price_subtotal
        self.amount_total = total
            
    name = fields.Char('Name',required=True)
    active=fields.Boolean('Active',default=True)
    line_ids = fields.One2many('marketing.package.line','package_id','Product Lines')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_amount', track_visibility='always')
        
class marketing_package_line(models.Model):
    _name = "marketing.package.line"
    _description = "Marketing Package Line"
    
    
    @api.one
    @api.depends('price', 'qty', 'discount',
        'product_id')
    def _compute_price(self):
        price = self.price * (1 - (self.discount or 0.0) / 100.0)
        total = (float(self.qty*price))
        self.price_subtotal = total
    
    package_id = fields.Many2one('marketing.package','Marketing Package')
    product_id = fields.Many2one('product.product','Product')
    price = fields.Float('Price')
    qty = fields.Float('Quantity')
    discount = fields.Float('Discount %')
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readonly=True, compute='_compute_price') 