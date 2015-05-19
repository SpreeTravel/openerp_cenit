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

    def _calculate_update (self, values):
        update = {}
        for k,v in values.items ():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0] ['id'],
                    'datatype_cenitID': v[0] ['data_types'] [0] ['id'],
                    #~ 'cenit_root': self.name,
                }

        return update

    def __add_lines (self, cr, uid, lines, context=None):
        line_pool = self.pool.get ('cenit.data_type.line')

        for entry in lines:
            line = line_pool.create (
                cr, uid, entry, context=context
            )

    @api.model
    def __match_linetype (self, field):
        rc = {}
        if field.ttype not in (u"many2one", u"many2many", u"one2many"):
            rc.update ({"line_type": "field"})
        else:
            domain = [('model', '=', field.relation)]
            candidates = self.search (domain)

            if candidates:
                rc.update ({
                    "line_type": "model",
                    "reference": candidates[0],
                    "line_cardinality": "2%s" % (field.ttype.split ("2") [1])
                })
            else:
                rc.update ({"line_type": "reference"})

        return rc

    def __match_schematype (self, line_type):
        return {
            u"datetime": {"type": "string", "format": "date-time"},
            u"float": {"type": "number"},
            u"integer": {"type": "integer"},
            u"boolean": {"type": "boolean"},
        }.get (line_type, {"type": "string"})

    @api.one
    def _get_dt_cenitID (self):
        path = "/api/v1/data_type"

        rc = self.get (path)

        for item in rc:
            if (item['setup::datatype']['schema']['uri'] == "%s.json" % (
                    self.name,
                )) and \
               (item['setup::datatype']['schema']['library']['name'] == \
                    self.library.name
                ):
                vals = {
                    'datatype_cenitID': item['setup::datatype']['id'],
                    'cenit_root': item['setup::datatype']['name']
                }
                self.with_context (noPush=True).write (vals)
                return

    @api.one
    def _update_schema_properties (self, values):
        schema = simplejson.loads (self.schema)

        schema ['properties'].clear ()
        schema ['properties'].update (values)

        return simplejson.dumps (schema)

    def _guess_value_from_name (self, name):
        if name.endswith ("_id"):
            return name [:-3]
        return name

    @api.model
    def create (self, vals):
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

            model_pool = self.env ['ir.model']
            model = model_pool.browse (vals['model'])

            if vals.get ('lines', False):
                for _,__,line in vals['lines']:
                    if _ == 0:
                        candidates = [
                            x.name for x in model.field_id if x.name == line [
                                'name'
                            ]
                        ]

                        if not candidates:
                            vals['lines'].remove ([_,__,line])

            for f in model.field_id:
                if (f.name not in odoo_fields):

                    values = {
                        'name': f.name,
                        'value': self._guess_value_from_name (f.name)
                    }

                    values.update (self.__match_linetype(f))
                    flag = -1
                    pos = 0
                    if vals.get ('lines', False):
                        for line in vals['lines']:
                            if line[2]['name'] == values['name']:
                                flag = pos
                                break
                            else:
                                pos += 1

                    if vals.get ('lines', False) and (flag < 0):
                        continue

                    if values ['line_type'] == "field":
                        schema['properties'].update ({
                            f.value: self.__match_schematype (f.ttype)
                        })
                    elif values ['line_type'] == "reference":
                        try:
                            name = getattr(getattr(model, field.name), 'name')
                            schema['properties'].update ({
                                f.value: self.__match_schematype ("string")
                            })
                        except:
                            continue

                    elif values ['line_type'] == "model":
                        data = {}
                        ref = values.pop ("reference")
                        values.update ({"reference": ref.id})
                        if values['line_cardinality'] == "2many":
                            data.update ({
                                "type": "array",
                                "items": {
                                    "$ref": "%s.json" %(ref.name)
                                }
                            })
                        else:
                            data.update ({
                                "$ref": "%s.json" %(ref.name)
                            })
                        schema['properties'].update ({
                            f.value: data
                        })
                    else:
                        schema['properties'].update ({
                            f.name: self.__match_schematype ("string")
                        })

                    if not vals.get ('lines', False):
                        lines.append (values)
                    else:
                        if not vals['lines'][flag][2].get ('value', False):
                            vals['lines'][flag][2].update ({
                                'value': values.get ('value', False)
                            })
                        if not vals['lines'][flag][2].get ('line_type', False):
                            vals['lines'][flag][2].update ({
                                'line_type': values.get ('line_type', False)
                            })
                        if not vals['lines'][flag][2].get ('reference', False):
                            vals['lines'][flag][2].update ({
                                'reference': values.get ('reference', False)
                            })
                        if not vals['lines'][flag][2].get (
                            'line_cardinality', False
                        ):
                            vals['lines'][flag][2].update ({
                                'line_cardinality': values.get (
                                    'line_cardinality', False
                                )
                            })

            vals.update ({'schema': simplejson.dumps (schema)})

            val_lines = []
            for line in lines:
                val_lines.append ([0, False, line])

            if not vals.get ('lines'):
                vals.update ({'lines': val_lines})
            else:
                vals['lines'].extend (val_lines)

        vals ['cenit_root'] = vals ['name']
        _id = super (CenitDataType, self).create (vals)

        return _id

    @api.one
    def write (self, vals):
        model_pool = self.env ['ir.model']
        model = model_pool.browse (self.model.id)
        if vals.get ('lines') and not vals.get("schema", False):
            new_lines = [
                y for y in vals['lines'] if y[0] == 0
            ]

            mod_lines = [
                x.name for x in self.lines if x.id in [
                    y[1] for y in vals ['lines'] if y[0] == 1
                ]
            ]
            existent_lines = [
                x.name for x in self.lines if x.id in [
                    y[1] for y in vals ['lines'] if y[0] == 4
                ]
            ]

            properties = simplejson.loads (self.schema) ['properties'].copy ()
            values = {}

            for _,__,line in new_lines:
                candidates = [
                    x for x in model.field_id if x.name == line['name']
                ]

                if candidates:
                    f = candidates [0]
                    defaults = self.__match_linetype(f)

                    if not line.get ('value', False):
                        line.update ({
                            'value': self._guess_value_from_name (
                                line.get ('name')
                            )
                        })
                    if not line.get ('line_type', False):
                        line.update ({'line_type': defaults.get ('line_type')})
                    if line.get ('line_type', False) == 'model':
                        if not line.get ('reference', False):
                            if defaults.get ('reference', False):
                                line.update ({
                                    'reference': defaults.get ('reference').id
                                })
                        if not line.get ('line_cardinality', False):
                            line.update ({
                                'line_cardinality': defaults.get (
                                    'line_cardinality', False
                                )
                            })

                    if line ['line_type'] == 'field':
                        if f:
                            values.update ({
                                line ['value']: self.__match_schematype (
                                    f.ttype
                                )
                            })
                        else:
                            values.update ({
                                line ['value']: self.__match_schematype (
                                    "string"
                                )
                            })
                    elif line ['line_type'] == 'reference':
                        values.update ({
                            line ['value']: self.__match_schematype ("string")
                        })
                    elif line ['line_type'] == 'model':
                        data = {}
                        ref = self.browse (line.get ("reference"))
                        if line.get ('line_cardinality', False) == "2many":
                            data.update ({
                                "type": "array",
                                "items": {
                                    "$ref": "%s.json" %(ref.name)
                                }
                            })
                        else:
                            data.update ({
                                "$ref": "%s.json" %(ref.name)
                            })
                        values.update ({
                            line ['value']: data
                        })
                    else:
                        values.update ({
                            line ['name']: self.__match_schematype ("string")
                        })
                else:
                    vals['lines'].remove ([_,__,line])

            for f in model.field_id:
                if f.name in existent_lines:
                    line = [ x for x in self.lines if x.name == f.name ] [0]

                    sch = properties.get (line.value, False)

                    if sch:
                        values.update ({
                            line.value: sch
                        })

                elif f.name in mod_lines:
                    line = [ x for x in self.lines if x.name == f.name ] [0]
                    v = [ x[2] for x in vals['lines'] if x[1] == line.id ] [0]

                    if not v.get ('line_type', 'NULL'):
                        defaults = self.__match_linetype (f)
                        v.update (defaults)
                    flag, pos = -1, 0
                    for l in vals['lines']:
                        if l[1] == line.id:
                            flag = pos
                            break
                        pos += 1


                    line_type = v.get ('line_type', False) or line.line_type
                    line_value = v.get ('value', False) or line.value
                    line_name = v.get ('name', False) or line.name
                    line_reference = v.get ('reference', False) or line.reference
                    line_cardinality = v.get ('line_cardinality', False) or \
                        line.line_cardinality

                    if line_type == "field":
                        values.update ({
                            line_value: self.__match_schematype (f.ttype)
                        })
                        v.update ({
                            'reference': False,
                            'line_cardinality': False,
                        })
                    elif line_type == "reference":
                        values.update ({
                            line_value : self.__match_schematype ("string")
                        })
                        v.update ({
                            'reference': False,
                            'line_cardinality': False,
                        })
                    elif line_type == 'model':
                        ref = line_reference
                        v.update ({'reference': line_reference.id})

                        if line_cardinality == '2many':
                            values.update ({
                                line_value: {
                                    "type": "array",
                                    "items": {
                                        "$ref": "%s.json" %(ref.name)
                                    }
                                }
                            })
                        else:
                            values.update ({
                                line_value: {
                                    "$ref": "%s.json" %(ref.name)
                                }
                            })
                    else:
                        values.update ({
                            line_name : self.__match_schematype ("string")
                        })
                        v.update ({
                            'reference': False,
                            'line_cardinality': False,
                        })
                    vals ['lines'][flag][2] = v

            schema = self._update_schema_properties (values)
            vals.update ({"schema": schema[0]})


        res = super (CenitDataType, self).write (vals)

        return res



class CenitDataTypeLine(models.Model):
    _name = 'cenit.data_type.line'

    name = fields.Char('Name', required=True)
    data_type = fields.Many2one('cenit.data_type', 'Data Type')

    line_type = fields.Selection(
        [
            ('field', 'Field'),
            ('model', 'Model'),
            ('default', 'Default'),
            ('reference', 'Reference')
        ],
        'Type'
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
