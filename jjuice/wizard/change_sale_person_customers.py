from openerp.osv import fields, osv

class assign_sales_person(osv.osv_memory):
    _name = "assign.sales.person"
    _description = "assign sales person for customers"
    
    def select_sales_person(self,cr,uid,ids,context=None):
         active_ids=context.get('active_ids')
         usr_id = self.read(cr,uid,ids,['user_id'],context)
         user_id=usr_id[0].get('user_id')
         obj=self.pool.get('res.partner')
         obj.write(cr,uid,active_ids,{
                               "user_id":user_id[0]}
                               ,context)
        
         return True
       
    _columns={
              'user_id':fields.many2one('res.users',"Select Sales Person")
              }