# -*- coding: utf-8 -*-
from openerp import fields
from openerp.addons.saas_utils import connector


class SenderMixin(object):

    sender = fields.Char('Sender', size=64)

    def create(self, cr, uid, vals, context=None):
        vals['sender'] = vals.get('sender', 'local')
        return super(SenderMixin, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        vals['sender'] = vals.get('sender', 'local')
        return super(SenderMixin, self).write(cr, uid, ids, vals, context)


class SynchMixin(object):

    def get_root(self, cr, uid, model):
        wdt = self.pool.get('cenit.data.type')
        matching_id = wdt.search(cr, uid, [('model_id.model', '=', model)])
        if matching_id:
            return wdt.browse(cr, uid, matching_id[0]).name
        return False

    def pull_object(self, cr, uid, oid, db, model):
        wh = self.pool.get('cenit.handler')
        vals = connector.call(db, 'cenit.serializer', 'serialize_model_id', model, oid)
        root = self.get_root(cr, uid, model)
        return wh.add(cr, 1, vals, root)

    def push_object(self, cr, uid, oid, db, model, method='add'):
        ws = self.pool.get('cenit.serializer')
        vals = ws.serialize_model_id(cr, uid, model, oid)
        root = self.get_root(cr, uid, model)
        return connector.call(db, 'cenit.handler', method, vals, root)

    def find_object(self, cr, uid, db, model, name):
        res = connector.call(db, model, 'search', [('name', '=', name)])
        return res and res[0] or False
