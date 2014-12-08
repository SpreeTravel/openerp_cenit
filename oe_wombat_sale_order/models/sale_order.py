# -*- coding: utf-8 -*-

from openerp import models, fields


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
