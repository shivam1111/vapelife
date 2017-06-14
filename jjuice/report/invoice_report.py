from openerp import tools
from openerp.osv import fields,osv

_SOURCE = [
           ('trade_show','Trade Show'),
           ('sales_trip','Sales Trip'),
           ('magazine_add','Magazine Add'),
           ('referral','Referral'),
           ]

class account_treasury_report(osv.osv):
    _inherit = "account.invoice.report"
    _description = "Invoice Report"
    _auto = False
    
    _columns = {
                'account_type':fields.char("Type Of Account",readonly=True),
                'classify_finance':fields.char("Account Classification(For Finance)",readonly=True),
                'volume':fields.char("Volume",readonly=True),
                'source':fields.selection(_SOURCE,string="Basic Acquisition Source",readonly=True),
                'source_name':fields.char("Acquisition Source",readonly=True),
                
                }
    
    def _select(self):
        
        select_str = """
            SELECT sub.id, sub.date, sub.product_id, sub.partner_id, sub.country_id,
                sub.payment_term, sub.period_id, sub.uom_name, sub.currency_id, sub.journal_id,
                sub.fiscal_position, sub.user_id, sub.company_id, sub.nbr, sub.type, sub.state,
                sub.account_type,sub.classify_finance,sub.volume,sub.source_name,sub.source,
                sub.categ_id, sub.date_due, sub.account_id, sub.account_line_id, sub.partner_bank_id,
                sub.product_qty, sub.price_total / cr.rate as price_total, sub.price_average /cr.rate as price_average,
                cr.rate as currency_rate, sub.residual / cr.rate as residual, sub.commercial_partner_id as commercial_partner_id
        """
        return select_str

    def _sub_select(self):
        select_str = """
                SELECT min(ail.id) AS id,
                    ai.date_invoice AS date,
                    ail.product_id, ai.partner_id, ai.payment_term, ai.period_id,
                    u2.name AS uom_name,
                    ai.currency_id, ai.journal_id, ai.fiscal_position, ai.user_id, ai.company_id,
                    count(ail.*) AS nbr,
                    COALESCE (partner.acccount_type, 'No Label') as account_type ,
                    COALESCE (partner.classify_finance, 'No Finance Classification') as classify_finance,
                    pav.name AS volume,
                    aq.name as source_name,
                    aq.source as source,
                    ai.type, ai.state, pt.categ_id, ai.date_due, ai.account_id, ail.account_id AS account_line_id,
                    ai.partner_bank_id,
                    SUM(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN (- ail.quantity) / u.factor * u2.factor
                            ELSE ail.quantity / u.factor * u2.factor
                        END) AS product_qty,
                    SUM(CASE
                         WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                            THEN - ail.price_subtotal
                            ELSE ail.price_subtotal
                        END) AS price_total,
                    CASE
                     WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                        THEN SUM(- ail.price_subtotal)
                        ELSE SUM(ail.price_subtotal)
                    END / CASE
                           WHEN SUM(ail.quantity / u.factor * u2.factor) <> 0::numeric
                               THEN CASE
                                     WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                                        THEN SUM((- ail.quantity) / u.factor * u2.factor)
                                        ELSE SUM(ail.quantity / u.factor * u2.factor)
                                    END
                               ELSE 1::numeric
                          END AS price_average,
                    CASE
                     WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text])
                        THEN - ai.residual
                        ELSE ai.residual
                    END / (SELECT count(*) FROM account_invoice_line l where invoice_id = ai.id) *
                    count(*) AS residual,
                    ai.commercial_partner_id as commercial_partner_id,
                    partner.country_id
        """
        return select_str
    
    def _from(self):
        from_str = """
                FROM account_invoice_line ail
                JOIN account_invoice ai ON ai.id = ail.invoice_id
                JOIN res_partner partner ON ai.commercial_partner_id = partner.id
                LEFT JOIN product_product pr ON pr.id = ail.product_id
                left JOIN product_template pt ON pt.id = pr.product_tmpl_id
                left JOIN product_attribute_value  pav ON pav.id = pr.vol_id
                left join account_acquisition aq on aq.id = partner.acquisition_id
                LEFT JOIN product_uom u ON u.id = ail.uos_id
                LEFT JOIN product_uom u2 ON u2.id = pt.uom_id
        """
        return from_str


    def _group_by(self):
        group_by_str = """
                GROUP BY ail.product_id, ai.date_invoice, ai.id,
                    ai.partner_id, ai.payment_term, ai.period_id, u2.name, u2.id, ai.currency_id, ai.journal_id,
                    ai.fiscal_position, ai.user_id, ai.company_id, ai.type, ai.state, pt.categ_id,
                    ai.date_due, ai.account_id, ail.account_id, ai.partner_bank_id, ai.residual,
                    ai.amount_total, ai.commercial_partner_id, partner.country_id,partner.acccount_type,
                    partner.classify_finance,
                    pav.name,
                    aq.name,
                    aq.source
        """
        return group_by_str    