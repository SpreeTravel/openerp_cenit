# -*- coding: utf-8 -*-

from openerp.osv.orm import TransientModel


class product_handler(TransientModel):
    _name = 'product.handler'
    _related_model = 'product.product'

    def add(self, cr, uid, params, context=None):
        product = self.pool.get(self._related_model)
        vals = {
            'name': params['name'],
            'default_code': params['sku'],
            'list_price': params['price'],
            'description': params['description']
        }
        return product.create(cr, uid, vals, context)

    def update(self, cr, uid, params, context=None):
        res = False
        if params.get('sku', False):
            product = self.pool.get(self._related_model)
            p_ids = product.search(cr, uid,
                                   [('default_code', '=', params['sku'])],
                                   context=context)
            if p_ids:
                vals = {
                    'name': params['name'],
                    'list_price': params['price'],
                    'description': params['description']
                }
                res = product.write(cr, uid, p_ids, vals, context)
        return res
