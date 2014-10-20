# -*- coding: utf-8 -*-
global MATCHING
MATCHING = { 
  'product':{
    'id':'default_code',
    'name': 'name',
    'sku': 'default_code',
    'description': 'description',
    'price': 'list_price',
    'cost_price': 'standard_price',
    # 'available_on':'produce_delay',    
    # 'permalink': '',
    # 'meta_description': '',
    # 'meta_keywords': '',
    # 'shipping_category':'',
    'taxons':'taxons',
    'options':'options',
    'properties':'properties',
    # 'images':'image',
    'variants':'variants',
  },
  'sales.order':{
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
