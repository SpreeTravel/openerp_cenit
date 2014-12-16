# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
import requests
import simplejson


class CenitClient(models.Model):
    _name = 'cenit.client'

    name = fields.Char('Name', size=128, required=1)
    url = fields.Char('URL', size=255)
    store = fields.Char('Store', size=64)
    token = fields.Char('Token', size=64)
    push_object_ids = fields.One2many('cenit.push.object', 'client_id',
                                      'Models')

    def push(self, cr, uid, ids, context=None):
        res = []
        obj = self.browse(cr, uid, ids[0], context)
        for po in obj.push_object_ids:
            status_code = po.push_all(cr, uid, [po.id], context)
            res.append(status_code)
        return res


class cenitPushObject(models.Model):
    _name = 'cenit.push.object'

    client_id = fields.Many2one('cenit.client', 'Client')
    root = fields.Char('Root', size=64)
    model_id = fields.Many2one('ir.model', 'Model')
    push_type = fields.Selection([('only_manual', 'Only Manual'),
                                  ('interval', 'Interval'),
                                  ('on_create', 'On Create'),
                                  ('on_write', 'On Update'),
                                  ('on_create_or_write', 'On Create & Update')
                                  ], 'Push Type', default='only_manual')
    push_method = fields.Selection([('push_http_post', 'HTTP POST')], 'Method',
                                   default='push_http_post')
    base_action_rule_id = fields.Many2one('base.action.rule', 'Action Rule')
    ir_cron_id = fields.Many2one('ir.cron', 'Action Cron')

    def create(self, cr, uid, vals, context=None):
        obj_id = super(cenitPushObject, self).create(cr, uid, vals, context)
        if vals.get('push_type', False):
            obj = self.browse(cr, uid, obj_id)
            self.set_push_type(cr, uid, obj, context)
        return obj_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(cenitPushObject, self).write(cr, uid, ids, vals, context)
        if vals.get('push_type', False):
            for obj in self.browse(cr, uid, ids):
                self.set_push_type(cr, uid, obj, context)
        return res

    def set_push_type(self, cr, uid, obj, context=None):
        ic_obj = self.pool.get('ir.cron')
        ias_obj = self.pool.get('ir.actions.server')
        bar_obj = self.pool.get('base.action.rule')
        if obj.push_type == 'only_manual':
            if obj.base_action_rule_id:
                bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
            elif obj.ir_cron_id:
                ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        elif obj.push_type == 'interval':
            if obj.ir_cron_id:
                pass
            else:
                vals_ic = {
                    'name': 'push_%s' % obj.model_id.model,
                    'interval_number': 10,
                    'interval_type': 'minutes',
                    'numbercall': -1,
                    'model': 'cenit.push.object',
                    'function': 'push_all',
                    'args': '([%s],)' % str(obj.id)
                }
                ic_id = ic_obj.create(cr, uid, vals_ic)
                self.write(cr, uid, obj.id, {'ir_cron_id': ic_id})
                if obj.base_action_rule_id:
                    bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
        elif obj.push_type in ['on_create', 'on_write', 'on_create_or_write']:
            if obj.base_action_rule_id:
                bar_obj.write(cr, uid, obj.base_action_rule_id.id,
                              {'kind': obj.push_type})
            else:
                vals_ias = {
                    'name': 'push_%s' % obj.model_id.model,
                    'model_id': obj.model_id.id,
                    'state': 'code',
                    'code': "self.pool.get('cenit.push.object').process(cr, uid, obj, {'client_id': %s})" % str(obj.client_id.id)
                }
                ias_id = ias_obj.create(cr, uid, vals_ias)
                vals_bar = {
                    'name': 'push_%s' % obj.model_id.model,
                    'active': True,
                    'kind': obj.push_type,
                    'model_id': obj.model_id.id,
                    'server_action_ids': [(6, 0, [ias_id])]
                }
                bar_id = bar_obj.create(cr, uid, vals_bar)
                self.write(cr, uid, obj.id, {'base_action_rule_id': bar_id})
                if obj.ir_cron_id:
                    ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        return True

    def process(self, cr, uid, model_obj, context=None):
        domain = [('model_id.model', '=', model_obj._name)]
        if context.get('client_id', False):
            domain.append(('client_id', '=', context.get('client_id')))
        push_obj_ids = self.search(cr, uid, domain, context=context)
        if push_obj_ids:
            push_obj = self.browse(cr, uid, push_obj_ids[0])
            ws = self.pool.get('cenit.serializer')
            data = [ws.serialize(cr, uid, model_obj)]
            return self.push(cr, uid, push_obj, data, context)
        return False

    def push_all(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        ws = self.pool.get('cenit.serializer')
        mo = self.pool.get(obj.model_id.model, False)
        if mo:
            models = []
            model_ids = mo.search(cr, uid, [], context=context)
            for x in mo.browse(cr, uid, model_ids, context):
                models.append(ws.serialize(cr, uid, x))
            return self.push(cr, uid, obj, models, context)
        return False

    def push(self, cr, uid, obj, data, context=None):
        return getattr(self, obj.push_method)(cr, uid, obj, data)

    def push_http_post(self, cr, uid, obj, data, context=None):
        payload = simplejson.dumps({obj.root: data})
        headers = {
            'Content-Type': 'application/json',
            'X-Hub-Store': obj.client_id.store,
            'X-Hub-Access-Token': obj.client_id.token
        }
        r = requests.post(obj.client_id.url, data=payload, headers=headers)
        return r.status_code
