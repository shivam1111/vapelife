from openerp import tools
from openerp.osv import fields,osv

FINANCE_CLASSIFY  = [
                 ('retailer','Retailer'),
                 ('wholesale','Wholesaler / Distributer'),
                 ('private_label','Private Label'),
                 ('website','Vapejjuice.com'),
                 ]

ACCOUNT_TYPE  = [('smoke_shop',"Smoke Shop"),('vape_shop','Vape Shop'),('convenient_gas_store','Convenient Store/ Gas Station'),
                 ('website','Online Store'),
                 ]

_SOURCE = [
           ('trade_show','Trade Show'),
           ('sales_trip','Sales Trip'),
           ('magazine_add','Magazine Add'),
           ('referral','Referral'),
           ]

class account_treasury_report(osv.osv):
    _inherit = "account.treasury.report"
    _description = "Treasury Analysis"
    _auto = False
    
    _columns = {
                'partner_id':fields.many2one('res.partner','Partner',readonly=True),
                'account_type':fields.selection(ACCOUNT_TYPE,string = "Type Of Account",readonly=True),
                'classify_finance':fields.selection(FINANCE_CLASSIFY,string = "Account Classification(For Finance)",readonly=True),
                'source':fields.selection(_SOURCE,string="Basic Acquisition Source",readonly=True),
                'source_name':fields.char("Acquisition Source",readonly=True),                
                }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_treasury_report')
        cr.execute("""
            create or replace view account_treasury_report as (
            select
                p.id as id,
                p.fiscalyear_id as fiscalyear_id,
                p.id as period_id,
                COALESCE (partner.acccount_type, 'No Label') as account_type ,
                COALESCE (partner.classify_finance, 'No Finance Classification') as classify_finance,
                aq.name as source_name,
                aq.source as source,
                l.partner_id as partner_id,
                sum(l.debit) as debit,
                sum(l.credit) as credit,
                sum(l.debit-l.credit) as balance,
                p.date_start as date,
                am.company_id as company_id
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
                left join res_partner partner on (l.partner_id = partner.id)
                left join account_acquisition aq on aq.id = partner.acquisition_id
            where l.state != 'draft'
              and a.type = 'liquidity'
            group by p.id, p.fiscalyear_id, p.date_start, am.company_id,l.partner_id,partner.acccount_type,
            partner.classify_finance,aq.name,
                    aq.source
            )
        """)

    