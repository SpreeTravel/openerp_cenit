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

from openerp import models, fields, api
#~ from openerp.addons.oe_cenit_client import cenit_api
from openerp.addons.web.http import request
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class CenitHubConfig (models.TransientModel):

    #~ def _get_translators (self, *args, **kwargs): #, cr, uid, context=None):
        #~ cenit = cenit_api.CenitApi ()
        #~ path = "/api/v1/translator"
#~ 
        #~ rc = cenit.get (
            #~ #self.env.cr,
            #~ #self.env.uid,
            #~ path,
            #~ #context=self.env.context
        #~ )
#~ 
        #~ values = []
        #~ 
        #~ for item in rc:
            #~ it = item.get ("translator")
            #~ values.append ((it.get('id'), it.get('name')))
#~ 
        #~ return values
    
    _name = 'cenit.hub.settings'
    _inherit = 'res.config.settings'

    cenit_url = fields.Char ('Cenit URL', required=1)
    cenit_user_key = fields.Char ('Cenit User key')
    cenit_user_token = fields.Char ('Cenit User token')
    odoo_endpoint = fields.Many2one ('cenit.connection', string='Odoo endpoint')

    #~ cenit_translator = fields.Selection (
        #~ _get_translators, string="Translator"
    #~ )

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
        
    #~ def get_default_cenit_translator (self, cr, uid, ids, context=None):
        #~ cenit_translator = self.pool.get ("ir.config_parameter").get_param (
            #~ cr, uid, "odoo_cenit.cenit_translator", default=None, context=context
        #~ )
#~ 
        #~ return {'cenit_translator': cenit_translator or False}

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

    #~ def set_cenit_translator (self, cr, uid, ids, context=None):
        #~ config_parameters = self.pool.get ("ir.config_parameter")
        #~ for record in self.browse (cr, uid, ids, context=context):
            #~ config_parameters.set_param (
                #~ cr, uid, "odoo_cenit.cenit_translator",
                #~ record.cenit_translator or '', context=context
            #~ )
