# -*- coding: utf-8 -*-

from openerp.osv.orm import TransientModel


class product_handler(TransientModel):
    _name = 'product.handler'

    def process(self, cr, uid, action, params, context=None):
        return getattr(self, action)(cr, uid, params, context)

    def add(self, cr, uid, params, context=None):
        pass
