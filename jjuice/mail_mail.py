from openerp.osv import osv, orm, fields

class mail_mail(osv.Model):
    _inherit = 'mail.mail'
    
    def create(self, cr, uid, values, context=None):
	# This method is overriden so that if we want to send mail to all the email ids related to the contact we will send it in 'email_multi_to' in context
        if context.get('email_multi_to',False):
            if 'email_to' in values:
                values['email_to'] = values['email_to']+context.get('email_multi_to','')
            else:
                values.update({
                               'email_to':context.get('email_multi_to','')
                               })
        return super(mail_mail,self).create(cr,uid,values,context=context)
