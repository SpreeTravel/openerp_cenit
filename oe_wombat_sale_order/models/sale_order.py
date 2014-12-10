# -*- coding: utf-8 -*-

from openerp import models
from openerp.osv import fields


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def _set_totals(self, cr, uid, oid, name, value, args, context=None):
        return True

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        return dict.fromkeys(ids, '')

    _columns = {
        'totals': fields.function(_get_totals, method=True, type='char',
                                  fnct_inv=_set_totals),
    }
