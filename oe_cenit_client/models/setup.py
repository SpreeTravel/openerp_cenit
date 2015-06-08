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
import simplejson

from openerp import models, fields, api
from openerp.addons.oe_cenit_client import cenit_api  # @UnresolvedImport

from datetime import datetime


_logger = logging.getLogger(__name__)


class CenitConnection (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection'
    cenit_model = 'connection'
    cenit_models = 'connections'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    url = fields.Char('URL', required=True)

    key = fields.Char('Key', readonly=True)
    token = fields.Char('Token', readonly=True)

    url_parameters = fields.One2many(
        'cenit.parameter',
        'conn_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'conn_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'conn_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'url': self.url,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})

        return vals

    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],
                }

        return update

    @api.one
    def _get_conn_data(self):
        path = "/api/v1/connection/%s" % self.cenitID
        rc = self.get(path)

        vals = {
            'key': rc['connection']['number'],
            'token': rc['connection']['token'],
        }

        self.with_context(local=True).write(vals)
        return

    @api.model
    def create(self, vals):
        _id = super(CenitConnection, self).create(vals)
        obj = self.browse(_id)

        if obj.cenitID:
            obj._get_conn_data()

        return _id


class CenitConnectionRole (cenit_api.CenitApi, models.Model):
    _name = 'cenit.connection.role'
    cenit_model = 'connection_role'
    cenit_models = 'connection_roles'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)

    connections = fields.Many2many(
        'cenit.connection',
        string='Connections'
    )

    webhooks = fields.Many2many(
        'cenit.webhook',
        string='Webhooks'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update({'id': self.cenitID})

        _reset = []

        connections = []
        for conn in self.connections:
            connections.append(conn._get_values())

        vals.update({
            'connections': connections
        })
        _reset.append('connections')

        webhooks = []
        for hook in self.webhooks:
            webhooks.append(hook._get_values())

        vals.update({
            'webhooks': webhooks
        })
        _reset.append('webhooks')

        vals.update({
            '_reset': _reset
        })

        return vals


class CenitParameter (models.Model):
    _name = 'cenit.parameter'

    key = fields.Char('Key', required=True)
    value = fields.Char('Value', required=True)

    conn_url_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    conn_header_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    conn_template_id = fields.Many2one(
        'cenit.connection',
        string='Connection'
    )

    hook_url_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )

    hook_header_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )

    hook_template_id = fields.Many2one(
        'cenit.webhook',
        string='Webhook'
    )


