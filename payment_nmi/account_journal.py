from openerp import models, fields, api, _

class account_journal(models.Model):
    _inherit = "account.journal"
    
    def _check_single_nmi_journal(self, cr, uid, ids, context=None):
        a = self.search(cr,uid,[('is_nmi_journal','=',True)],context)
        if len(a) > 1:
            return False
        return True
    
    _constraints = [
        (_check_single_nmi_journal, 'Error: There can only be a single NMI Journal', ['is_nmi_journal']),
        ]   
    
    is_nmi_journal = fields.Boolean("NMI Payment Journal")