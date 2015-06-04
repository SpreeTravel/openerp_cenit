#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  collections.py
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


_logger = logging.getLogger(__name__)


class CenitCollection(models.Model):

    @api.model
    def _update_collection_list(self):
        param_pool = self.env['cenit.collection.parameter']
        path = "/api/v1/shared_collection"
        api = cenit_api.CenitApi()
        rc = api.get(self.env.cr, self.env.uid, path)

        collections = []
        for entry in rc:
            collection = entry.get('shared_collection')
            data = {
                'sharedID': collection.get('id'),
                'name': collection.get('name'),
                'description': collection.get('description'),
            }

            domain = [('sharedID','=',data.get('sharedID'))]
            candidates = self.search(domain)

            if not candidates:
                coll = self.create(data)
            else:
                coll = candidates[0]
                coll.write(data)


            params = collection.get('pull_parameters', [])
            param_list = []
            strict_keys = []

            for param in params:
                param_data = {
                    'cenitID': param.get('id'),
                    'name': param.get('label')
                }
                domain = [('cenitID', '=', param_data.get('cenitID'))]
                candidates = param_pool.search(domain)

                if not candidates:
                    param_list.append([0, False, param_data])
                else:
                    p = candidates[0]
                    param_list.append([1, p.id, param_data])

                strict_keys.append(param_data.get('name'))

            domain = [
                ('name', 'not in', strict_keys),
                ('collection', '=', coll.id)
            ]
            candidates = param_pool.search(domain)
            for candidate in candidates:
                param_list.append([2, candidate.id, False])

            rc = coll.write({'parameters': param_list})

        return {
            "type": "ir.actions.act_window",
            "res_model": "cenit.collection",
            "view_type": "form",
            "view_mode": "tree,form",
        }

    @api.one
    def _install_libraries(self, values):
        library_pool = self.env['cenit.library']
        schema_pool = self.env['cenit.schema']

        for library in values:
            schemas = library.get('schemas', [])
            lib_data = {
                'cenitID': library.get('id'),
                'name': library.get('name'),
            }

            domain = [('name', '=', lib_data.get('name'))]
            candidates = library_pool.search(domain)

            if not candidates:
                lib = library_pool.with_context(local=True).create(lib_data)
            else:
                lib = candidates[0]
                lib.with_context(local=True).write(lib_data)

            for schema in schemas:
                cenitID = schema.get('id')
                sch_data = {
                    'uri': schema.get('uri'),
                    'schema': schema.get('schema'),
                    'library': lib.id
                }

                domain = [
                    ('library', '=', sch_data.get('library')),
                    ('uri', '=', sch_data.get('uri')),
                ]
                candidates = schema_pool.search(domain)

                if not candidates:
                    sch = schema_pool.with_context(local=True).create(sch_data)
                else:
                    sch = candidates[0]
                    sch.with_context(local=True).write(sch_data)

    @api.one
    def _get_param_lines(self, ref_id, values, prefix):
        parameter_pool = self.env['cenit.parameter']

        url = []
        header = []
        template = []

        params = {
            'parameters': url,
            'headers': header,
            'template_parameters': template,
        }

        fields = {
            'parameters': '%s_url_id' %(prefix,),
            'headers': '%s_header_id' %(prefix,),
            'template_parameters': '%s_template_id' %(prefix,),
        }

        for key in ('parameters', 'headers', 'template_parameters'):
            vals = values.get(key, [])
            field = fields.get(key)
            param = params.get(key)

            strict_keys = []

            for entry in vals:
                if not entry.get('key'):
                    continue

                domain = [
                    ('key', '=', entry.get('key')),
                    (field, '=', ref_id),
                ]
                candidates = parameter_pool.search(domain)

                param_data = {
                    'key': entry.get('key'),
                    'value': entry.get('value')
                }

                if not candidates:
                    param.append([0, False, param_data])
                else:
                    p = candidates[0]
                    param.append([1, p.id, param_data])

                strict_keys.append(param_data.get('key'))

            domain = [
                ('key', 'not in', strict_keys),
                (field, '=', ref_id),
            ]

            left_overs = parameter_pool.search(domain)
            for entry in left_overs:
                param.append([2, entry.id, False])

        rc = {
            'url_parameters': params.get('parameters'),
            'header_parameters': params.get('headers'),
            'template_parameters': params.get('template_parameters'),
        }

        return rc

    @api.one
    def _install_connections(self, values):
        connection_pool = self.env['cenit.connection']

        for connection in values:
            conn_data = {
                'cenitID': connection.get('id'),
                'name': connection.get('name'),
                'url': connection.get('url'),
                'key': connection.get('number'),
                'token': connection.get('token'),
            }

            domain = [('name', '=', conn_data.get('name'))]
            candidates = connection_pool.search(domain)

            if not candidates:
                conn_id = connection_pool.with_context(local=True).create(
                    conn_data
                )
                conn = connection_pool.browse(conn_id)
            else:
                conn = candidates[0]
                conn.with_context(local=True).write(conn_data)

            conn_params = self._get_param_lines(conn.id, connection, "conn")[0]
            conn.with_context(local=True).write(conn_params)

    @api.one
    def _install_webhooks(self, values):
        webhook_pool = self.env['cenit.webhook']

        for webhook in values:
            hook_data = {
                'cenitID': webhook.get('id'),
                'name': webhook.get('name'),
                'path': webhook.get('path'),
                'method': webhook.get('method'),
                'purpose': webhook.get('purpose'),
            }

            domain = [('name', '=', hook_data.get('name'))]
            candidates = webhook_pool.search(domain)

            if not candidates:
                hook_id = webhook_pool.with_context(local=True).create(
                    hook_data
                )
                hook = webhook_pool.browse(hook_id)
            else:
                hook = candidates[0]
                hook.with_context(local=True).write(hook_data)

            hook_params = self._get_param_lines(hook.id, webhook, "hook")[0]
            hook.with_context(local=True).write(hook_params)

    @api.one
    def _install_connection_roles(self, values):
        role_pool = self.env['cenit.connection.role']
        conn_pool = self.env['cenit.connection']
        hook_pool = self.env['cenit.webhook']

        for role in values:
            role_data = {
                'cenitID': role.get('id'),
                'name': role.get('name'),
            }

            domain = [('name', '=', role_data.get('name'))]
            candidates = role_pool.search(domain)

            if not candidates:
                role_id = role_pool.with_context(local=True).create(
                    role_data
                )
                crole = role_pool.browse(role_id)
            else:
                crole = candidates[0]
                crole.with_context(local=True).write(role_data)

            connections = []
            webhooks = []

            for connection in role.get('connections', []):
                domain = [('name', '=', connection.get('name'))]
                candidates = conn_pool.search(domain)

                if candidates:
                    conn = candidates[0]
                    connections.append(conn.id)

            for webhook in role.get('webhooks', []):
                domain = [('name', '=', webhook.get('name'))]
                candidates = hook_pool.search(domain)

                if candidates:
                    hook = candidates[0]
                    webhooks.append(hook.id)

            role_members = {
                'connections': [(6, False, connections)],
                'webhooks': [(6, False, webhooks)],
            }
            crole.with_context(local=True).write(role_members)

    @api.one
    def _install_flows(self, values, events, translators):
        flow_pool = self.env['cenit.flow']
        lib_pool = self.env['cenit.library']
        sch_pool = self.env['cenit.schema']
        hook_pool = self.env['cenit.webhook']
        role_pool = self.env['cenit.connection.role']

        for flow in values:
            flow_data = {
                'cenitID': flow.get('id'),
                'name': flow.get('name'),
            }
            for event in events:
                if event[1] == flow.get('event', {}).get('name', False):
                    flow_data.update({
                        'execution': event[0]
                    })
            for trans in translators:
                if trans[1] == flow.get('translator', {}).get('name', False):
                    flow_data.update({
                        'cenit_translator': trans[0],
                        'format_': trans[2]
                    })
            types = dict(
                flow_pool.fields_get(
                    allfields=['format_']
                )['format_']['selection']
            ).keys()

            if flow_data['format_'] not in types:
                continue

            dt = flow.get('custom_data_type', {})
            schema = dt.get('schema', {})
            library = schema.get('library', {})

            domain = [('name', '=', library.get('name', ''))]
            rc = lib_pool.search(domain)
            if not rc:
                continue

            domain = [
                ('uri', '=', schema.get('uri', '')),
                ('library', '=', rc[0].id)
            ]
            rc = sch_pool.search(domain)
            if not rc:
                continue
            flow_data.update({
                'schema': rc[0].id
            })

            hook = flow.get('webhook', {})
            domain = [('name', '=', hook.get('name', ''))]
            rc = hook_pool.search(domain)
            if not rc:
                continue
            flow_data.update({
                'webhook': rc[0].id
            })

            role = flow.get('connection_role', {})
            domain = [('name', '=', role.get('name', ''))]
            rc = role_pool.search(domain)
            if rc:
                flow_data.update({
                    'connection_role': rc[0].id
                })

            domain = [('name', '=', flow_data.get('name'))]
            candidates = flow_pool.search(domain)

            if not candidates:
                flow_id = flow_pool.with_context(local=True).create(
                    flow_data
                )
                flow = flow_pool.browse(flow_id)
            else:
                flow = candidates[0]
                flow.with_context(local=True).write(flow_data)

    @api.one
    def _parse_refs(self, values):
        rc = []
        for ref in values:
            rc.append((
                ref.get('id'),
                ref.get('name'),
                ref.get('mime_type'))
            )

        return rc

    @api.one
    def _install_dummy(self, values):
        pass

    @api.one
    def install_collection(self):
        api = cenit_api.CenitApi()

        path = "/api/v1/shared_collection/%s/pull" % (self.sharedID,)
        data = {
            'pull_parameters': dict(
                (param.cenitID,param.value) for param in self.parameters
            )
        }
        rc = api.post(self.env.cr, self.env.uid, path, data)

        path = "/api/v1/collection"
        rc = api.get(self.env.cr, self.env.uid, path)

        data = {}
        for entry in rc:
            collection = entry.get('collection', {})
            if collection.get('name', False) == self.name:
                data = collection
                break

        events = self._parse_refs(data.get('events', []))[0]
        translators = self._parse_refs(data.get('translators', []))[0]

        keys = (
            'libraries', 'connections', 'webhooks', 'connection_roles'
        )

        for key in keys:
            values = data.get(key, {})
            {
                'connections':      self._install_connections,
                'connection_roles': self._install_connection_roles,
                'libraries':        self._install_libraries,
                'webhooks':         self._install_webhooks,
            }.get(key, self._install_dummy)(values)

        if data.get('flows', False):
            self._install_flows(data.get('flows'), events, translators)

        return True

    _name = "cenit.collection"

    cenitID = fields.Char('CenitID')
    sharedID = fields.Char('SharedID')
    name = fields.Char('Name')
    description = fields.Text('Description')
    #~ image = fields.Binary('Image')

    parameters = fields.One2many(
        'cenit.collection.parameter',
        'collection',
        string = 'Pull Parameters'
    )


class CenitCollectionPullParameter(models.Model):
    _name = "cenit.collection.parameter"

    cenitID = fields.Char('CenitID')
    name = fields.Char('Name')
    value = fields.Char('Value')

    collection = fields.Many2one(
        'cenit.collection',
        string="Collection",
        ondelete="cascade",
        required=True
    )
