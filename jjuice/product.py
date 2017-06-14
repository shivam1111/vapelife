from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import SUPERUSER_ID

class product_product(osv.osv):
    _inherit = "product.product"
    
    def write(self,cr,uid,ids,vals,context=None):
        product_tmpl = self.pool.get('product.template')
        res = super(product_product,self).write(cr,uid,ids,vals,context)
        if vals.get('vol_id',False) or vals.get('conc_id',False):
            for  i in self.browse(cr,uid,ids,context):
                name = ''
                if i.flavor_id:
                    name += i.flavor_id.name
                    if i.vol_id:
                        name+= " | %s"%(i.vol_id.name)
                    if i.conc_id:
                        name+= " | %s"%(i.conc_id.name)
                product_tmpl.write(cr,uid,i.product_tmpl_id.id,{'name':name})
        return res

    def _check_shipping(self, cr, uid, ids, context=None):
        cr.execute('''
            select count(*) from product_product where shipping = true
        ''')
        count = cr.fetchall()[0][0]
        if (count > 1):
            return False
        return True
    
    def _check_unqiue_product(self,cr,uid,ids,context=None):
        for product in self.browse(cr,uid,ids,context):
            if product.flavor_id and product.conc_id and product.vol_id and product.product_tmpl_id.type == "product" :
                res = self.search(cr,uid,[('vol_id','=',product.vol_id.id),
                                            ('conc_id','=',product.conc_id.id),
                                            ('product_tmpl_id.type','=',product.product_tmpl_id.type),
                                            ('flavor_id','=',product.flavor_id.id),
                                        ])
                if len(res) > 1:
                    return False
        return True
        
    _constraints = [
        (_check_shipping, 'Error: There can be only one shipping product', ['shipping']),
        (_check_unqiue_product,'Flavor,Concentration,Type of Product,Volume. This combnation should be unique',['flavor_id','vol_id','conc_id','product_tmpl_id.type'])
    ]

#     [{'id': 10, 'name': '10ml'}, {'id': 11, 'name': '350ml'}]
# case_mark,shipping,queryDict,sale_rep,internal_sale,order_note,div_html,payment_lines
    def first_create_sale_order(self,cr,uid,shipping,querryDict,sale_rep,internal_sale,order_note,div_html,payment_lines,context=None):
        uid = SUPERUSER_ID
        payment_plan = self.pool.get('payment.plan')
        paid_line = False
        line = self.pool.get('sale.order.line')
        sale_order = self.pool.get('sale.order').create(cr,uid,{
                                                                'partner_id':int(querryDict.get('active_id',False)),
                                                                'internal_sale':internal_sale,
                                                                'sale_rep':[(6,0,sale_rep)],
                                                                'note':order_note,
                                                                'field_order_html':div_html,
                                                                },context)
        if shipping > 0 :
            cr.execute('''
                select id from product_product where shipping = true limit 1
            ''')
            product_shipping_id = cr.fetchall()
            if product_shipping_id:
                line.create(cr,uid,{
                                'order_id':sale_order,
                                'product_id':product_shipping_id[0][0],
                                'product_uom_qty':1,
                                'price_unit':shipping,
                                'sequence':11,
                                },context)            
        
        for line in payment_lines:
            if not line.get('paid',False):
                line.update({'amount_original':line.get('amount',False),'order_id':sale_order,'partner_id':int(querryDict.get('active_id',False))})
                payment_plan.create(cr,uid,line,context)
            else:
                paid_line = line
        return {'sale_order':sale_order,'paid_line':paid_line}
        
    def check_availability_product(self,cr,uid,line_list,packages,context=None):
#         [
#          {
#          'line_ids': [{'product_id': 61, 'price': 1000, 'qty': 10, 'discount': 11, 'subtotal': 8900, 'id': 1, 'name': 'Marketing'}], 
#             'qty': 1, 'id': 1, 'name': 'Trial'
#          }
#          ]    
# {
#  61:{'id':[1],'qty':10,'individual':False} individual tells whether the product was ordered seperately  in marketing tab or not
#  }    
        package_dict = {}
        #Creating package_dict from packages
        for package in packages:
            for line in package.get('line_ids',False):
                qty = float(line.get('qty',0))
                product_id = line.get('product_id')
                #First check if the product is present in the package dict. If yes then just simply add the qty and marketing package id
                if product_id in package_dict.keys():
                    package_dict[product_id]['id'].append(package.get('id'))
                    package_dict[product_id]['qty'] = package_dict[product_id]['qty'] + qty 
                #If not present already then update the dict with element <product_id>:{'id':[<marketing id>],'qty':<qty>,'individual':<boolean>,
