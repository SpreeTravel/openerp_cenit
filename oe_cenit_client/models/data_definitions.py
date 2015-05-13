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

import logging
import simplejson


from openerp import models, fields, api
from openerp.addons.oe_cenit_client import cenit_api


_logger = logging.getLogger(__name__)


#~ class CenitSchema (cenit_api.CenitApi, models.Model):
    #~ _name = 'cenit.schema'
    #~ cenit_model = 'schema'
    #~ cenit_models = 'schemas'
#~ 
    #~ cenitID = fields.Char ('Cenit ID')
#~ 
    #~ name = fields.Char (compute='_compute_name')
    #~ 
    #~ uri = fields.Char ('URI', required=True)
    #~ schema = fields.Text ('Schema', required=True)
#~ 
    #~ _sql_constraints = [
        #~ ('lib_uri_uniq', 'UNIQUE(library, uri)', 'The Library|uri combo must be unique!'),
    #~ ]
#~ 
#~ 
    #~ @api.one
    #~ def _compute_name (self):
        #~ self.name = "%s | %s" %(self.library.name, self.uri)
#~ 
    #~ def _get_values (self):
        #~ vals = {
            #~ 'uri': self.uri,
            #~ 'schema': self.schema,
            #~ 'library': {
                #~ "id": self.library.cenitID
            #~ }
        #~ }
        #~ if self.cenitID:
            #~ vals.update ({'id': self.cenitID})
#~ 
        #~ return vals


class CenitLibrary (cenit_api.CenitApi, models.Model):
    _name = 'cenit.library'
    cenit_model = 'library'
    cenit_models = 'libraries'

    cenitID = fields.Char ('Cenit ID')
    
    name = fields.Char ('Name', required=True)

    data_types = fields.One2many (
        'cenit.data_type',
        'library',
        string = 'Data Types'
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

        return vals


# TODO: Assumptions
#       1. The relation with Schema will be One2One
class CenitDataType (cenit_api.CenitApi, models.Model):
    _name = 'cenit.data_type'
    cenit_model = 'schema'
    cenit_models = 'schemas'

    cenitID = fields.Char ('Cenit ID')
    datatype_cenitID = fields.Char ('Cenit ID')
    cenit_root = fields.Char ('Cenit Root')

    name = fields.Char ('Name', size=128, required=True)
    library = fields.Many2one (
        'cenit.library',
        string = 'Library',
        required = True,
        ondelete = 'cascade'
    )

    model = fields.Many2one ('ir.model', 'Model', required=True)
    schema = fields.Text ('Schema')
    
    lines = fields.One2many ('cenit.data_type.line', 'data_type', 'Mapping')

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
    ]

    
    def _get_values (self):
        vals = {
            'uri': "%s.json" %(self.name,),
            'schema': self.schema,
            'library': {
                "id": self.library.cenitID
            }
        }
        if self.cenitID:
            vals.update ({'id': self.cenitID})

        return vals
    
    def __add_lines (self, cr, uid, lines, context=None):
        line_pool = self.pool.get ('cenit.data_type.line')

        for entry in lines:
            line = line_pool.create (
                cr, uid, entry, context=context
            )
            _logger.info ("\n\nAdding line %s with values: %s\n", line, entry)

    def __match_linetype (self, line_type):
        return {
            u"": None
        }.get (line_type, "field")

    #~ def __match_schematype (self, line_type):
        #~ return {
            #~ u"": None
        #~ }.get (line_type, "string")

    def __get_dt_cenitID (self, cr, uid, obj, context=None):
        path = "/api/v1/data_type"

        rc = self.get (cr, uid, path, context=context)

        if not isinstance (context, dict):
            context = {}
        context.update ({'noPush': True})

        for item in rc:
            if item['schema_id']['id'] == obj.cenitID:
                _logger.info ('\n\n\nDATATYPE: %s\n', item)
                vals = {
                    'datatype_cenitID': item['id'],
                    'cenit_root': item['name']
                }
                self.write (cr, uid, obj.id, vals, context=context)
                return
                

    def create (self, cr, uid, vals, context=None):
        _logger.info ("\n\nCreating DataType with values %s\n", vals)
        
        schema = vals.get ('schema', False)
        sflag = not schema
        lines = []
        if not schema:
            schema = {
                "name": vals ["name"],
                "type": "object",
                "properties": {},
                #~ "required": ["id",]
            }
            
            odoo_fields = (
                u"create_date",
                u"create_uid",
                u"write_date",
                u"write_uid",
            )
            
            model_pool = self.pool.get ('ir.model')
            model = model_pool.browse (cr, uid, vals['model'], context=context)
            for f in model.field_id:
                if (f.name not in odoo_fields):
                    _logger.info ("\n\nField: [%s, %s, %s, %s -> %s]\n",
                        f.name, f.ttype, f.required, f.relation, f.relation_field
                    )
                    values = {
                        #'data_type': _id,
                        'name': f.name,
                        'value': f.name,
                        'line_type': self.__match_linetype (f.ttype),
                        # 'required': f.required,
                        # 'relation': f.relation,
                        # 'relation_field': f.relation_field,
                    }
                    flag = -1
                    pos = 0
                    if vals.get ('lines', False):
                        for line in vals['lines']:
                            if line[2]['name'] == values['name']:
                                flag = pos
                                continue
                            else:
                                pos += 1
                                
                    if vals.get ('lines', False) and (flag < 0):
                        continue

                    if not vals.get ('lines', False):
                        lines.append (values)
                    else:
                        _logger.info ("\n\nLINES: %s\n",vals['lines'])
                        vals['lines'][flag][2].update (values)
                    
                    if values ['line_type'] == "field":
                        schema['properties'].update ({
                            f.name: {
                                "type": "string"
                            }
                        })

                    #~ if f.required:
                        #~ schema['required'].append (f.name)
        
            vals.update ({'schema': simplejson.dumps (schema)})
            
        _id = super (CenitDataType, self).create (
            cr, uid, vals, context=context
        )

        for line in lines:
            line.update ({'data_type': _id})

        obj = self.browse (cr, uid, _id, context=context)
        self.__add_lines (cr, uid, lines, context=context)
        
        if obj.cenitID:
            self.__get_dt_cenitID (cr, uid, obj, context=context)

        return _id


class CenitDataTypeLine(models.Model):
    _name = 'cenit.data_type.line'

    name = fields.Char('Name')
    data_type = fields.Many2one('cenit.data_type', 'Data Type')

    line_type = fields.Selection(
        [
            ('field', 'Field'),
            ('function', 'Function'),
            ('model', 'Model'),
            ('default', 'Default'),
            ('reference', 'Reference')
        ],
        'Type',
        default='field'
    )
    reference = fields.Many2one('cenit.data_type', 'Reference')
    line_cardinality = fields.Selection(
        [
            ('2many', '2many'),
            ('2one', '2one')
        ],
        'Cardinality'
    )
    value = fields.Char('Value')
    primary = fields.Boolean('Primary')


