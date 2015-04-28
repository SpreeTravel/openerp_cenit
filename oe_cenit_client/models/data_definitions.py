#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  data_definitions.py
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

from openerp import models, fields
from openerp.addons.oe_cenit_client import cenit_api



class CenitSchema (cenit_api.CenitApi, models.Model):
    _name = 'cenit.schema'
    cenit_model = 'schema'
    cenit_models = 'schemas'

    cenitID = fields.Char ('Cenit ID')

    name = fields.Char (compute='_compute_name')
    
    library = fields.Many2one (
        'cenit.library',
        string = 'Library',
        required = True,
        ondelete = 'cascade'
    )

    uri = fields.Char ('URI', required=True)
    schema = fields.Text ('Schema', required=True)

    def _compute_name (self):
        self.name = "%s | %s" %(self.library.name, self.uri)

    def _get_values (self):
        vals = {
            'uri': self.uri,
            'schema': self.schema,
            'library': {
                "id": self.library.cenitID
            }
        }
        if self.cenitID:
            vals.update ({'id': self.cenitID})

        return vals


class CenitLibrary (cenit_api.CenitApi, models.Model):
    _name = 'cenit.library'
    cenit_model = 'library'
    cenit_models = 'libraries'

    cenitID = fields.Char ('Cenit ID')
    
    name = fields.Char ('Name', required=True)

    schemas = fields.One2many (
        'cenit.schema',
        'library',
        string = 'Schemas'
    )

    def _get_values (self):
        vals = {
            'name': self.name
        }
        if self.cenitID:
            vals.update ({'id': self.cenitID})

        return vals

