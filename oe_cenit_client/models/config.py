#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
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
import urllib2
import urlparse

from openerp import models, fields
from openerp.addons.oe_cenit_client import cenit_api
from openerp.addons.web.http import request
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class CenitHubConfig (models.TransientModel, cenit_api.CenitApi):
    _name = 'cenit.hub.settings'
    _inherit = 'res.config.settings'

    cenit_url = fields.Char ('Cenit URL', required=1)
    cenit_user_key = fields.Char ('Cenit User key')
    cenit_user_token = fields.Char ('Cenit User token')
    odoo_endpoint = fields.Many2one ('cenit.connection', string='Odoo endpoint')

    #~ conn_cenitID = fields.Char ('Cenit ID')
    #~ conn_name = fields.Char ('Name', required=1)
    #~ conn_url = fields.Char ('URL', required=1)
    #~ conn_role_id = fields.Many2one ('cenit.connection.role', string='Role')

    ############################################################################
    # Default values getters
    ############################################################################

    def get_default_cenit_url (self, cr, uid, ids, context=None):
        cenit_url = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_url", default=None, context=context
        )
        return {'cenit_url': cenit_url or False}

    def get_default_cenit_user_key (self, cr, uid, ids, context=None):
        cenit_user_key = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_user_key", default=None, context=context
        )
        return {'cenit_user_key': cenit_user_key or False}

    def get_default_cenit_user_token (self, cr, uid, ids, context=None):
        cenit_user_token = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.cenit_user_token", default=None, context=context
        )
        return {'cenit_user_token': cenit_user_token or False}

    def get_default_odoo_endpoint (self, cr, uid, ids, context=None):
        odoo_endpoint = self.pool.get ("ir.config_parameter").get_param (
            cr, uid, "odoo_cenit.odoo_endpoint", default=None, context=context
        )
        if (type(odoo_endpoint) in (unicode, str)) and odoo_endpoint.isdigit ():
            odoo_endpoint = int(odoo_endpoint)
        
        return {'odoo_endpoint': odoo_endpoint or False}
        
    #~ def get_default_conn_cenitID (self, cr, uid, ids, context=None):
        #~ conn_cenitID = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.conn_cenitID", default=None, context=context
        #~ )
        #~ return {'conn_cenitID': conn_cenitID or False}
#~ 
    #~ def get_default_conn_name (self, cr, uid, ids, context=None):
        #~ conn_name = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.conn_name", default=None, context=context)
        #~ if conn_name is None:
            #~ conn_name = "Cenit Odoo"
        #~ return {'conn_name': conn_name or False}
#~ 
    #~ def get_default_conn_url (self, cr, uid, ids, context=None):
        #~ conn_url = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.conn_url", default=None, context=context)
        #~ if conn_url is None:
            #~ conn_url = self.pool.get ("ir.config_parameter").get_param (
                #~ cr, uid, "web.base.url", context=context
            #~ )
        #~ return {'conn_url': conn_url or False}
#~ 
    #~ def get_default_conn_role_id (self, cr, uid, ids, context=None):
        #~ conn_role_id = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.conn_role_id", default=None, context=context
        #~ )
        #~ if (type(conn_role_id) in (unicode, str)) and conn_role_id.isdigit ():
            #~ conn_role_id = int(conn_role_id)
        #~ 
        #~ return {'conn_role_id': conn_role_id or False}

    ############################################################################
    # Values setters
    ############################################################################

    def set_cenit_url (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_url",
                record.cenit_url or '', context=context
            )

    def set_cenit_user_key (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_user_key",
                record.cenit_user_key or '', context=context
            )

    def set_cenit_user_token (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.cenit_user_token",
                record.cenit_user_token or '', context=context
            )

    def set_odoo_endpoint (self, cr, uid, ids, context=None):
        config_parameters = self.pool.get ("ir.config_parameter")
        for record in self.browse (cr, uid, ids, context=context):
            config_parameters.set_param (
                cr, uid, "odoo_cenit.odoo_endpoint",
                record.odoo_endpoint.id or '', context=context
            )
            
    #~ def set_conn_name (self, cr, uid, ids, context=None):
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ for record in self.browse (cr, uid, ids, context=context):
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.conn_name",
                #~ record.conn_name or '', context=context
            #~ )
#~ 
    #~ def set_conn_url (self, cr, uid, ids, context=None):
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ for record in self.browse (cr, uid, ids, context=context):
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.conn_url",
                #~ record.conn_url or '', context=context
            #~ )
#~ 
    #~ def set_conn_role_id (self, cr, uid, ids, context=None):
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ for record in self.browse (cr, uid, ids, context=context):
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.conn_role_id",
                #~ record.conn_role_id.id or '', context=context
            #~ )

    #~ ############################################################################
    #~ # Other methods
    #~ ############################################################################
#~ 
    #~ def __post_to_cenit (self, cr, uid, values, context=None):
        #~ path = "/api/v1/push"
#~ 
        #~ _logger.info ("\n\nValues: %s\n", values)
        #~ 
        #~ rc = False
        #~ try:
            #~ rc = self.post (cr, uid, path, values, context=context)
        #~ except Warning, e:
            #~ _logger.exception (e)
#~ 
        #~ return rc
    #~ 
    #~ def execute (self, cr, uid, ids, context=None):
        #~ super (CenitHubConfig, self).execute (
            #~ cr, uid, ids, context=context
        #~ )
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ config = self.browse (cr, uid, ids, context=context)
#~ 
        #~ values = {}
        #~ 
        #~ conn_values = {
            #~ 'name': config.conn_name,
            #~ 'url': config.conn_url,
        #~ }
        #~ 
        #~ conn_cenitID = config_parameters.get_param (
            #~ cr, uid, "odoo_cenit.conn_cenitID", default=None, context=context
        #~ )
        #~ if conn_cenitID:
            #~ conn_values.update ({
                #~ 'id': conn_cenitID
            #~ })
#~ 
        #~ values = {
            #~ 'connection': conn_values
        #~ }
#~ 
        #~ rc = self.__post_to_cenit (cr, uid, values, context=context)
#~ 
        #~ _logger.info ("\n\nRC: %s\n", rc)
#~ 
        #~ if rc:
            #~ conn_cenitID = rc['connections'][0]['id']
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.conn_cenitID",
                #~ conn_cenitID, context=context
            #~ )
        #~ else:
            #~ warning = {
                #~ 'title': _('Error!'),
                #~ 'message' :
                    #~ _('Something failed while attempting to configure %s as a connection in Cenit' % (
                        #~ config.conn_name
                    #~ )
                #~ )
            #~ }
            #~ return {'warning': warning}
#~ 
        #~ role = config.conn_role_id
        #~ if role:
            #~ rc = False
            #~ if not role.cenitID:
                #~ rc = role.cenit_push (cr, uid, role.id, context=context)
            #~ if rc:
                #~ role_values = role._get_values ()
                #~ role_values ['connections'].append ({
                    #~ 'id': conn_cenitID
                #~ })
                #~ values = {
                    #~ 'connection_role': role_values 
                #~ }
#~ 
            #~ rc = self.__post_to_cenit (cr, uid, values, context=context)
        #~ 
            #~ _logger.info ("\n\nRC: %s\n", rc)
#~ 
