#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  connection.py
#  
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import logging

from openerp import models, fields, api
from openerp.addons.oe_cenit_client import cenit_api


_logger = logging.getLogger(__name__)


class CenitConnection (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection'
    cenit_model = 'connection'
    cenit_models = 'connections'

    cenitID = fields.Char ('Cenit ID')
    
    name = fields.Char ('Name', required=True)
    url = fields.Char ('URL', required=True)

    key = fields.Char ('Key', readonly=True)
    token = fields.Char ('Token', readonly=True)

    url_parameters = fields.One2many (
        'cenit.parameter',
        'conn_url_id',
        string = 'Parameters'
    )
    header_parameters = fields.One2many (
        'cenit.parameter',
        'conn_header_id',
        string = 'Header Parameters'
    )
    template_parameters = fields.One2many (
        'cenit.parameter',
        'conn_template_id',
        string = 'Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values (self):
        vals = {
            'name': self.name,
            'url': self.url,
        }

        if self.cenitID:
            vals.update ({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append ({
                'key': param.key,
                'value': param.value
            })
        vals.update ({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append ({
                'key': header.key,
                'value': header.value
            })
        vals.update ({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append ({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update ({'template_parameters': template})
            
        return vals

    def _calculate_update (self, values):
        update = {}
        for k,v in values.items ():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0] ['id'],
                    'key': v[0] ['number'],
                    'token': v[0] ['token'],
                }

        return update


class CenitConnectionRole (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection.role'
    cenit_model = 'connection_role'
    cenit_models = 'connection_roles'

    cenitID = fields.Char ('Cenit ID')
    
    name = fields.Char ('Name', required=True)

    connections = fields.Many2many (
        'cenit.connection',
        string = 'Connections'
    )

    webhooks = fields.Many2many (
        'cenit.webhook',
        string = 'Webhooks'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values (self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update ({'id': self.cenitID})

        _reset = []

        connections = []
        for conn in self.connections:
            connections.append (conn._get_values ())

        vals.update ({
            'connections': connections
        })
        _reset.append ('connections')
            
        
        webhooks = []
        for hook in self.webhooks:
            webhooks.append (hook._get_values ())

        vals.update ({
            'webhooks': webhooks
        })
        _reset.append ('webhooks')

        vals.update ({
            '_reset': _reset
        })
        
        return vals


class CenitParameter (models.Model):
    _name = 'cenit.parameter'

    key = fields.Char ('Key', required=True)
    value = fields.Char ('Value', required=True)

    conn_url_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )
    
    conn_header_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )
    
    conn_template_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )

    hook_url_id = fields.Many2one (
        'cenit.webhook',
        string = 'Webhook'
    )

    hook_header_id = fields.Many2one (
        'cenit.webhook',
        string = 'Webhook'
    )

    hook_template_id = fields.Many2one (
        'cenit.webhook',
        string = 'Webhook'
    )


class CenitWebhook (cenit_api.CenitApi, models.Model):
    _name = 'cenit.webhook'
    cenit_model = 'webhook'
    cenit_models = 'webhooks'

    cenitID = fields.Char ('Cenit ID')

    name = fields.Char ('Name', required=True)
    path = fields.Char ('Path', required=True)
    purpose = fields.Selection (
        [
            ('send', 'Send'),
            ('receive', 'Receive')
        ],
        'Purpose', default='send', required=True
    )
    method = fields.Selection (
        [
            ('get', 'HTTP GET'),
            ('post', 'HTTP POST'),
            ('put', 'HTTP PUT'),
            ('delete', 'HTTP DELETE'),
        ],
        'Method', default='post', required=True
    )

    url_parameters = fields.One2many (
        'cenit.parameter',
        'hook_url_id',
        string = 'Parameters'
    )
    header_parameters = fields.One2many (
        'cenit.parameter',
        'hook_header_id',
        string = 'Header Parameters'
    )
    template_parameters = fields.One2many (
        'cenit.parameter',
        'hook_template_id',
        string = 'Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values (self):
        vals = {
            'name': self.name,
            'path': self.path,
            'purpose': self.purpose,
            'method': self.method,
        }

        if self.cenitID:
            vals.update ({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append ({
                'key': param.key,
                'value': param.value
            })
        vals.update ({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append ({
                'key': header.key,
                'value': header.value
            })
        vals.update ({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append ({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update ({'template_parameters': template})

        return vals


class CenitFlow (cenit_api.CenitApi, models.Model):

    def _get_translators (self): #, cr, uid, context=None):
        path = "/api/v1/translator"

        rc = self.get (
            self.env.cr,
            self.env.uid,
            path,
            context=self.env.context)

        if not isinstance (rc, list):
            rc = [rc]

        values = []
        
        for item in rc:
            _logger.info ("\n\nITEM: %s\n", item)
            it = item #.get ("translator")
            values.append ((it.get('id'), it.get('name')))

        return values
    
    _name = "cenit.flow"

    cenit_model = 'flow'
    cenit_models = 'flows'

    cenitID = fields.Char ('Cenit ID')

    name = fields.Char ('Name', size=64, required=True, unique=True)
    execution = fields.Selection (
        [
            ('only_manual', 'Only Manual'),
            ('interval', 'Interval'),
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Create & Update')
        ],
        'Execution', default='only_manual', required=True
    )
    cenit_translator = fields.Selection (
        _get_translators, string="Translator", required=True
    )

    data_type = fields.Many2one (
        'cenit.data_type', 'Source data type', required=True
    )
    scope = fields.Selection (
        [
            ('Event', 'Event source'),
            ('All', 'All sources'),
        ],
        'Source scope', default='Event', required=True
    )
    
    connection_role = fields.Many2one (
        'cenit.connection.role', 'Connection role', required=True
    )
    webhook = fields.Many2one (
        'cenit.webhook', 'Webhook', required=True
    )
    
    cenit_response_translator = fields.Selection (
        _get_translators, string="Response translator"
    )
    response_data_type = fields.Many2one (
        'cenit.data_type', 'Response data type'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values (self):
        vals = {
            'name': self.name,
            'active': True,
            'discard_events': False,
            'data_type_scope': self.scope,
        }

        if self.cenitID:
            vals.update ({'id': self.cenitID})

        if self.execution not in ('only_manual', 'interval'):
            event = {
                '_type': "Setup::Observer",
                'name': "%s > %s" % (self.data_type.name, self.execution),
                'data_type': {'id': self.data_type.datatype_cenitID},
                'triggers': {
                    'on_create': '{"created_at":{"0":{"o":"_not_null","v":["","",""]}}}',
                    'on_write': '{"updated_at":{"0":{"o":"_presence_change","v":["","",""]}}}',
                    'on_create_or_write': '{"updated_at":{"0":{"o":"_change","v":["","",""]}}}',
                } [self.execution]
            }
            vals.update ({
                'event': event
            })

        if self.cenit_translator:
            vals.update({
                'translator': {
                    'id': self.cenit_translator
                }
            })

        if self.data_type.datatype_cenitID:
            vals.update ({
                'custom_data_type': {
                    'id': self.data_type.datatype_cenitID
                }
            })

        if self.connection_role:
            vals.update({
                'connection_role': {
                    'id': self.connection_role.cenitID
                }
            })

        if self.webhook:
            vals.update({
                'webhook': {
                    'id': self.webhook.cenitID
                }
            })

        return vals

    #~ method = fields.Selection (
        #~ [
            #~ ('http_post', 'HTTP POST'),
            #~ ('local_post', 'LOCAL POST'),
            #~ ('file_post', 'FILE POST')
        #~ ], 'Method', default='http_post'
    #~ )
#~ 
    #~ base_action_rule = fields.Many2one (
        #~ 'base.action.rule', 'Action Rule'
    #~ )
    #~ ir_cron = fields.Many2one (
        #~ 'ir.cron', 'Action Cron'
    #~ )
#~ 
    #~ def create(self, cr, uid, vals, context=None):
        #~ obj_id = super(cenit_api.CenitApi, self).create(cr, uid, vals, context)
        #~ method = 'set_%s_execution' % vals['purpose']
        #~ getattr(self, method)(cr, uid, [obj_id], context)
        #~ return obj_id
#~ 
    #~ def write(self, cr, uid, ids, vals, context=None):
        #~ res = super(CenitFlow, self).write(cr, uid, ids, vals, context)
        #~ if vals.get('execution', False):
            #~ for obj in self.browse(cr, uid, ids):
                #~ method = 'set_%s_execution' % obj.purpose
                #~ getattr(self, method)(cr, uid, [obj.id], context)
        #~ return res
#~ 
    #~ def unlink(self, cr, uid, ids, context=None):
        #~ ref_obj = self.pool.get('cenit.flow.reference')
        #~ for oid in ids:
            #~ ref_ids = ref_obj.search(cr, uid, [('flow_id', '=', oid)])
            #~ if ref_ids:
                #~ ref_obj.unlink(cr, uid, ref_ids)
        #~ return super(CenitFlow, self).unlink(cr, uid, ids, context)
#~ 
    #~ def find(self, cr, uid, model, purpose, context=None):
        #~ domain = [('root', '=', model), ('purpose', '=', purpose)]
        #~ obj_ids = self.search(cr, uid, domain, context=context)
        #~ return obj_ids and self.browse(cr, uid, obj_ids[0]) or False
#~ 
    #~ def set_receive_execution(self, cr, uid, ids, context=None):
        #~ for obj in self.browse(cr, uid, ids):
            #~ if obj.method == 'http_post':
                #~ flow_reference = self.pool.get('cenit.flow.reference')
                #~ try:
                    #~ flow_reference.set_flow_in_cenit(cr, uid, obj, context)
                #~ except:
                    #~ pass
#~ 
    #~ def receive(self, cr, uid, model, data, context=None):
        #~ res = False
        #~ context = context or {}
        #~ obj = self.find(cr, uid, model.lower(), 'receive', context)
        #~ if obj:
            #~ klass = self.pool.get(obj.model_id.model)
            #~ if obj.format == 'json':
                #~ action = context.get('action', 'synch')
                #~ wh = self.pool.get('cenit.handler')
                #~ context.update({'receive_object': True})
                #~ xids = getattr(wh, action)(cr, uid, data, obj.root, context)
                #~ res = True
            #~ elif obj.format == 'edi':
                #~ for edi_document in data:
                    #~ klass.edi_import(cr, uid, edi_document, context)
                #~ res = True
        #~ return res
#~ 
    #~ def set_send_execution(self, cr, uid, ids, context=None):
        #~ obj = self.browse(cr, uid, ids[0], context)
        #~ ic_obj = self.pool.get('ir.cron')
        #~ ias_obj = self.pool.get('ir.actions.server')
        #~ bar_obj = self.pool.get('base.action.rule')
        #~ if obj.execution == 'only_manual':
            #~ if obj.base_action_rule_id:
                #~ bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
            #~ elif obj.ir_cron_id:
                #~ ic_obj.unlink(cr, uid, [obj.ir_cron_id.id])
        #~ elif obj.execution == 'interval':
            #~ if obj.ir_cron_id:
                #~ pass
            #~ else:
                #~ vals_ic = {
                    #~ 'name': 'push_%s' % obj.model_id.model,
                    #~ 'interval_number': 10,
                    #~ 'interval_type': 'minutes',
                    #~ 'numbercall': -1,
                    #~ 'model': 'cenit.flow',
                    #~ 'function': 'send_all',
                    #~ 'args': '([%s],)' % str(obj.id)
                #~ }
                #~ ic_id = ic_obj.create(cr, uid, vals_ic)
                #~ self.write(cr, uid, obj.id, {'ir_cron_id': ic_id})
                #~ if obj.base_action_rule_id:
                    #~ bar_obj.unlink(cr, uid, obj.base_action_rule_id.id)
        #~ elif obj.execution in ['on_create', 'on_write', 'on_create_or_write']:
            #~ if obj.base_action_rule_id:
                #~ bar_obj.write(cr, uid, obj.base_action_rule_id.id,
                              #~ {'kind': obj.execution})
            #~ else:
                #~ vals_ias = {
                    #~ 'name': 'push_%s' % obj.model_id.model,
                    #~ 'model_id': obj.model_id.id,
                    #~ 'state': 'code',
                    #~ 'code': "self.pool.get('cenit.flow').send(cr, uid, obj)"
                #~ }
                #~ ias_id = ias_obj.create(cr, uid, vals_ias)
                #~ vals_bar = {
                    #~ 'name': 'push_%s' % obj.model_id.model,
                    #~ 'active': True,
                    #~ 'kind': obj.execution,
                    #~ 'model_id': obj.model_id.id,
                    #~ 'server_action_ids': [(6, 0, [ias_id])]
                #~ }
                #~ bar_id = bar_obj.create(cr, uid, vals_bar)
                #~ self.write(cr, uid, obj.id, {'base_action_rule_id': bar_id})
                #~ if obj.ir_cron_id:
                    #~ ic_obj.unlink(cr, uid, obj.ir_cron_id.id)
        #~ return True
#~ 
    #~ def send(self, cr, uid, model_obj, context=None):
        #~ domain = [('model_id.model', '=', model_obj._name),
                  #~ ('purpose', '=', 'send')]
        #~ flow_obj_ids = self.search(cr, uid, domain, context=context)
        #~ if flow_obj_ids:
            #~ flow_obj = self.browse(cr, uid, flow_obj_ids[0])
            #~ if flow_obj.format == 'json':
                #~ ws = self.pool.get('cenit.serializer')
                #~ data = [ws.serialize(cr, uid, model_obj)]
            #~ elif flow_obj.format == 'edi':
                #~ data = self.pool.get(model_obj._name).edi_export(cr, uid,
                                                                 #~ [model_obj])
            #~ return self._send(cr, uid, flow_obj, data, context)
        #~ return False
#~ 
    #~ def send_all(self, cr, uid, ids, context=None):
        #~ obj = self.browse(cr, uid, ids[0])
        #~ ws = self.pool.get('cenit.serializer')
        #~ mo = self.pool.get(obj.model_id.model, False)
        #~ if mo:
            #~ models = []
            #~ model_ids = mo.search(cr, uid, [], context=context)
            #~ if obj.format == 'json':
                #~ for x in mo.browse(cr, uid, model_ids, context):
                    #~ models.append(ws.serialize(cr, uid, x))
            #~ elif obj.format == 'edi' and hasattr(mo, 'edi_export'):
                #~ models = mo.edi_export(cr, uid, mo.browse(cr, uid, model_ids))
            #~ if model_ids:
                #~ return self._send(cr, uid, obj, models, context)
        #~ return False
#~ 
    #~ def _send(self, cr, uid, obj, data, context=None):
        #~ return getattr(self, obj.method)(cr, uid, obj, data, context)
#~ 
    #~ def http_post(self, cr, uid, obj, data, context=None):
        #~ client = self.pool.get('cenit.client').instance(cr, uid, context)
        #~ p = inflect.engine()
        #~ payload = simplejson.dumps({p.plural(obj.root.lower()): data})
        #~ headers = {
            #~ 'Content-Type': 'application/json',
            #~ 'X-Hub-Store': client.connection_key,
            #~ 'X-Hub-Access-Token': client.connection_token
        #~ }
        #~ url = client.url + '/cenit'
        #~ r = requests.post(url, data=payload, headers=headers)
        #~ return r.status_code
#~ 
    #~ def local_post(self, cr, uid, obj, data, context=None):
        #~ db = context.get('partner_db')
        #~ if db:
            #~ registry = openerp.modules.registry.RegistryManager.get(db)
            #~ with registry.cursor() as rcr:
                #~ uids = registry['res.users'].search(rcr, SI,
                                                #~ [('oauth_uid', '!=', False)])
                #~ ruid = uids and uids[0] or SI
                #~ model = obj.root.lower()
                #~ return registry['cenit.flow'].receive(rcr, ruid, model, data)
#~ 
    #~ def file_post(self, cr, uid, obj, data, context=None):
        #~ p = inflect.engine()
        #~ payload = simplejson.dumps({p.plural(obj.root.lower()): data})
        #~ f = open('/home/cesar/file_post', 'w')
        #~ f.write(payload)
        #~ f.close()
#~ 
    #~ def clean_reference(self, cr, uid, ids, context=None):
        #~ ref = self.pool.get('cenit.flow.reference')
        #~ ref_id = ref.search(cr, uid, [('flow_id', 'in', ids)], context=context)
        #~ if ref_id:
            #~ try:
                #~ ref.unlink(cr, uid, ref_id)
            #~ except:
                #~ cr.execute('delete from cenit_flow_reference where id = %s',
                           #~ (ref_id[0],))
        #~ return True

