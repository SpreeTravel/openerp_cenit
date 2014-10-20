# -*- coding: utf-8 -*-
'''
Created on 15/10/2014

@author: José Andrés Hernández Bustio
'''

from openerp.osv import fields
from openerp.osv.orm import Model

from matching.matching import MATCHING

class product(Model):
    _name = 'product.template'
    _inherit = 'product.template'

    def serialize(self, product, context=None):     
        vals = {k: getattr(product, v) for k, v in MATCHING.get('product').items()}
        vals.update({'available_on': '2014-01-29T14:01:28.000Z','shipping_category': 'Default'})
        return vals
   
    def _set_product_id(self, cr, uid, id, name, value, args, context=None):
        return;
        
    def _get_product_id(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            id = obj.name.replace(' ', '-')
            if obj.default_code:
                id = obj.default_code
            result[obj.id] = id
        return result
    
    def _set_taxons(self, cr, uid, id, name, value, args, context=None):
        if not value:
            return False
        pc = self.pool.get('product.category')
        current_tx = False
        for tx in value[0]:
            categ_id = pc.search(cr, uid, [('name', '=', tx)], context=context)
            if categ_id:
                current_tx = categ_id[0]
            else:
                vals = {'name': tx, 'parent_id': current_tx}
                current_tx = pc.create(cr, uid, vals, context)
        product = self.browse(cr, uid, id, context=context)
        product.categ_id = current_tx
    
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

    # TODO: find how to set prices in variants
    def _set_variants(self, cr, uid, id, name, value, args, context=None):
        res = []
        for var in variants:
            vals = {
                'default_code': var['sku'],
                'variants': ' - '.join([k + ':' + v for k, v in var['options'].items()])
            }
            res.append((0, 0, vals))
        return res
    
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
                # var['images']= 
                variants.append(var)
            result[obj.id] = variants
        return result
    
    def _set_options(self, cr, uid, id, name, value, args, context=None):
        return;
        
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
    
    def _set_properties(self, cr, uid, id, name, value, args, context=None):
        return;
        
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
        'taxons': fields.function(_get_taxons, method=True, type='char', fnct_inv=_set_taxons),
        'variants': fields.function(_get_variants, method=True, type='char', fnct_inv=_set_taxons),
        'options': fields.function(_get_options, method=True, type='char', fnct_inv=_set_options),
        'properties': fields.function(_get_properties, method=True, type='char', fnct_inv=_set_properties),
        'product_id': fields.function(_get_product_id, method=True, type='char', fnct_inv=_set_product_id),
    }
