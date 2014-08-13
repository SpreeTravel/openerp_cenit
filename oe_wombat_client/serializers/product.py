# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv.orm import Model


class product_serializer(Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def serialize(self, model_obj, context=None):
        vals = {
            'id': model_obj.name.replace(' ', '-'),
            'name': model_obj.name,
            'sku': model_obj.name.replace(' ', '-'),
            'price': model_obj.list_price,
            'cost_price': model_obj.standard_price,
            'available_on': '2014-01-29T14:01:28.000Z',
            'shipping_category': 'Default'
        }
        return vals
