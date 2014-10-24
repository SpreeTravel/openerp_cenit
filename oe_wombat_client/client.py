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

from openerp.osv import fields
from openerp.osv.orm import Model
import requests
import simplejson
from serializers import models

class wombat_client(Model):
    _name = 'wombat.client'
    _columns = {
        'url': fields.char('URL', size=255),
        'store': fields.char('Store', size=64),
        'token': fields.char('Token', size=64),
        'push_object_ids': fields.one2many('wombat.push.object', 'client_id',
                                           'Models')
    }
    
    def push(self, cr, uid, ids, context=None):
        res = []
        obj = self.browse(cr, uid, ids[0], context)
        for po in obj.push_object_ids:
            mo = self.pool.get(po.model_id.model, False)
            if mo:
                model_ids = mo.search(cr, uid, [], context=context)
                models = [mo.serialize(x) for x in mo.browse(cr, uid,
                                                             model_ids,
                                                             context)]
                payload = simplejson.dumps({po.root: models})
                headers = {
                    'Content-Type': 'application/json',
                    'X-Hub-Store': obj.store,
                    'X-Hub-Access-Token': obj.token
                }
                r = requests.post(obj.url, data=payload, headers=headers)
                res.append(r.status_code)
        return res

class wombat_push_object(Model):
    _name = 'wombat.push.object'
    _columns = {
        'client_id': fields.many2one('wombat.client', 'Client'),
        'root': fields.char('Root', size=64),
        'model_id': fields.many2one('ir.model', 'Model')
    }
