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
import requests
import simplejson
from openerp import models, fields
from openerp.tools import config


class CenitClient(models.Model):
    _name = 'cenit.client'

    name = fields.Char('Connection Name', size=128, required=1)
    role = fields.Char('Connection Role Name', size=128)
    connection_token = fields.Char('Connection Token', size=128)
    connection_ref = fields.Char('Connection Ref', size=128)
    connection_role_ref = fields.Char('Connection Role Ref', size=128)

    url = fields.Char('URL', size=255, required=1)
    key = fields.Char('Key', size=64, required=1)
    token = fields.Char('Token', size=128, required=1)

    def create(self, cr, uid, vals, context=None):
        res_id = super(CenitClient, self).create(cr, uid, vals, context)
        self.set_connection_in_cenit(cr, uid, [res_id], context)
        return res_id

    def unlink(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            self.delete(cr, uid, '/setup/connections/%s' % obj.connection_ref)
        return super(CenitClient, self).unlink(cr, uid, ids)

    def set_connection_in_cenit(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0])
        rparams = {'connection_role': {'name': obj.role or 'Master'}}
        role = self.post(cr, uid, '/setup/connection_roles', rparams)
        cname = obj.name + ' ' + cr.dbname
        cparams = {'connection': {
            'name': cname,
            'url': '%s/cenit' % self.local_url(),
            'key': cr.dbname,
            'connection_roles': [{'id': role['id']['$oid']}]
        }}
        connection = self.post(cr, uid, '/setup/connections', cparams)
        update = {
            'connection_token': connection['authentication_token'],
            'connection_ref': connection['id']['$oid'],
            'connection_role_ref': role['id']['$oid']
        }
        return self.write(cr, uid, obj.id, update)

    def post(self, cr, uid, path, vals, context=None):
        config = self.instance(cr, uid, context)
        headers = {
            'Content-Type': 'application/json',
            'X-User-Key': config.key,
            'X-User-Access-Token': config.token
        }
        payload = simplejson.dumps(vals)
        r = requests.post(config.url + path, data=payload, headers=headers)
        if r.status_code == 201:
            return simplejson.loads(r.content)
        raise Warning('Error trying to configure Cenit.')

    def get(self, cr, uid, path, context=None):
        config = self.instance(cr, uid, context)
        headers = {
            'Content-Type': 'application/json',
            'X-User-Key': config.key,
            'X-User-Access-Token': config.token
        }
        r = requests.get(config.url + path, headers=headers)
        if r.status_code == 200:
            return simplejson.loads(r.content)
        raise Warning('Error getting data from Cenit.')

    def delete(self, cr, uid, path, context=None):
        config = self.instance(cr, uid, context)
        headers = {
            'Content-Type': 'application/json',
            'X-User-Key': config.key,
            'X-User-Access-Token': config.token
        }
        r = requests.delete(config.url + path, headers=headers)
        if r.status_code == 204:
            return True
        raise Warning('Error removing data in Cenit.')

    def instance(self, cr, uid, context=None):
        client = self.pool.get('cenit.client')
        client_ids = client.search(cr, uid, [])
        if client_ids:
            return client.browse(cr, uid, client_ids[0])
        return False

    def local_url(self):
        return config.get('local_url', 'http://localhost:8069')
