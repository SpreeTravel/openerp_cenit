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
import requests
import simplejson


class WombatClient(models.Model):
    _name = 'wombat.client'

    url = fields.Char('URL', size=255)
    store = fields.Char('Store', size=64)
    token = fields.Char('Token', size=64)
    push_object_ids = fields.One2many('wombat.push.object', 'client_id',
                                      'Models')

    def push(self, cr, uid, ids, context=None):
        res = []
        ws = self.pool.get('wombat.serializer')
        obj = self.browse(cr, uid, ids[0], context)
        for po in obj.push_object_ids:
            mo = self.pool.get(po.model_id.model, False)
            if mo:
                models = []
                model_ids = mo.search(cr, uid, [], context=context)
                for x in mo.browse(cr, uid, model_ids, context):
                    models.append(ws.serialize(cr, uid, x))
                payload = simplejson.dumps({po.root: models})
                headers = {
                    'Content-Type': 'application/json',
                    'X-Hub-Store': obj.store,
                    'X-Hub-Access-Token': obj.token
                }
                r = requests.post(obj.url, data=payload, headers=headers)
                res.append(r.status_code)
        return res


class WombatPushObject(models.Model):
    _name = 'wombat.push.object'

    client_id = fields.Many2one('wombat.client', 'Client')
    root = fields.Char('Root', size=64)
    model_id = fields.Many2one('ir.model', 'Model')
