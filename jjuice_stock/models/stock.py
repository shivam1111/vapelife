from openerp import models, fields, api,_
import time 
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class stock_inventory(models.Model):
    _inherit = "stock.inventory"
    _description = "Stock Inventory"
    
    @api.multi
    @api.model
    def prepare_inventory(self):
        inventory_line_obj = self.env['stock.inventory.line']
        for inventory in self:
            # If there are inventory lines already (e.g. from import), respect those and set their theoretical qty
            line_ids = [line.id for line in inventory.line_ids]
            if not line_ids and inventory.filter != 'partial':
                #compute the inventory lines and create them
                vals = self._get_inventory_lines(inventory)
                for product_line in vals:
                    inventory_line_obj.create(product_line)
            self.state='confirm'
            self.data = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return True
    
    def _get_inventory_lines(self,inventory):
        location_obj = self.env['stock.location']
        product_obj = self.env['product.product']
        location_ids = location_obj.search([('id', 'child_of', [inventory.location_id.id])])
        location_ids = map(lambda x:x.id,location_ids)
        domain = ' s.location_id in %s'
        args = (tuple(location_ids),)
        if inventory.partner_id:
            domain += ' and owner_id = %s'
            args += (inventory.partner_id.id,)
        if inventory.lot_id:
            domain += ' and lot_id = %s'
            args += (inventory.lot_id.id,)
        if inventory.product_id:
            domain += ' and product_id = %s'
            args += (inventory.product_id.id,)
        if inventory.package_id:
            domain += ' and package_id = %s'
            args += (inventory.package_id.id,)

        if inventory.filter == "stockable": 
            domain += " and pt.type = 'product'"

        if inventory.filter == "stockable_sellable": 
            domain += " and pt.type = 'product' and pt.sale_ok = True"            
        
        self._cr.execute('''
           SELECT product_id, sum(s.qty) as product_qty, s.location_id, s.lot_id as prod_lot_id, s.package_id, s.owner_id as partner_id
           FROM stock_quant as s left join product_product as p on p.id = s.product_id left join product_template as pt on pt.id= p.product_tmpl_id WHERE''' + domain + '''
           GROUP BY product_id, s.location_id, lot_id, package_id, partner_id
        ''', args)
        vals = []
        for product_line in self._cr.dictfetchall():
            #replace the None the dictionary by False, because falsy values are tested later on
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            product_line['inventory_id'] = inventory.id
            product_line['theoretical_qty'] = product_line['product_qty']
            if product_line['product_id']:
                product = product_obj.search([('id','=',product_line['product_id'])],limit=1)
                product_line['product_uom_id'] = product[0].uom_id.id
            vals.append(product_line)
        return vals    
    
    @api.model
    def _get_available_filters(self):
        """
           This function will return the list of filter allowed according to the options checked
           in 'Settings\Warehouse'.

           :rtype: list of tuple
        """
        #default available choices
        res_filter = [
            ('none', _('All products')), 
            ('partial', _('Manual Selection of Products')), 
            ('product', _('One product only')),
            ('stockable',_('Only Stockable')),
            ('stockable_sellable',_('Only Stockable and Sellable')),
        ]
        
        settings_obj = self.env['stock.config.settings']
        config_ids = settings_obj.search([], limit=1, order='id DESC')
        #If we don't have updated config until now, all fields are by default false and so should be not dipslayed
        if not config_ids:
            return res_filter

        stock_settings = settings_obj.search(cr, uid, config_ids[0])
        if stock_settings.group_stock_tracking_owner:
            res_filter.append(('owner', _('One owner only')))
            res_filter.append(('product_owner', _('One product for a specific owner')))
        if stock_settings.group_stock_production_lot:
            res_filter.append(('lot', _('One Lot/Serial Number')))
        if stock_settings.group_stock_tracking_lot:
            res_filter.append(('pack', _('A Pack')))
        return res_filter    
    
    filter =  fields.Selection(_get_available_filters, 'Inventory of', required=True,default="stockable_sellable",
                                   help="If you do an entire inventory, you can choose 'All Products' and it will prefill the inventory with the current stock.  If you only do some products  "\
                                      "(e.g. Cycle Counting) you can choose 'Manual Selection of Products' and the system won't propose anything.  You can also let the "\
                                      "system propose for a single product / lot /... ")
    