from openerp import models, fields, api, _

class display_product_availability(models.TransientModel):
    _name = "dispaly.product.availability"
    _description = "Displays non available products"
    
    def prepare_wizard(self,cr,uid,info,context=None):
        vals = {'line_ids':[]}
        for i in info.keys():
            available_qty = info[i]['available_qty']
            required_qty = info[i]['required_qty']
            vals['line_ids'].append((
                                     0,0,{'product_id':int(i),'available_qty':available_qty,'required_qty':required_qty}
                                     ))
        md = self.pool.get('ir.model.data')
        view_id = md.get_object_reference(cr, uid, 'jjuice', 'display_product_availability_form')[1]
        wizard_id = self.create(cr,uid,vals,context) 
        return  [view_id,wizard_id]
        
    line_ids = fields.One2many('dislay.prouct.availability.line','display_product_availability_id','Product lines')
    
class display_product_availability_line(models.TransientModel):
    _name = "dislay.prouct.availability.line"
    _description = "Line"
    
    display_product_availability_id = fields.Many2one('dispaly.product.availability')
    product_id = fields.Many2one('product.product','Product')
    available_qty  = fields.Float('Available Qty')
    required_qty = fields.Float('Required Qty')   
    