{
    'name': 'Vapelife Point of Sale',
    'version': '0.1',
    'author': 'J & G Infosystems',
    'category': 'Hidden',
    'description': """
OpenERP Point of sale Customization
==========================

        """,
    'version': '2.0',
    'depends':['point_of_sale'],
    'data' : [
        'resources.xml',
        'product.xml',
        'product_attribute_value.xml',
        'point_of_sale_view.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'auto_install': False,
}