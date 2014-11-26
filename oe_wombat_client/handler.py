# -*- coding: utf-8 -*-

from openerp import models


class WombatHandler(models.TransientModel):
    _name = 'wombat.handler'

    def find(self, cr, uid, match, model_obj, params, context=None):
        fp = [x for x in match.line_ids if x.primary]
        if fp:
            fp = fp[0]
            to_search = [(fp.name, '=', params[fp.value])]
            obj_ids = model_obj.search(cr, uid, to_search, context=context)
            if obj_ids:
                return obj_ids[0]
        return False

    def find_reference(self, cr, uid, field, params, context):
        if field.reference_id:
            model_obj = self.pool.get(field.reference_id.model_id.name)
            fparams = {field.value: params[field.value]}
            match = field.reference_id
            obj_id = self.find(cr, uid, match, model_obj, fparams, context)
            return obj_id
        return False

    def add(self, cr, uid, params, m_name, context=None):
        res = False
        wdt = self.pool.get('wombat.data.type')
        matching_id = wdt.search(cr, uid, [('name', '=', m_name)],
                                     context=context)
        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            model_obj = self.pool.get(match.model_id.model)
            obj_id = self.find(cr, uid, match, model_obj, params, context)
            if not obj_id:
                vals = {}
                for field in match.line_ids:
                    if field.line_type == 'field':
                        vals[field.name] = params.get(field.value, False)
                    elif field.line_type == 'reference':
                        vals[field.name] = self.find_reference(cr, uid, field,
                                                               params, context)
                    elif field.line_type == 'default':
                        vals[field.name] = field.value
                res = model_obj.create(cr, uid, vals, context)
        return res

    def update(self, cr, uid, params, m_name, context=None):
        res = False
        wdt = self.pool.get('wombat.data.type')
        matching_id = wdt.search(cr, uid, [('name', '=', m_name)],
                                     context=context)
        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            model_obj = self.pool.get(match.model_id.model)
            obj_id = self.find(cr, uid, model_obj, params, context)
            if obj_id:
                vals = {}
                for field in match.line_ids:
                    if field.line_type == 'field':
                        vals[field.name] = params.get(field.value, False)
                    elif field.line_type == 'reference':
                        vals[field.name] = self.find_reference(cr, uid, field,
                                                               params, context)
                    elif field.line_type == 'default':
                        vals[field.name] = field.value
                res = model_obj.write(cr, uid, obj_id, vals, context)
        return res
