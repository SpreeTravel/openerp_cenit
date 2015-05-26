# -*- coding: utf-8 -*-

import logging

from openerp import models


_logger = logging.getLogger(__name__)


class CenitHandler(models.TransientModel):
    _name = 'cenit.handler'

    def find(self, cr, uid, match, model_obj, params, context=None):
        fp = [x for x in match.lines if x.primary]
        fp = fp and fp[0] or False
        if fp and params.get(fp.value, False):
            to_search = [(fp.name, '=', params[fp.value])]
            obj_ids = model_obj.search(cr, uid, to_search, context=context)
            if obj_ids:
                return obj_ids[0]
        return False

    #~ def find_reference(self, cr, uid, field, params, context=None):
        #~ if field.reference:
            #~ model_obj = self.pool.get(field.reference.model.model)
            #~ to_search = [('name', '=', params.get(field.value, False))]
            #~ obj_ids = model_obj.search(cr, uid, to_search, context=context)
            #~ return obj_ids and obj_ids[0] or False
        #~ return False

    def find_reference(self, cr, uid, match, field, params, context=None):
        _logger.info ("\n\nFinding reference on %s with %s\n", field, match)

        f = [x for x in match.model.field_id if x.name == field.name][0]
        model_pool = self.pool.get ("ir.model")
        model_id = model_pool.search (cr, uid, [('model', '=', f.relation)], context=context)[0]
        model_obj = model_pool.browse (cr, uid, model_id, context=context)
        model_obj = self.pool.get (model_obj.model)
        _logger.info ("\n\nModel: %s\n", model_obj)

        op = "="
        value = params.get(field.value, False)
        if (field.line_cardinality == "2many") and value:
            op = "in"
        to_search = [('name', op, value)]
        _logger.info ("\n\nDomain: %s\n", to_search)

        obj_ids = model_obj.search(cr, uid, to_search, context=context)
        _logger.info ("\n\nCandidates: %s\n", obj_ids)

        rc = obj_ids and obj_ids[0] or False
        if field.line_cardinality == "2many":
            rc = obj_ids or False

        return rc

    def process(self, cr, uid, match, params, context=None):
        vals = {}

        for field in match.lines:
            if field.line_type == 'field':
                if params.get(field.value, False):
                    vals[field.name] = params[field.value]
            elif field.line_type == 'model':
                if field.line_cardinality == '2many':
                    vals[field.name] = []
                    for x in params.get(field.value, []):
                        item = self.process(cr, uid, field.reference, x)
                        vals[field.name].append((0, 0, item))
                elif field.line_cardinality == '2one':
                    x = params.get(field.value, {})
                    rel_ids = self.add(cr, uid, x, field.reference.name)
                    vals[field.name] = rel_ids and rel_ids[0] or False
            elif field.line_type == 'reference':
                vals[field.name] = self.find_reference(cr, uid, match, field,
                                                       params, context)
                                                       #~ params, context)
            elif field.line_type == 'default':
                vals[field.name] = field.value
        _logger.info ("\n\nProcessed values: %s\n", vals)
        return vals

    def get_match(self, cr, uid, root, context=None):
        wdt = self.pool.get('cenit.data_type')
        matching_ids = wdt.search(cr, uid, [('cenit_root', '=', root)])

        if matching_ids:
            return wdt.browse(cr, uid, matching_ids[0], context)
        return False

    def add(self, cr, uid, params, m_name, context=None):
        context = context or {}
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False
        model_obj = self.pool.get(match.model.model)
        if not isinstance(params, list):
            params = [params]
        obj_ids = []
        for p in params:
            obj_id = self.find(cr, uid, match, model_obj, p, context)
            if not obj_id:
                vals = self.process(cr, uid, match, p, context)
                if not vals:
                    continue
                obj_id = model_obj.create(cr, uid, vals, context)
            obj_ids.append(obj_id)
        return obj_ids

    def update(self, cr, uid, params, m_name, context=None):
        context = context or {}
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False
        model_obj = self.pool.get(match.model.model)
        if not isinstance(params, list):
            params = [params]
        obj_ids = []
        for p in params:
            obj_id = self.find(cr, uid, match, model_obj, p, context)
            if obj_id:
                vals = self.process(cr, uid, match, p, context)
                model_obj.write(cr, uid, obj_id, vals, context)
            obj_ids.append(obj_id)
        return obj_ids

    def push(self, cr, uid, params, m_name, context=None):
        context = context or {}
        match = self.get_match(cr, uid, m_name, context)
        if not match:
            return False

        if not isinstance(params, list):
            params = [params]

        obj_ids = []
        for p in params:
            vals = self.process(cr, uid, match, p, context)
            model_obj = self.pool.get(match.model.model)
            obj_id = self.find(cr, uid, match, model_obj, p, context)
            if obj_id:
                model_obj.write(cr, uid, obj_id, vals, context)
            else:
                obj_id = model_obj.create(cr, uid, vals, context)
            obj_ids.append(obj_id)
        return obj_ids
