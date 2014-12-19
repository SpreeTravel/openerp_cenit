# -*- coding: utf-8 -*-

from openerp import models


class CenitHandler(models.TransientModel):
    _name = 'cenit.handler'

    def find(self, cr, uid, match, model_obj, params, context=None):
        fp = [x for x in match.line_ids if x.primary]
        fp = fp and fp[0] or False
        if fp and params.get(fp.value, False):
            to_search = [(fp.name, '=', params[fp.value])]
            obj_ids = model_obj.search(cr, uid, to_search, context=context)
            if obj_ids:
                return obj_ids[0]
        return False

    def find_reference(self, cr, uid, field, params, context=None):
        if field.reference_id:
            model_obj = self.pool.get(field.reference_id.model_id.model)
            to_search = [('name', '=', params[field.value])]
            obj_ids = model_obj.search(cr, uid, to_search, context=context)
            return obj_ids and obj_ids[0] or False
        return False

    def process(self, cr, uid, match, params, context=None):
        vals = {}
        for field in match.line_ids:
            if field.line_type == 'field':
                vals[field.name] = params.get(field.value, False)
            elif field.line_type == 'model':
                if field.line_cardinality == '2many':
                    vals[field.name] = []
                    for x in params.get(field.value, []):
                        item = self.process(cr, uid, field.reference_id, x)
                        vals[field.name].append((0, 0, item))
            elif field.line_type == 'reference':
                vals[field.name] = self.find_reference(cr, uid, field,
                                                       params, context)
            elif field.line_type == 'default':
                vals[field.name] = field.value
        return vals

    def get_match(self, cr, uid, m_name, context=None):
        wdt = self.pool.get('cenit.data.type')
        matching_id = wdt.search(cr, uid, [('name', '=', m_name)], context)
        if matching_id:
            return wdt.browse(cr, uid, matching_id[0], context)
        return False

    def add(self, cr, uid, params, m_name, context=None):
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False
        model_obj = self.pool.get(match.model_id.model)
        if not isinstance(params, list):
            params = [params]
        obj_ids = []
        for p in params:
            obj_id = self.find(cr, uid, match, model_obj, p, context)
            if not obj_id:
                vals = self.process(cr, uid, match, p, context)
                obj_id = model_obj.create(cr, uid, vals, context)
            obj_ids.append(obj_id)
        return obj_ids

    def update(self, cr, uid, params, m_name, context=None):
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False
        model_obj = self.pool.get(match.model_id.model)
        obj_id = self.find(cr, uid, match, model_obj, params, context)
        if obj_id:
            vals = self.process(cr, uid, match, params, context)
            model_obj.write(cr, uid, obj_id, vals, context)
        return obj_id

    def synch(self, cr, uid, params, m_name, context=None):
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False
        vals = self.process(cr, uid, match, params, context)
        model_obj = self.pool.get(match.model_id.model)
        obj_id = self.find(cr, uid, match, model_obj, params, context)
        if obj_id:
            model_obj.write(cr, uid, obj_id, vals, context)
        else:
            obj_id = model_obj.create(cr, uid, vals, context)
        return obj_id
