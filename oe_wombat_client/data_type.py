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


class WombatDataType(models.Model):
    _name = 'wombat.data.type'

    name = fields.Char('Name', size=128)
    model_id = fields.Many2one('ir.model', 'Model')
    line_ids = fields.One2many('wombat.data.type.line', 'data_type_id',
                               'Lines')


class WombatDataTypeLine(models.Model):
    _name = 'wombat.data.type.line'

    data_type_id = fields.Many2one('wombat.data.type', 'Data Type')
    name = fields.Char('Name')
    line_type = fields.Selection([('field', 'Field'), ('function', 'Function'),
                                  ('model', 'Model'), ('default', 'Default')],
                                 'Type')
    line_cardinality = fields.Selection([('2many', '2many'), ('2one', '2one')],
                                        'Cardinality')
    value = fields.Char('Value')
    primary = fields.Boolean('Primary')
