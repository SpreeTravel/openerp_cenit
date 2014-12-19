# -*- coding: utf-8 -*-
import itertools

from openerp import models
from openerp.osv import fields


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def _match_variant(self, cr, uid, value_ids, params, context=None):
        for p in params:
            if p.get('options', False) and (set(value_ids)).issubset(set(p['options'].values())):
                return p['options']
        return False

    def _get_attribute(self, cr, uid, name, context=None):
        pa = self.pool.get('product.attribute')
        attr = pa.search(cr, uid, [('name', '=', name)], context=context)
        if attr:
            attr_id = attr[0]
        else:
            attr_id = pa.create(cr, uid, {'name': name})
        return attr_id

    def _get_attribute_value(self, cr, uid, name, attr_id, context=None):
        pav = self.pool.get('product.attribute.value')
        to_search = [('name', '=', name), ('attribute_id', '=', attr_id)]
        attr_value = pav.search(cr, uid, to_search, context=context)
        if attr_value:
            attr_value_id = attr_value[0]
        else:
            to_create = {x[0]: x[2] for x in to_search}
            attr_value_id = pav.create(cr, uid, to_create)
        return attr_value_id

    def _set_taxons(self, cr, uid, oid, name, value, args, context=None):
        if not value:
            return False
        pc = self.pool.get('product.category')
        current_tx = False
        taxons = isinstance(value[0], list) and value[0] or value
        for tx in taxons:
            categ_id = pc.search(cr, uid, [('name', '=', tx)], context=context)
            if categ_id:
                current_tx = categ_id[0]
            else:
                vals = {'name': tx, 'parent_id': current_tx}
                current_tx = pc.create(cr, uid, vals, context)
        self.write(cr, uid, oid, {'categ_id': current_tx}, context=context)

    def _get_taxons(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            current = obj.categ_id
            taxons = [current.name]
            while (current.parent_id):
                taxons.append(current.parent_id.name)
                current = current.parent_id
            taxons.reverse()
            result[obj.id] = taxons
        return result

    def _set_properties(self, cr, uid, oid, name, value, args, context=None):
        context = context or {}
        pa = self.pool.get('product.attribute')
        pav = self.pool.get('product.attribute.value')
        attribute_lines = []
        for a, v in value.items():
            if not v:
                continue
            attr = pa.search(cr, uid, [('name', '=', a)], context=context)
            if attr:
                attr_id = attr[0]
            else:
                attr_id = pa.create(cr, uid, {'name': a})
            to_search = [('name', '=', v), ('attribute_id', '=', attr_id)]
            attr_value = pav.search(cr, uid, to_search, context=context)
            if attr_value:
                attr_value_id = attr_value[0]
            else:
                to_create = {x[0]: x[2] for x in to_search}
                attr_value_id = pav.create(cr, uid, to_create)
            attribute_lines.append((0, 0, {
                                        'attribute_id': attr_id,
                                        'value_ids': [(6, 0, [attr_value_id])]
                                    }))
        if attribute_lines:
            self.write(cr, uid, oid, {'attribute_line_ids': attribute_lines})

    def _get_properties(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            pp = {}
            for at_line in obj.attribute_line_ids:
                if len(at_line.value_ids) <= 1:
                    at = at_line.attribute_id
                    pp[at.name] = at_line.value_ids.name
            result[obj.id] = pp
        return result

    def _set_options(self, cr, uid, oid, name, value, args, context=None):
        pa = self.pool.get('product.attribute')
        attribute_ids = []
        for var in value:
            attr = pa.search(cr, uid, [('name', '=', var)], context=context)
            if attr:
                attr_id = attr[0]
            else:
                attr_id = pa.create(cr, uid, {'name': var})
            attribute_ids.append(attr_id)
        attribute_lines = []
        for attr in attribute_ids:
            attribute_lines.append((0, 0, {'attribute_id': attr}))
        if attribute_lines:
            self.write(cr, uid, oid, {'attribute_line_ids': attribute_lines})

    def _get_options(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            attributes = []
            for at_line in obj.attribute_line_ids:
                if len(at_line.value_ids) > 1:
                    at = at_line.attribute_id
                    attributes.append(at.name)
            result[obj.id] = attributes
        return result

    def _set_variants(self, cr, uid, oid, name, value, args, context=None):
        context = context or {}
        obj = self.browse(cr, uid, oid)
        options = {x.attribute_id.name: x for x in obj.attribute_line_ids}

        attr_values = {}
        for var in value:
            for a, v in var['options'].items():
                attr = options.get(a, False)
                if attr:
                    v = str(v)
                    if attr not in attr_values:
                        attr_values[attr] = []
                    attr_value_id = self._get_attribute_value(cr, uid, v, attr.attribute_id.id, context)
                    if attr_value_id not in attr_values[attr]:
                        attr_values[attr].append(attr_value_id)
        attribute_lines = []
        for k, v in attr_values.items():
            attribute_lines.append((1, k.id, {'value_ids': [(6, 0, v)]}))
        if attribute_lines:
            self.write(cr, uid, oid, {'attribute_line_ids': attribute_lines})

        for variant in obj.product_variant_ids:
            value_names = [x.name for x in variant.attribute_value_ids]
            var = self._match_variant(cr, uid, value_names, value, context)
            if var:
                attr_value_ids = []
                for a, v in var.items():
                    v = str(v)
                    if v not in value_names:
                        attr_id = self._get_attribute(cr, uid, a, context)
                        attr_value_id = self._get_attribute_value(cr, uid, v, attr_id, context)
                        attr_value_ids.append(attr_value_id)
                # TODO: update variants
        return True

    def _get_variants(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            variants = []
            for variant in obj.product_variant_ids:
                var = {}
                var['sku'] = variant.default_code
                var['price'] = variant.lst_price
                var['cost_price'] = variant.price
                var['quantity'] = variant.qty_available
                options = {}
                for at_value in variant.attribute_value_ids:
                    at = at_value.attribute_id
                    value = at_value.name
                    options[at.name] = value
                var['options'] = options
                variants.append(var)
            result[obj.id] = variants
        return result

    _columns = {
        'taxons': fields.function(_get_taxons, method=True, type='char',
                                  fnct_inv=_set_taxons, priority=1),
        'properties': fields.function(_get_properties, method=True,
                                      type='char', fnct_inv=_set_properties,
                                      priority=2),
        'options': fields.function(_get_options, method=True, type='char',
                                   fnct_inv=_set_options, priority=3),
        'variants': fields.function(_get_variants, method=True, type='char',
                                    fnct_inv=_set_variants, priority=4)
    }
