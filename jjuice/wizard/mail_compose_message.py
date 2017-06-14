from openerp.osv import osv
from openerp.osv import fields

class mail_compose_message(osv.TransientModel):
    _inherit = 'mail.compose.message'
    
    def on_change_update_optional_emails(self,cr,uid,ids,partner_ids,context=None):
        email_multi = ''
        if partner_ids[0][2] and isinstance(partner_ids[0][2],list):
            for j in partner_ids[0][2]:
                cr.execute('''
                    select email from multi_email where partner_id = {0}
                '''.format(j))
                list_mail = cr.fetchall()
                for i in list_mail:
                    email_multi = email_multi + i[0] + ','
        return {
                 'value':{
                           'partner_multi_emails':email_multi
                           }
                 }
    
    _columns = {
                'partner_multi_emails':fields.text('Optional Email To'),
                'update_optional_emails':fields.boolean('Update Optional Emails')
                }
    
    def send_mail(self, cr, uid, ids, context=None):
        for wizard in self.browse(cr, uid, ids, context=context):
            context.update({'email_multi_to':wizard.partner_multi_emails})
        return super(mail_compose_message,self).send_mail(cr, uid, ids, context)        