#                                                                                                     'available':<boolean>,
#                                                                                                        'available_qty':<qty>
#                                                                                                        }
                package_dict.update({
                                     line.get('product_id',False):{
                                                                   'id':[package.get('id',False)],
                                                                   'qty':qty,
                                                                   'individual':False,
                                                                   'not_available':False,
                                                                   'product_id':line.get('product_id',False)
                                                                   }
                                     })

        product = self.pool.get('product.product')
        list_fields = ['virtual_available','incoming_qty']
        def read_product_get_available(cr,uid,product_id,fields,qty,context=None):
            info =  product.read(cr,uid,product_id,fields,context)
            virtual_available = info.get('virtual_available',False)
            incoming_qty = info.get('incoming_qty',False)
            available = virtual_available - incoming_qty
            return [available < qty,available]
        
        product_availabilty = {} # This dict will hold the existing required qty of product. As we go down the loop the required qty will be added
            #for the product and checked against available        
        for line in line_list:
            qty = float(line.get('qty',0))
            # For marketing we will first build the dictionary and then check the availability in the end outside the loop
            if (line.get('marketing',False)):
                # First check whether the product is present in package_dict. iF yes then just add the qty to it
                product_id = line.get('id',False)
                if product_id in package_dict.keys():
                    package_dict[product_id]['individual'] = True
                    package_dict[product_id]['qty'] = package_dict[product_id]['qty'] + qty
                #if not then create a new record in the dictionary
                else:
                    package_dict.update({
                                         product_id:{
                                                     'id':[],
                                                     'qty':qty,
                                                     'individual':True,
                                                     'not_available':False,
                                                     'product_id':product_id
                                                     }
                                         })
            # Now checking availability for miscellaneous products
            elif (line.get('misc',False)):
                product_id = line.get('id',False)
                info = read_product_get_available(cr, uid, product_id, list_fields,qty,context)
                line.update({
                             'not_available':info[0],
                             'available_qty':info[1]
                             })
            #Free Samples and JJuice product lines
            else:
                cr.execute('''
                select p.id from product_product as p join product_attribute_value_product_product_rel as l on p.id = l.prod_id join product_template as t on p.product_tmpl_id = t.id where t.product_tmpl_id =  %s and l.att_id= %s
                '''%(int (line.get('class_list',False).get('2',False)) ,int (line.get('class_list',False).get('1',False))) )            
                list_vol = cr.fetchall()
                cr.execute('''
                select p.id from product_product as p join product_attribute_value_product_product_rel as l on p.id = l.prod_id join product_template as t on p.product_tmpl_id = t.id where t.product_tmpl_id =  %s and l.att_id= %s 
                '''%(int(line.get('class_list',False).get('2',False)),int(line.get('class_list',False).get('0',False))))            
                list_conc = cr.fetchall()
                product_id = list(set(list_vol).intersection(list_conc))[0] and list(set(list_vol).intersection(list_conc))[0][0]
                if product_id in product_availabilty:
                    product_availabilty[product_id] = product_availabilty[product_id] + qty
                else:
                    product_availabilty.update({
                                                 product_id:qty
                                                 })
                info = read_product_get_available(cr, uid, product_id, list_fields,qty,context)
                if info[1] < product_availabilty.get(product_id):   # if available qty < total required qty (free samples + product tab)
                    info[0] = True
                line.update({
                             'not_available':info[0],
                             'available_qty':info[1],
                             'product_id':product_id
                             })
        # Now the dictionary for the marketing products is created. we can now check availability
        for id in package_dict.keys():
            record = package_dict[id]
            qty = float(record.get('qty',0))
            info = read_product_get_available(cr, uid, id, list_fields,qty,context)
            record['not_available'] = info[0]
            record['available_qty'] = info[1]
        return [package_dict,line_list]
    
    def create_sale_order(self,cr,uid,line_list,sale_id,paid_line,discount_rate,tax_rate,marketing_packages,context=None):
        # class list is the class list of the td of the input field 
        #0 position is concentration
        #1 position is volume
        #2 position is product.template.custom
        uid =SUPERUSER_ID
        
