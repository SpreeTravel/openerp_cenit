# -*- coding: utf-8 -*-

from openerp import models


class WombatSerializer(models.TransientModel):
    _name = 'wombat.serializer'

    def serialize(self, cr, uid, obj, context=None):
        vals = {}
        wdt = self.pool.get('wombat.data.type')
        matching_id = wdt.search(cr, uid, [('name', '=', obj._name)],
                                 context=context)
        if matching_id:
            match = wdt.browse(cr, uid, matching_id[0], context)
            for field in match.line_ids:
                if field.line_type == 'field':
                    vals[field.value] = getattr(obj, field.name)
                elif field.line_type == 'default':
                    vals[field.name] = field.value
        return vals
