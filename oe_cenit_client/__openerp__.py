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

{
    'name': 'Odoo Cenit Client',
    'version': '0.1',
    'author': 'OpenJAF',
    'website': 'http://www.openjaf.com',
    'category': 'Integration',
    'description': """
        Odoo Cenit Client
    """,
    'depends': ['base', 'base_action_rule'],
    'data': [
        'security/ir.model.access.csv',
        'view/collections.xml',
        'view/config.xml',
        'view/data_definitions.xml',
        'view/setup.xml',
    ],
    'installable': True
}