#         [{'line_ids': [{'product_id': 519, 'price': 40.5, 'qty': 1, 'discount': 10, 'subtotal': 40.5, 'id': 2, 'name': '**JJuice Custom 2-Tier Display Case'}], 
#             'qty': 1, 'id': 1, 'name': 'Trial'}]

        sale_line = self.pool.get('sale.order.line');
        #creating lines for marketing_packages
        
        for package in marketing_packages:
            for line in package.get('line_ids',False):
                sale_line.create(cr,uid,{
                                         'discount':float(line.get('discount',0)) + (100 - float(line.get('discount',0)))*discount_rate/100,
                                         'tax_id':[(6,0,tax_rate)],
                                         'order_id':sale_id,
                                         'product_id':line.get('product_id',0),
                                         'price_unit':float(line.get('price',0)),
                                         'product_uom_qty':line.get('qty',0) * package.get('qty',0),
                                         'sequence':12,
                                         },context={'price_unit_change':True})
        for line in line_list:
            if (line.get('misc',False)):
                    sale_line.create(cr,uid,{
                                             'discount':discount_rate,
                                             'tax_id':[(6,0,tax_rate)],
                                             'order_id':sale_id,
                                             'product_id':line.get('id',0),
                                             'price_unit':float(line.get('price',0)),
                                             'product_uom_qty':line.get('qty',0),
                                             },context={'price_unit_change':True})                
            elif (line.get('marketing',False)):
                    sale_line.create(cr,uid,{
                                             'discount':float(line.get('discount',0)) + (100 - float(line.get('discount',0)))*discount_rate/100,
                                             'tax_id':[(6,0,tax_rate)],
                                             'order_id':sale_id,
                                             'product_id':line.get('id',0),
                                             'price_unit':float(line.get('price',0)),
                                             'product_uom_qty':line.get('qty',0),
                                             'sequence':12,
                                             },context={'price_unit_change':True})                                    
            
            else: #  This case is eligible for free samples and the products having concentration and volume
                cr.execute('''
                select p.id from product_product as p join product_attribute_value_product_product_rel as l on p.id = l.prod_id join product_template as t on p.product_tmpl_id = t.id where t.product_tmpl_id =  %s and l.att_id= %s 
                '''%(int (line.get('class_list',False).get('2',False)) ,int (line.get('class_list',False).get('1',False))) )            
                list_vol = cr.fetchall()
                cr.execute('''
                select p.id from product_product as p join product_attribute_value_product_product_rel as l on p.id = l.prod_id join product_template as t on p.product_tmpl_id = t.id where t.product_tmpl_id =  %s and l.att_id= %s 
                '''%(int(line.get('class_list',False).get('2',False)),int(line.get('class_list',False).get('0',False))))            
                list_conc = cr.fetchall()
                for product_id in list(set(list_vol).intersection(list_conc)):
                    sale_line.create(cr,uid,{
                                             'discount':discount_rate,
                                             'tax_id':[(6,0,tax_rate)],
                                             'order_id':sale_id,
                                             'product_id':product_id[0],
                                             'price_unit':float(line.get('price',0)),
                                             'product_uom_qty':float(line.get('qty',0)),
                                             },context={'price_unit_change':True})
                        
        return True
    
    def get_values_product_vol_tax(self,cr,uid,vol_id,context=None):
        result = {}
        res = []
        list_conc = []
        list_records = []
        misc_records = []
        marketing_records = []
        model_object = self.pool.get('ir.model.data')
        record_id = model_object.get_object_reference(cr,uid,'jjuice','attribute_conc')[1]
        model_object = self.pool.get('ir.model.data')
        vol_attribute_id = model_object.get_object_reference(cr,uid,'jjuice','attribute_vol')[1]        
        sample_records = []
        for vol in vol_id:
            # This fetches all the product.template.custom having the volume vol.get('id',False) where top_fifteen = true
            cr.execute('''
            select distinct a.product_tmpl_id,c.name from product_attribute_line_custom as a  join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id join product_template_custom as c on a.product_tmpl_id = c.id where val_id = %s and c.top_fifteen = true
            ''' %(vol.get('id',False)))
            sample_records = [x for x in cr.fetchall()]
            sample_records = sorted(sample_records, key=lambda record: record[1])
            for tmpl_id in sample_records:
                  # Find the concentration in which the tmpl_id is present in
                cr.execute('''
                  select val_id from product_attribute_line_custom as a join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id where a.attribute_id = %s and a.product_tmpl_id = %s
                  ''' %(record_id,tmpl_id[0]))
                list_records.append({'id':tmpl_id[0],'name':tmpl_id[1],'conc_id':[x[0] for x in cr.fetchall()]})
            # This fetches all the product.template.custom having the volume vol.get('id',False) where top_fifteen = false
            cr.execute('''
            select distinct a.product_tmpl_id,c.name from product_attribute_line_custom as a  join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id join product_template_custom as c on a.product_tmpl_id = c.id where val_id = %s and c.top_fifteen = false
            ''' %(vol.get('id',False)))
            sample_records = [x for x in cr.fetchall()]
            sample_records = sorted(sample_records, key=lambda record: record[1])
            for tmpl_id in sample_records:
                  # Find the concentration in which the tmpl_id is present in
                cr.execute('''
                  select val_id from product_attribute_line_custom as a join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id where a.attribute_id = %s and a.product_tmpl_id = %s
                  ''' %(record_id,tmpl_id[0]))
                list_records.append({'id':tmpl_id[0],'name':tmpl_id[1],'conc_id':[x[0] for x in cr.fetchall()]})
            res.append({
                        'vol_id':vol.get('id',False),
                        'vol_name':vol.get('name',False),
                        'template_list':list_records,
                        })            
            list_records = []
        #Fetching all the miscellaneous products
        cr.execute('''
        select a.id,b.name,b.list_price from product_product as a join product_template as b on a.product_tmpl_id = b.id where a.misc = true 
        ''')
        for records in cr.fetchall():
            misc_records.append({'name':records[1],'id':records[0],'price':records[2]})

        #fetching all the marketing products
        cr.execute('''
        select a.id,b.name,b.list_price from product_product as a join product_template as b on a.product_tmpl_id = b.id where a.market_case = true 
        ''')        
        for records in cr.fetchall():
            marketing_records.append({'name':records[1],'id':records[0],'price':records[2]})
        
        result.update({'normal':res,'misc':misc_records,'marketing':marketing_records})        
        #Fetching the free samples
        cr.execute('''
        select id,attribute_id,name from  product_attribute_value where default_free_samples = true
        ''')
        attribute_free = cr.fetchone()  #(3,1,name)
        if attribute_free:
            if attribute_free[1] != vol_attribute_id:
                raise osv.except_osv(_('Error!'),_('Please Choose only volume attributes for Free Samples'))
        cr.execute('''
        select distinct a.product_tmpl_id,c.name from product_attribute_line_custom as a  
            join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id 
                join product_template_custom as c on a.product_tmpl_id = c.id where val_id = %s 
        ''' %(attribute_free[0]))        
