# -*- coding: utf-8 -*-

from openerp import models
from openerp.osv import fields


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'

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

    def _set_variants(self, cr, uid, oid, name, value, args, context=None):
        context = context or {}
        pa = self.pool.get('product.attribute')
        pav = self.pool.get('product.attribute.value')
        attr_values = {}
        for var in value:
            for a, v in var['options'].items():
                attr = pa.search(cr, uid, [('name', '=', a)], context=context)
                if attr:
                    attr_id = attr[0]
                else:
                    attr_id = pa.create(cr, uid, {'name': a})
                if attr_id not in attr_values:
                    attr_values[attr_id] = []
                to_search = [('name', '=', v), ('attribute_id', '=', attr_id)]
                attr_value = pav.search(cr, uid, to_search, context=context)
                if attr_value:
                    attr_value_id = attr_value[0]
                else:
                    to_create = {x[0]: x[2] for x in to_search}
                    attr_value_id = pav.create(cr, uid, to_create)
                if attr_value_id not in attr_values[attr_id]:
                    attr_values[attr_id].append(attr_value_id)
        attribute_lines = []
        for k, v in attr_values.items():
            vals = {
                'attribute_id': k,
                'value_ids': [(6, 0, v)]
            }
            attribute_lines.append((0, 0, vals))
        if attribute_lines:
            self.write(cr, uid, oid, {'attribute_line_ids': attribute_lines})

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

    def _set_options(self, cr, uid, oid, name, value, args, context=None):
        pass

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

    _columns = {
        'taxons': fields.function(_get_taxons, method=True, type='char',
                                  fnct_inv=_set_taxons),
        'variants': fields.function(_get_variants, method=True, type='char',
                                    fnct_inv=_set_variants),
        'options': fields.function(_get_options, method=True, type='char',
                                   fnct_inv=_set_options),
        'properties': fields.function(_get_properties, method=True,
                                      type='char', fnct_inv=_set_properties)
    }
