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

from openerp import models, fields
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
        'cenit.connection.parameter',
        'url_id',
        string = 'Parameters'
    )
    header_parameters = fields.One2many (
        'cenit.connection.parameter',
        'header_id',
        string = 'Header Parameters'
    )
    template_parameters = fields.One2many (
        'cenit.connection.parameter',
        'template_id',
        string = 'Template Parameters'
    )

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
            
        _logger.info ("\n\nReturning values: %s\n", vals)
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

    def _get_values (self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update ({'id': self.cenitID})

        connections = []
        for conn in self.connections:
            connections.append (conn._get_values ())

        vals.update ({
            'connections': connections
        })
        return vals


class CenitConnectionParameter (models.Model):
    _name = 'cenit.connection.parameter'

    key = fields.Char ('Key', required=True)
    value = fields.Char ('Value', required=True)

    url_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )
    
    header_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )
    
    template_id = fields.Many2one (
        'cenit.connection',
        string = 'Connection'
    )


class CenitFlow (cenit_api.CenitApi, models.Model):
    _name = "cenit.flow"

    cenit_model = 'flow'
    cenit_models = 'flows'

    cenitID = fields.Char ('Cenit ID')

    name = fields.Char ('Name', size=64, required=True)
    root = fields.Char ('Root', size=64, required=True)
    data_type = fields.Many2one (
        'cenit.data_type', 'Data type', required=True
    )
    purpose = fields.Selection (
        [
            ('send', 'Send'),
            ('receive', 'Receive')
        ],
        'Purpose', default='send', required=True
    )
    execution = fields.Selection (
        [
            ('only_manual', 'Only Manual'),
            ('interval', 'Interval'),
            ('on_create', 'On Create'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Create & Update')
        ],
        'Execution', default='only_manual'
    )
    _format = fields.Selection (
        [
            ('json', 'JSON'),
            ('edi', 'EDI')
        ],
        'Format', default='json'
    )
    method = fields.Selection (
        [
            ('http_post', 'HTTP POST'),
            ('local_post', 'LOCAL POST'),
            ('file_post', 'FILE POST')
        ], 'Method', default='http_post'
    )

    base_action_rule = fields.Many2one (
        'base.action.rule', 'Action Rule'
    )
    ir_cron = fields.Many2one (
        'ir.cron', 'Action Cron'
    )

