# -*- coding: utf-8 -*-
global MATCHING
MATCHING = { 
  'product':{
    'id':('product_id',),
    'name': ('name',),
    'sku': ('default_code',),
    'description': ('description',),
    'price': ('list_price',),
    'cost_price': ('standard_price',),
    # 'available_on':'produce_delay',    
    # 'permalink': '',
    # 'meta_description': '',
    # 'meta_keywords': '',
    # 'shipping_category':'',
    'taxons':('taxons','eval'),
    'options':('options','eval'),
    'properties':('properties','eval'),
    # 'images':'image',
    'variants':('variants','eval'),
  },
  'order':{
    'id': 'name',
    'status': 'state',
    # 'channel': '',
    # 'email': '',user.email
    'currency': 'currency_id',
    'placed_on': 'date_confirm',
    # 'totals': '',
    # 'line_items': '',
    # 'adjustments': '',
    # 'shipping_address': '',
    # 'billing_address': '',
    # 'payments': '',
  },
}
