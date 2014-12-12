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


class WombatClient(models.Model):
    _name = 'wombat.client'

    name = fields.Char('Name', size=128, required=1)
    url = fields.Char('URL', size=255)
    store = fields.Char('Store', size=64)
    token = fields.Char('Token', size=64)
    push_object_ids = fields.One2many('wombat.push.object', 'client_id',
                                      'Models')

    def push(self, cr, uid, ids, context=None):
        res = []
        ws = self.pool.get('wombat.serializer')
        obj = self.browse(cr, uid, ids[0], context)
        for po in obj.push_object_ids:
            mo = self.pool.get(po.model_id.model, False)
            if mo:
                models = []
                model_ids = mo.search(cr, uid, [], context=context)
                for x in mo.browse(cr, uid, model_ids, context):
                    models.append(ws.serialize(cr, uid, x))
                payload = simplejson.dumps({po.root: models})
                headers = {
                    'Content-Type': 'application/json',
                    'X-Hub-Store': obj.store,
                    'X-Hub-Access-Token': obj.token
                }
                r = requests.post(obj.url, data=payload, headers=headers)
                res.append(r.status_code)
        return res


class WombatPushObject(models.Model):
    _name = 'wombat.push.object'

    client_id = fields.Many2one('wombat.client', 'Client')
    root = fields.Char('Root', size=64)
    model_id = fields.Many2one('ir.model', 'Model')
    push_type = fields.Selection([('manual', 'Manual'),
                                  ('on_create', 'On Create'),
                                  ('on_write', 'On Update'),
                                  ('on_create_or_write', 'On Create & Update')
                                  ], 'Push Type', default='manual')
    push_method = fields.Selection([('push_http_post', 'HTTP POST')], 'Method',
                                   default='push_http_post')
    base_action_rule_id = fields.Many2one('base.action.rule', 'Action Rule')

    def create(self, cr, uid, vals, context=None):
        obj_id = super(WombatPushObject, self).create(cr, uid, vals, context)
        if vals.get('push_type', 'manual') != 'manual':
            obj = self.browse(cr, uid, obj_id)
            self.set_action_rule(cr, uid, obj, context)
        return obj_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(WombatPushObject, self).write(cr, uid, ids, vals, context)
        if vals.get('push_type', False):
            for obj in self.browse(cr, uid, ids):
                self.set_action_rule(cr, uid, obj, context)
        return res

    def set_action_rule(self, cr, uid, obj, context=None):
        ias_obj = self.pool.get('ir.actions.server')
        bar_obj = self.pool.get('base.action.rule')
        if obj.base_action_rule_id:
            if obj.push_type == 'manual':
                res = bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
            else:
                res = bar_obj.write(cr, uid, obj.base_action_rule_id.id,
                                    {'kind': obj.push_type})
        else:
            vals_ias = {
                'name': 'push_%s' % obj.model_id.model,
                'model_id': obj.model_id.id,
                'state': 'code',
                'code': "self.pool.get('wombat.push.object').%s(cr, uid, obj, {'client_id': %s})" % (obj.push_method, str(obj.client_id.id))
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
            res = self.write(cr, uid, obj.id, {'base_action_rule_id': bar_id})
        return res

    def push_http_post(self, cr, uid, obj, context=None):
        domain = [('model_id.model', '=', obj._name)]
        if context.get('client_id', False):
            domain.append(('client_id', '=', context.get['client_id']))
        push_obj_ids = self.search(cr, uid, domain, context=context)
        if push_obj_ids:
            push_obj = self.browse(cr, uid, push_obj_ids[0])
            ws = self.pool.get('wombat.serializer')
            data = ws.serialize(cr, uid, obj)
            payload = simplejson.dumps({push_obj.root: [data]})
            headers = {
                'Content-Type': 'application/json',
                'X-Hub-Store': push_obj.client_id.store,
                'X-Hub-Access-Token': push_obj.client_id.token
            }
            r = requests.post(push_obj.client_id.url, data=payload,
                              headers=headers)
            return r.status_code
        return False
