# -*- coding: utf-8 -*-

from openerp import models


class CenitSerializer(models.TransientModel):
    _name = 'cenit.serializer'

    def find_reference(self, cr, uid, field, obj, context=None):
        return getattr(getattr(obj, field.name), 'name')

    def serialize(self, cr, uid, obj, context=None):
        vals = {}
        wdt = self.pool.get('cenit.data_type')
        matching_id = wdt.search(cr, uid, [('model.model', '=', obj._name)],
                                 context=context)
        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            columns = self.pool.get(obj._name)._columns
            for field in match.lines:
                if field.line_type == 'field' and getattr(obj, field.name):
                    vals[field.value] = getattr(obj, field.name)
                    #~ if field.name in columns:
                        #~ if columns[field.name]._type in ['selection', 'date']:
                            #~ vals[field.value] = getattr(obj, field.name)
                            #~ continue
                    #~ try:
                        #~ vals[field.value] = eval(getattr(obj, field.name))
                        #~ if type(vals[field.value]) == type:
                            #~ vals[field.value] = getattr(obj, field.name)
                    #~ except:
                        #~ vals[field.value] = getattr(obj, field.name)
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
