# -*- coding: utf-8 -*-

import logging
import simplejson

from openerp import models


_logger = logging.getLogger(__name__)


class CenitSerializer(models.TransientModel):
    _name = 'cenit.serializer'

    def _get_checker (self, schema_type):
        return {
            'integer': int,
            'number': float,
            'boolean': bool,
        }.get (schema_type['type'], str)

    def find_reference(self, cr, uid, field, obj, context=None):
        # TODO: Future me, please remember to do some kind of checking on the
        #       availability of the field name.
        model = getattr(obj, field.name)
        _logger.info ("\n\n[Serial] %s::%s\n", obj, model)
        names = []
        for record in model:
            name = getattr(record, 'name', False)
            _logger.info ("\n\n[Serial] %s->%s\n", field.name, name)
            _logger.info ("\n\n[Serial] %s\n", dir(name))

            if not name:
                name = False
            names.append (name)

        if field.line_cardinality == "2many":
            return names

        if len(names) > 0:
            return names[0]
        return False

    def serialize(self, cr, uid, obj, context=None):
        vals = {}
        wdt = self.pool.get('cenit.data_type')
        matching_id = wdt.search(cr, uid, [('model.model', '=', obj._name)],
                                 context=context)

        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            schema = simplejson.loads (match.schema) ['properties']

            columns = self.pool.get(obj._name)._columns
            for field in match.lines:
                if field.line_type == 'field' and getattr(obj, field.name):
                    checker = self._get_checker (schema.get (field.value))
                    vals[field.value] = checker (getattr(obj, field.name))
                elif field.line_type == 'model':
                    relation = getattr(obj, field.name)
                    if field.line_cardinality == '2many':
                        vals[field.value] = [self.serialize(cr, uid, x, context) for x in relation]
                    else:
                        vals[field.value] = self.serialize(cr, uid, relation, context)
                elif field.line_type == 'reference':
                    #~ if field.line_cardinality == '2many':
                        #~ pass
                    #~ else:
                    vals[field.value] = self.find_reference(cr, uid, field, obj, context)
                elif field.line_type == 'default':
                    vals[field.name] = field.value
        _logger.info ("\n\nSerialized values: %s\n", vals)
        return vals

    def serialize_model_id(self, cr, uid, model, oid, context=None):
        obj = self.pool.get(model).browse(cr, uid, oid)
        return self.serialize(cr, uid, obj, context)
