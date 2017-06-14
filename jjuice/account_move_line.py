from openerp.osv import fields, osv
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _description = "Journal Items JJuice"

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        if context.get('show_payments',False):
            for line in self.browse(cr, uid, ids, context=context):
                result.append((line.id, line.date + "|" + "Dr."+str(line.debit)+"/"+"Cr."+str(line.credit)+"|"+line.journal_id.name  + "\n" ))
            return result            
        else:
            return super(account_move_line,self).name_get(cr,uid,ids,context)

    
    def _get_move_lines(self, cr, uid, ids, context=None):
        result = []
        for move in self.pool.get('account.move').browse(cr, uid, ids, context=context):
            for line in move.line_id:
                result.append(line.id)
        return result
    
    _columns = {
                'date': fields.related('move_id','date', string='Deposit date', type='date', required=True, select=True,
                                store = {
                                    'account.move': (_get_move_lines, ['date'], 20)
                                }),                
                }

    