class CenitWebhook (cenit_api.CenitApi, models.Model):
    @api.depends('method')
    def _compute_purpose(self):
        self.purpose = {
            'get': 'send'
        }.get(self.method, 'receive')

    _name = 'cenit.webhook'
    cenit_model = 'webhook'
    cenit_models = 'webhooks'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', required=True)
    path = fields.Char('Path', required=True)
    purpose = fields.Char(compute='_compute_purpose', store=True)
    method = fields.Selection(
        [
            ('get', 'HTTP GET'),
            ('put', 'HTTP PUT'),
            ('post', 'HTTP POST'),
            ('delete', 'HTTP DELETE'),
        ],
        'Method', default='post', required=True
    )

    url_parameters = fields.One2many(
        'cenit.parameter',
        'hook_url_id',
        string='Parameters'
    )
    header_parameters = fields.One2many(
        'cenit.parameter',
        'hook_header_id',
        string='Header Parameters'
    )
    template_parameters = fields.One2many(
        'cenit.parameter',
        'hook_template_id',
        string='Template Parameters'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'path': self.path,
            'purpose': self.purpose,
            'method': self.method,
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        params = []
        for param in self.url_parameters:
            params.append({
                'key': param.key,
                'value': param.value
            })
        vals.update({'parameters': params})

        headers = []
        for header in self.header_parameters:
            headers.append({
                'key': header.key,
                'value': header.value
            })
        vals.update({'headers': headers})

        template = []
        for tpl in self.template_parameters:
            template.append({
                'key': tpl.key,
                'value': tpl.value
            })
        vals.update({'template_parameters': template})

        return vals

    @api.model
    def create(self, vals):
        return super(CenitWebhook, self).create(vals)


class CenitEvent (models.Model):
    _name = "cenit.event"

    cenitID = fields.Char('CenitID')
    name = fields.Char('Name', required=True, unique=True)
    type_ = fields.Selection(
        [
            ('Setup::Observer', 'Observer'),
            ('Setup::Scheduler', 'Scheduler'),
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_update', 'On Create or Update'),
            ('on_create_or_update', 'On Create or Update'),
            ('interval', 'Interval'),
            ('only_manual', 'Only Manual'),
        ],
        string="Type"
    )
    schema = fields.Many2one(
        'cenit.schema',
        string = 'Schema'
    )


class CenitTranslator (models.Model):
    _name = "cenit.translator"

    cenitID = fields.Char('CenitID')
    name = fields.Char('Name', required=True, unique=True)
    type_ = fields.Char("Type")
    mime_type = fields.Char('MIME Type')
    schema = fields.Many2one(
        'cenit.schema',
        string = 'Schema'
    )


class CenitFlow (cenit_api.CenitApi, models.Model):

    def _get_translators(self):
        path = "/api/v1/translator"

        rc = self.get(path)

        if not isinstance(rc, list):
            rc = [rc]

        values = []

        for item in rc:
            it = item.get("translator")
            #~ if self.format_ and (it.get('mime_type', '') != self.format_):
                #~ continue
            #~ if self.webhook and (it.get('type', '') != self.webhook.purpose):
                #~ continue
            values.append((it.get('id'), it.get('name')))

        return values

    def _get_events(self):
        path = "/api/v1/event"
        rc = self.get(path)

        if not isinstance(rc, list):
            rc = [rc]

        values = []

        for item in rc:
            it = item.values()[0]
            values.append((it.get('id'), it.get('name')))

        values.extend ([
            (False, '-------------'),
            ('interval', 'Interval'),
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Create & Update')
        ])
        return values

    _name = "cenit.flow"

    cenit_model = 'flow'
    cenit_models = 'flows'

    cenitID = fields.Char('Cenit ID')

    name = fields.Char('Name', size=64, required=True, unique=True)
    event = fields.Many2one("cenit.event", string='Event')

    cron = fields.Many2one('ir.cron', string='Cron rules')
    base_action_rules = fields.Many2many(
        'base.action.rule', string='Action Rule'
    )

    format_ = fields.Selection(
        [
            ('application/json', 'JSON'),
            ('application/EDI-X12', 'EDI')
        ],
        'Format', default='application/json', required=True
    )
    local = fields.Boolean('Bypass Cenit', default=False)
    cenit_translator = fields.Many2one('cenit.translator', "Translator")

    schema = fields.Many2one(
        'cenit.schema', 'Schema', required=True
    )
    data_type = fields.Many2one(
        'cenit.data_type', string='Source data type'
    )

    webhook = fields.Many2one(
        'cenit.webhook', string='Webhook', required=True
    )
    connection_role = fields.Many2one(
        'cenit.connection.role', string='Connection role'
    )

    method = fields.Selection(related="webhook.method")

    cenit_response_translator = fields.Selection(
        [], string="Response translator"
    )
    response_data_type = fields.Many2one(
        'cenit.data_type', string='Response data type'
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    def _get_values(self):
        vals = {
            'name': self.name,
            'active': True,
            'discard_events': False,
            'data_type_scope': 'All',
        }

        if self.cenitID:
            vals.update({'id': self.cenitID})

        odoo_events = (
            'only_manual',
            'interval',
            'on_create',
            'on_write',
            'on_create_or_write'
        )

        if self.event not in odoo_events:
            event = {
                "id": self.event.cenitID
            }
            vals.update({
                'event': event,
                'data_type_scope': 'Event',
            })
        elif self.event not in ('only_manual', 'interval'):
            cr = '{"created_at":{"0":{"o":"_not_null","v":["","",""]}}}'
            wr = '{"updated_at":{"0":{"o":"_presence_change","v":["","",""]}}}'
            cr_wr = '{"updated_at":{"0":{"o":"_change","v":["","",""]}}}'
            event = {
                '_type': "Setup::Observer",
                'name': "%s::%s > %s @ %s" % (
                    self.data_type.library.name,
                    self.data_type.name,
                    self.execution,
                    datetime.now().ctime()
                ),
                'data_type': {'id': self.data_type.schema.datatype_cenitID},
                'triggers': {
                    'on_create': cr,
                    'on_write': wr,
                    'on_create_or_write': cr_wr,
                }[self.event]
            }

            vals.update({
                'event': event,
                'data_type_scope': 'Event',
            })

        if self.cenit_translator:
            vals.update({
                'translator': {
                    'id': self.cenit_translator.cenitID
                }
            })

        if self.schema.datatype_cenitID:
            vals.update({
                'custom_data_type': {
                    'id': self.schema.datatype_cenitID
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

    def _calculate_update(self, values):
        update = {}
        for k, v in values.items():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0]['id'],

                }
                if v[0].get('event', False):
                    _logger.info("\n\nCalculating FLOW update from: %s\n", v[0])
                    #~ update.update({
                        #~ 'event': v[0]['event']['id']
                    #~ })

        return update

    @api.onchange('webhook')
    def on_webhook_changed(self):
        return {
            'value': {
                'connection_role': ""
            },
            "domain": {
                "connection_role": [
                    ('webhooks', 'in', self.webhook.id)
                ]
            }
        }

    @api.onchange('schema')
    def on_schema_changed(self):
        return {
            'value': {
                'data_type': "",
                'event': "",
            },
            "domain": {
                "data_type": [
                    ('schema', '=', self.schema.id)
                ],
                'event': [
                    ('schema', '=', self.schema.id)
                ],
            }
        }

    @api.onchange('schema', 'webhook')
    def _on_schema_or_hook_changed(self):
        return {
            'value': {
                'cenit_translator': "",
            },
            'domain': {
                'cenit_translator': [
                    ('schema', 'in', (self.schema.id, False)),
                    ('type_', '=', {
                            'get': 'Import',
                        }.get(self.webhook.method, 'Export')
                    )
                ]
            }
        }

    @api.one
    def _get_direction (self):
        my_url = self.env['ir.config_parameter'].get_param(
            'web.base.url', default=''
        )

        conn = self.connection_role.connections and \
            self.connection_role.connections[0]
        my_conn = conn.url == my_url

        return {
            ('get', True): 'send',
            ('put', False): 'send',
            ('post', False): 'send',
            ('delete', False): 'send',
        }.get((self.webhook.method, my_conn), 'receive')

    @api.model
    def create(self, vals):
        local = vals.get('cenitID', False) == False
        obj_id = super(CenitFlow, self).create(vals)
        obj = self.browse(obj_id)

        if not local:
            purpose = obj._get_direction()[0]

            method = 'set_%s_execution' % (purpose, )
            getattr(obj, method)()

        return obj_id

    @api.one
    def write(self, vals):
        prev_purpose = self._get_direction()[0]
        prev_dt = self.data_type
        res = super(CenitFlow, self).write(vals)
        new_purpose = self._get_direction()[0]

        if ((new_purpose != prev_purpose) or \
             (vals.get('event', False)) or \
             (prev_dt != self.data_type)):

            method = 'set_%s_execution' % new_purpose
            getattr(self, method)()

        return res

    @api.one
    def unlink(self):

        if self.base_action_rules:
            self.base_action_rules.unlink()
        if self.cron:
            self.cron.unlink()

        return super(CenitFlow, self).unlink()

    @api.model
    def find(self, model, purpose):
        domain = [('data_type.cenit_root', '=', model)]
        objs = self.search(domain)

        return objs and objs[0] or False

    @api.one
    def set_receive_execution(self):
        pass

    @api.model
    def receive(self, model, data):
        res = False
        context = self.env.context.copy() or {}
        obj = self.find(model.lower(), 'receive')

        if obj:
            klass = self.env[obj.data_type.model.model]

            if obj.format_ == 'application/json':
                action = context.get('action', 'push')
                wh = self.env['cenit.handler']
                context.update({'receive_object': True})

                action = getattr(wh, action, False)
                if action:
                    root = obj.data_type.cenit_root
                    res = action (data, root)

            elif obj.format_ == 'application/EDI-X12':
                for edi_document in data:
                    klass.edi_import(edi_document)
                res = True
        return res

    @api.one
    def set_send_execution(self):
        if self.data_type:
            dts = [self.data_type]
        else:
            dt_pool = self.env['cenit.data_type']
            domain = [('schema', '=', self.schema.id)]
            dts = dt_pool.search(domain)

        execution = {
            'only_manual': 'only_manual',
            'interval': 'interval',
            'on_create': 'on_create',
            'on_write': 'on_write'
        }.get(self.event.type_, 'on_create_or_write')

        for data_type in dts:
            if execution == 'only_manual':

                if self.base_action_rules:
                    self.base_action_rules.unlink()

                elif self.cron:
                    self.cron.unlink()

            if execution == 'interval':
                ic_obj = self.env['ir.cron']

                if self.cron:
                    _logger.info ("\n\nCronID\n")

                else:
                    vals_ic = {
                        'name': 'push_%s' % data_type.model.model,
                        'interval_number': 10,
                        'interval_type': 'minutes',
                        'numbercall': -1,
                        'model': 'cenit.flow',
                        'function': 'send_all',
                        'args': '(%s)' % str(self.id)
                    }
                    ic = ic_obj.create(vals_ic)
                    self.write({'cron': ic.id})

                    if self.base_action_rules:
                        self.base_action_rules.unlink()

            elif execution in ('on_create', 'on_write', 'on_create_or_write'):
                ias_obj = self.env['ir.actions.server']
                bar_obj = self.env['base.action.rule']

                if self.base_action_rules:
                    self.base_action_rules.unlink()

                cd = "self.pool.get('cenit.flow').send(cr, uid, obj, %s)"\
                    % (self.id,)
                vals_ias = {
                    'name': 'push_%s' % data_type.model.model,
                    'model_id': data_type.model.id,
                    'state': 'code',
                    'code': cd
                }
                ias = ias_obj.create(vals_ias)
                vals_bar = {
                    'name': 'push_%s' % data_type.model.model,
                    'active': True,
                    'kind': execution,
                    'model_id': data_type.model.id,
                    'server_action_ids': [(6, 0, [ias.id])]
                }
                bar = bar_obj.create(vals_bar)
                self.write({'base_action_rules': bar.id})

                if self.cron:
                    self.cron.unlink()

        return True

    @api.model
    def send(self, obj, flow_id):
        flow = self.browse(flow_id)
        if flow:
            data = None
            if flow.format_ == 'application/json':
                ws = self.env['cenit.serializer']
                data = [ws.serialize(obj, flow.data_type)]
            elif flow.format_ == 'application/EDI-X12':
                data = self.env[obj._name].edi_export([obj])
            return flow._send(data)
        return False

    @api.model
    def send_all(self, id_):
        flow = self.browse(id_)
        mo = self.env[flow.data_type.model.model]
        if mo:
            data = []
            objs = mo.search([])
            if flow.format_ == 'application/json':
                ws = self.env['cenit.serializer']
                for x in objs:
                    data.append(ws.serialize(x, flow.data_type))
            elif flow.format_ == 'application/EDI-X12' and \
                 hasattr(mo, 'edi_export'):
                data = mo.edi_export(objs)
            if data:
                return flow._send(data)
        return False

    @api.one
    def _send(self, data):
        method = "http_post"
#         if local:
#             method = "local_http"
        return getattr(self, method)(data)

    @api.one
    def http_post(self, data):
        path = "/api/v1/push"

        root = self.data_type.cenit_root
        if isinstance(root, list):
            root = root[0]
        values = {root: data}

        rc = False
        try:
            rc = self.post(path, values)
        except Warning as e:
            _logger.exception(e)

        return rc

#     def local_post(self, cr, uid, obj, data, context=None):
#         db = context.get('partner_db')
#         if db:
#             registry = openerp.modules.registry.RegistryManager.get(db)
#             with registry.cursor() as rcr:
#                 uids = registry['res.users'].search(rcr, SI,
#                                                 [('oauth_uid', '!=', False)])
#                 ruid = uids and uids[0] or SI
#                 model = obj.root.lower()
#                 return registry['cenit.flow'].receive(rcr, ruid, model, data)
