# -*- coding: utf-8 -*-

from openerp import fields


class CenitMixin(object):

    sender = fields.Char('Sender', size=64)

    def create(self, cr, uid, vals, context=None):
        vals['sender'] = vals.get('sender', 'local')
        return super(CenitMixin, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals['sender'] = vals.get('sender', 'local')
        return super(CenitMixin, self).write(cr, uid, ids, vals, context)