#         [(34, u'Shivam3'), (23, u'Shivam1'), (24, u'Shivam2')]
        sample_records = [x for x in cr.fetchall()]
        sample_records = sorted(sample_records, key=lambda record: record[1])
        for tmpl_id in sample_records:
              # Find the concentration in which the tmpl_id is present in
            cr.execute('''
              select val_id from product_attribute_line_custom as a join product_attribute_line_custom_product_attribute_value_rel as b on a.id = b.line_id where a.attribute_id = %s and a.product_tmpl_id = %s
              ''' %(record_id,tmpl_id[0]))
            list_records.append({'id':tmpl_id[0],'name':tmpl_id[1],'conc_id':[x[0] for x in cr.fetchall()]})
        tax_object = self.pool.get('account.tax')
        taxes = tax_object.search(cr,uid,[('type_tax_use','=','sale'),('type','=','percent')],context)
        tax_detail =  tax_object.read(cr,uid,taxes,['id','name','amount'],context)
        result.update({'extra':list_records,'vol_id':attribute_free[0],'vol_name':attribute_free[2],'taxes':tax_detail})
        return result

    def _get_domain_volume(self,context=None):
        # We have access to self.env in this context.
        ids = self.env.ref('jjuice.attribute_vol').id
        return [('attribute_id','=', ids)]
    
    def _get_domain_concentration(self,context=None):
        # We have access to self.env in this context.
        ids = self.env.ref('jjuice.attribute_conc').id
        return [('attribute_id','=', ids)]    
    
    def name_get(self, cr, uid, ids, context=None):
        result = super(product_product,self).name_get(cr, uid, ids, context=None)
        return result
        
    _sql_constraints = [
                        ('properties_uniq', 'unique(tab_id,vol_id,conc_id,flavor_id)', ("The Concentration,Volume,Flavor and Tab of a  product should be unique!"))
                ]
    
    _columns = {
                'shipping':fields.boolean("Shipping"),
                'tab_id':fields.many2one('product.tab','Tab',ondelete='cascade', select=True),
                'vol_id':fields.many2one('product.attribute.value',string="Volume",domain=_get_domain_volume,readonly=True),
                'conc_id':fields.many2one('product.attribute.value',string="Concentration",domain=_get_domain_concentration,readonly=True),
                'flavor_id':fields.many2one('product.flavors',"Flavor")
                }
