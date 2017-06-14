from openerp import tools
from openerp.osv import fields, osv

class sale_report(osv.osv):
    _inherit = "sale.report"
    _description = "Sales Orders Statistics"
    _auto = False
    _columns = {
                'conc':fields.many2one("product.attribute.value",string = "Concentration",readonly=True),                        
                'vol':fields.many2one("product.attribute.value",string = "Volume",readonly=True),
                'account_type':fields.char("Type Of Account",readonly=True),
                'classify_finance':fields.char("Account Classification(For Finance)",readonly=True)
                }

    def _select(self,cr):
        cr.execute('''
            select res_id from ir_model_data where name = 'attribute_conc'
        ''')
        conc = cr.fetchone()
        conc_id = conc and conc[0] or False
        cr.execute('''
            select res_id from ir_model_data where name = 'attribute_vol'
        ''')
        vol = cr.fetchone()
        vol_id = vol and vol[0] or False
        if vol_id and conc_id:
            select_str = """
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                    SELECT r.currency_id, r.rate, r.name AS date_start,
                        (SELECT name FROM res_currency_rate r2
                        WHERE r2.name > r.name AND
                            r2.currency_id = r.currency_id
                         ORDER BY r2.name ASC
                         LIMIT 1) AS date_end
                    FROM res_currency_rate r
                )            
                 SELECT min(l.id) as id,
                        l.product_id as product_id,
                        t.uom_id as product_uom,
                        sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                        sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                        count(*) as nbr,
                        (select a.id from product_product 
                            left join product_attribute_value_product_product_rel as rel on product_product.id = rel.prod_id
                            left join product_attribute_value as a on rel.att_id = a.id where product_product.id = l.product_id and a.attribute_id = %s) as conc,
                        (select a.id from product_product 
                            left join product_attribute_value_product_product_rel as rel on product_product.id = rel.prod_id
                            left join product_attribute_value as a on rel.att_id = a.id where product_product.id = l.product_id and a.attribute_id = %s) as vol,                        
                        s.date_order as date,
                        s.date_confirm as date_confirm,
                        s.partner_id as partner_id,
                        COALESCE (partner.acccount_type, 'No Label') as account_type ,
                        COALESCE (partner.classify_finance, 'No Finance Classification') as classify_finance,
                        s.user_id as user_id,
                        s.company_id as company_id,
                        extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                        s.state,
                        t.categ_id as categ_id,
                        s.pricelist_id as pricelist_id,
                        s.project_id as analytic_account_id,
                        s.section_id as section_id
            """ %(conc_id,vol_id)
        else:
           select_str = """
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                    SELECT r.currency_id, r.rate, r.name AS date_start,
                        (SELECT name FROM res_currency_rate r2
                        WHERE r2.name > r.name AND
                            r2.currency_id = r.currency_id
                         ORDER BY r2.name ASC
                         LIMIT 1) AS date_end
                    FROM res_currency_rate r
                )                 
                 SELECT min(l.id) as id,
                        l.product_id as product_id,
                        t.uom_id as product_uom,
                        sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
                        sum(l.product_uom_qty * l.price_unit * (100.0-l.discount) / 100.0) as price_total,
                        count(*) as nbr,
                        (select a.id from product_product 
                            left join product_attribute_value_product_product_rel as rel on product_product.id = rel.prod_id
                            left join product_attribute_value as a on rel.att_id = a.id where product_product.id = l.product_id and a.attribute_id = 3) as conc,
                        s.date_order as date,
                        s.date_confirm as date_confirm,
                        s.partner_id as partner_id,
                        COALESCE (partner.acccount_type, 'No Label') as account_type ,
                        COALESCE (partner.classify_finance, 'No Finance Classification') as classify_finance,
                        s.user_id as user_id,
                        s.company_id as company_id,
                        extract(epoch from avg(date_trunc('day',s.date_confirm)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
                        s.state,
                        t.categ_id as categ_id,
                        s.pricelist_id as pricelist_id,
                        s.project_id as analytic_account_id,
                        s.section_id as section_id
            """        
        return select_str   
    
    def _from(self):
        from_str = """
                sale_order_line l
                      join sale_order s on (l.order_id=s.id)
                        left join product_product p on (l.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
                                left join res_partner as partner on (s.partner_id = partner.id)
                    left join product_uom u on (u.id=l.product_uom)
                    left join product_uom u2 on (u2.id=t.uom_id)
                    left join product_pricelist pp on (s.pricelist_id = pp.id)
                    join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.date_start <= coalesce(s.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(s.date_order, now())))
        """
        return from_str
     

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    l.order_id,
                    t.uom_id,
                    t.categ_id,
                    s.date_order,
                    s.date_confirm,
                    s.partner_id,
                    s.user_id,
                    s.company_id,
                    l.state,
                    s.pricelist_id,
                    s.project_id,
                    s.section_id,
                    s.state,
                    partner.acccount_type,
                    partner.classify_finance
        """
        return group_by_str
    
    def init(self, cr):
        # self._table = sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(cr), self._from(), self._group_by()))
    
