# -*- coding: utf-8 -*-

from openerp import models


class WombatSerializer(models.TransientModel):
    _name = 'wombat.serializer'

    def find_reference(self, cr, uid, field, obj, context=None):
        return getattr(getattr(obj, field.name), 'name')

    def serialize(self, cr, uid, obj, context=None):
        vals = {}
        wdt = self.pool.get('wombat.data.type')
        matching_id = wdt.search(cr, uid, [('model_id.model', '=', obj._name)],
                                 context=context)
        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            for field in match.line_ids:
                if field.line_type == 'field':
                    try:
                        vals[field.value] = eval(getattr(obj, field.name))
                    except:
                        vals[field.value] = getattr(obj, field.name)
                elif field.line_type == 'model':
                    relation = getattr(obj, field.name)
                    if field.line_cardinality == '2many':
                        vals[field.value] = [self.serialize(cr, uid, x, context) for x in relation]
                    else:
                        vals[field.value] = self.serialize(cr, uid, relation, context)
                elif field.line_type == 'reference':
                    vals[field.value] = self.find_reference(cr, uid, field, obj, context)
                elif field.line_type == 'default':
                    vals[field.name] = field.value
        return vals

    def serialize_model_id(self, cr, uid, model, oid, context=None):
        obj = self.pool.get(model).browse(cr, uid, oid)
        return self.serialize(cr, uid, obj, context)