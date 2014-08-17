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

TAXON_FIELDS = ['categ_id', 'public_categ_id']


class product_serializer(Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def serialize(self, product, context=None):
        vals = {
            'id': self._get_id(product),
            'name': product.name,
            'sku': product.default_code,
            'price': product.list_price,
            'cost_price': product.standard_price,
            'available_on': '2014-01-01T14:01:28.000Z',
            'shipping_category': 'Default',
            'taxons': self._get_categories(product),
            'variants': self._get_variants(product)
        }
        return vals

    def _get_id(self, product):
        if product.default_code:
            return product.default_code
        return product.name.replace(' ', '-')

    def _get_categories(self, product):
        taxons = []
        for field in TAXON_FIELDS:
            current = getattr(product, field)
            taxon_parents = [current.name]
            while (current.parent_id):
                taxon_parents.append(current.parent_id.name)
                current = current.parent_id
            taxon_parents.reverse()
            taxons.append(taxon_parents)
        return taxons

    def _get_variants(self, product):
        variants = []
        for variant in product.product_variant_ids:
            var = {}
            var['sku'] = variant.code
            var['price'] = variant.lst_price
            var['cost_price'] = variant.price
            var['quantity'] = variant.qty_available
            variants.append(var)
        return variants
