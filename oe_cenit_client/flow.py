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
import requests
import simplejson
import inflect
from openerp import models, fields


class CenitFlow(models.Model):
    _name = 'cenit.flow'

    name = fields.Char('Name', size=64, required=1)
    root = fields.Char('Root', size=64, required=1)
    model_id = fields.Many2one('ir.model', 'Model', required=1)
    purpose = fields.Selection([('send', 'Send'), ('receive', 'Receive')],
                               'Purpose', default='send', required=1)
    execution = fields.Selection([('only_manual', 'Only Manual'),
                                  ('interval', 'Interval'),
                                  ('on_create', 'On Create'),
                                  ('on_write', 'On Update'),
                                  ('on_create_or_write', 'On Create & Update')
                                  ], 'Execution', default='only_manual')
    method = fields.Selection([('http_post', 'HTTP POST')], 'Method',
                              default='http_post')

    base_action_rule_id = fields.Many2one('base.action.rule', 'Action Rule')
    ir_cron_id = fields.Many2one('ir.cron', 'Action Cron')

    def create(self, cr, uid, vals, context=None):
        obj_id = super(CenitFlow, self).create(cr, uid, vals, context)
        method = 'set_%s_execution' % vals['purpose']
        getattr(self, method)(cr, uid, [obj_id], context)
        return obj_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(CenitFlow, self).write(cr, uid, ids, vals, context)
        if vals.get('execution', False):
            for obj in self.browse(cr, uid, ids):
                method = 'set_%s_execution' % obj.purpose
                getattr(self, method)(cr, uid, [obj.id], context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        ref_obj = self.pool.get('cenit.flow.reference')
        for oid in ids:
            ref_ids = ref_obj.search(cr, uid, [('flow_id', '=', oid)])
            if ref_ids:
                ref_obj.unlink(cr, uid, ref_ids)
        return super(CenitFlow, self).unlink(cr, uid, ids, context)

    def set_send_execution(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        ic_obj = self.pool.get('ir.cron')
        ias_obj = self.pool.get('ir.actions.server')
        bar_obj = self.pool.get('base.action.rule')
        if obj.execution == 'only_manual':
            if obj.base_action_rule_id:
                bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
            elif obj.ir_cron_id:
                ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        elif obj.execution == 'interval':
            if obj.ir_cron_id:
                pass
            else:
                vals_ic = {
                    'name': 'push_%s' % obj.model_id.model,
                    'interval_number': 10,
                    'interval_type': 'minutes',
                    'numbercall': -1,
                    'model': 'cenit.flow',
                    'function': 'process_all',
                    'args': '([%s],)' % str(obj.id)
                }
                ic_id = ic_obj.create(cr, uid, vals_ic)
                self.write(cr, uid, obj.id, {'ir_cron_id': ic_id})
                if obj.base_action_rule_id:
                    bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
        elif obj.execution in ['on_create', 'on_write', 'on_create_or_write']:
            if obj.base_action_rule_id:
                bar_obj.write(cr, uid, obj.base_action_rule_id.id,
                              {'kind': obj.execution})
            else:
                vals_ias = {
                    'name': 'push_%s' % obj.model_id.model,
                    'model_id': obj.model_id.id,
                    'state': 'code',
                    'code': "self.pool.get('cenit.flow').execute(cr, uid, obj)"
                }
                ias_id = ias_obj.create(cr, uid, vals_ias)
                vals_bar = {
                    'name': 'push_%s' % obj.model_id.model,
                    'active': True,
                    'kind': obj.execution,
                    'model_id': obj.model_id.id,
                    'server_action_ids': [(6, 0, [ias_id])]
                }
                bar_id = bar_obj.create(cr, uid, vals_bar)
                self.write(cr, uid, obj.id, {'base_action_rule_id': bar_id})
                if obj.ir_cron_id:
                    ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        return True

    def set_receive_execution(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        flow_reference = self.pool.get('cenit.flow.reference')
        return flow_reference.set_flow_in_cenit(cr, uid, obj, context)

    def execute(self, cr, uid, model_obj, context=None):
        if model_obj.sender == 'client':
            return False
        domain = [('model_id.model', '=', model_obj._name)]
        flow_obj_ids = self.search(cr, uid, domain, context=context)
        if flow_obj_ids:
            flow_obj = self.browse(cr, uid, flow_obj_ids[0])
            ws = self.pool.get('cenit.serializer')
            data = [ws.serialize(cr, uid, model_obj)]
            return self.process(cr, uid, flow_obj, data, context)
        return False

    def process_all(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        ws = self.pool.get('cenit.serializer')
        mo = self.pool.get(obj.model_id.model, False)
        if mo:
            models = []
            model_ids = mo.search(cr, uid, [], context=context)
            for x in mo.browse(cr, uid, model_ids, context):
                models.append(ws.serialize(cr, uid, x))
            if models:
                return self.process(cr, uid, obj, models, context)
        return False

    def process(self, cr, uid, obj, data, context=None):
        return getattr(self, obj.method)(cr, uid, obj, data)

    def http_post(self, cr, uid, obj, data, context=None):
        client = self.pool.get('cenit.client').instance(cr, uid, context)
        p = inflect.engine()
        payload = simplejson.dumps({p.plural(obj.root.lower()): data})
        headers = {
            'Content-Type': 'application/json',
            'X-Hub-Store': cr.dbname,
            'X-Hub-Access-Token': client.connection_token
        }
        url = client.url + '/cenit'
        r = requests.post(url, data=payload, headers=headers)
        return r.status_code


class CenitFlowReference(models.Model):
    _name = 'cenit.flow.reference'

    flow_id = fields.Many2one('cenit.flow', 'Flow')
    flow_ref = fields.Char('Flow', size=128)
    role_ref = fields.Char('Role', size=128)
    data_type_ref = fields.Char('Role', size=128)
    webhook_ref = fields.Char('Role', size=128)
    event_ref = fields.Char('Role', size=128)

    def unlink(self, cr, uid, ids, context=None):
        client = self.pool.get('cenit.client')
        for obj in self.browse(cr, uid, ids):
            client.delete(cr, uid, '/setup/flows/%s' % obj.flow_ref)
        return super(CenitFlowReference, self).unlink(cr, uid, ids, context)

    def set_flow_in_cenit(self, cr, uid, flow, context=None):
        ref = {}
        client = self.pool.get('cenit.client')
        ref_id = self.search(cr, uid, [('flow_id', '=', flow.id)])
        if not ref_id:
            ref['flow_id'] = flow.id
            ref['role_ref'] = self.get_role(cr, uid, context)
            ref['webhook_ref'] = self.post_webhook(cr, uid, flow, context)
            ref['data_type_ref'] = self.get_data_type(cr, uid, flow, context)
            ref['event_ref'] = self.get_event(cr, uid, flow, context)
            vals = {
                'name': flow.name,
                'purpose': 'send',
                'connection_role_id': ref['role_ref'],
                'data_type_id': ref['data_type_ref'],
                'webhook_id': ref['webhook_ref'],
                'event_id': ref['event_ref']
            }
            response = client.post(cr, uid, '/setup/flows', {'flow': vals})
            ref.update({'flow_ref': response['id']['$oid']})
            self.create(cr, uid, ref)
        return True

    def get_role(self, cr, uid, context=None):
        client = self.pool.get('cenit.client').instance(cr, uid)
        return client.connection_role_ref

    def get_data_type(self, cr, uid, flow, context=None):
        client = self.pool.get('cenit.client')
        data_type_name = flow.root.capitalize()
        for element in client.get(cr, uid, '/setup/data_types'):
            if element['name'] == data_type_name:
                return element['id']['$oid']
        return False

    def get_event(self, cr, uid, flow, context=None):
        client = self.pool.get('cenit.client')
        event = 'created_at'
        if flow.execution == 'on_write':
            event = 'updated_at'
        event_name = '%s on %s' % (flow.root, event)
        for element in client.get(cr, uid, '/setup/events'):
            if element['name'] == event_name:
                return element['id']['$oid']
        return False

    def post_webhook(self, cr, uid, flow, context=None):
        vals = {
            'name': flow.name,
            'path': 'add_%s' % flow.root.lower(),
        }
        client = self.pool.get('cenit.client')
        response = client.post(cr, uid, '/setup/webhooks', {'webhook': vals})
        return response['id']['$oid']
