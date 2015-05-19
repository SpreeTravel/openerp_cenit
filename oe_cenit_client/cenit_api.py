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
import logging

from openerp import models, fields, api

from openerp.addons.web.http import request

from openerp.tools import config
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class CenitApi (object):

    def _get_values (self):
        vals = self.read ([])[0]
        vals.pop ('create_uid')
        vals.pop ('create_date')
        vals.pop ('__last_update')
        vals.pop ('write_uid')
        vals.pop ('write_date')
        vals.pop ('display_name')
        vals.pop ('id')

        _logger.info ("\n\nReturning values: %s\n", vals)
        return vals

    def _calculate_update (self, values):
        update = {}
        for k,v in values.items ():
            if k == "%s" % (self.cenit_models):
                update = {
                    'cenitID': v[0] ['id']
                }

        return update

    def cenit_push (self, cr, uid, _id, context=None):
        obj = self.browse (cr, uid, _id, context=context)

        path = "/api/v1/push"
        values = {
            self.cenit_model: obj._get_values ()
        }

        rc = False
        _logger.info ("\n\nPushing to Cenit values: %s\n", values)
        try:
            rc = self.post (cr, uid, path, values, context=context)
            _logger.info ("\n\nResponse received: %s\n", rc)

            if rc.get ('success', False):
                update = self._calculate_update (rc['success'])
                if not isinstance (context, dict):
                    context = {}
                else:
                    context = context.copy ()
                context.update ({'noPush':True})
                rc = self.write (cr, uid, obj.id, update, context=context)
            else:
                _logger.error (rc.get ('errors'))
                return False
        except Warning as e:
            _logger.exception (e)

        return rc

    def cenit_drop (self, cr, uid, _id, context=None):
        obj = self.browse (cr, uid, _id, context=context)
        path = "/api/v1/%s/%s" % (self.cenit_model, obj.cenitID)

        rc = False
        _logger.info ("\n\nDroping from Cenit: %s\n", path)

        try:
            rc = self.delete (cr, uid, path, context=context)
            _logger.info ("\n\nResponse received: %s\n", rc)
        except Warning as e:
            _logger.exception (e)

        return rc

    @api.cr_uid_context
    def post (self, cr, uid, path, vals, context=None):
        config = self.instance(cr, uid, context)
        payload = simplejson.dumps(vals)

        _logger.info ("\n\nJSON: %s\n\n", payload)

        r = requests.post(
            config.get ('cenit_url') + path,
            data=payload,
            headers=self.headers (config)
        )
        if 200 <= r.status_code < 300:
            return simplejson.loads (r.content)

        _logger.exception (simplejson.loads (r.content))
        raise Warning('Error trying to configure Cenit.')

    @api.cr_uid_context
    def get(self, cr, uid, path, context=None):
        config = self.instance(cr, uid, context)

        r = requests.get (
            config.get ('cenit_url') + path,
            headers=self.headers (config)
        )
        if 200 <= r.status_code < 300:
            return simplejson.loads(r.content)
        raise Warning('Error getting data from Cenit.')

    @api.cr_uid_context
    def delete(self, cr, uid, path, context=None):
        config = self.instance(cr, uid, context)

        r = requests.delete (
            config.get ('cenit_url') + path,
            headers=self.headers(config)
        )
        if 200 <= r.status_code < 300:
            return True

        raise Warning('Error removing data in Cenit.')

    def instance(self, cr, uid, ids, context=None):
        icp = request.registry.get ('ir.config_parameter')

        config = {
            'cenit_url': icp.get_param (
                cr, uid, "odoo_cenit.cenit_url", default=None, context=context
            ),
            'cenit_user_key': icp.get_param (
                cr, uid, "odoo_cenit.cenit_user_key", default=None, context=context
            ),
            'cenit_user_token': icp.get_param (
                cr, uid, "odoo_cenit.cenit_user_token", default=None, context=context
            ),
        }

        return config

    def headers(self, config):
        return {
            'Content-Type': 'application/json',
            'X-User-Access-Key': config.get ('cenit_user_key'),
            'X-User-Access-Token': config.get ('cenit_user_token')
        }

    @api.cr_uid_context
    def create (self, cr, uid, vals, context=None):
        _logger.info ('\n\nCreating with context: %s\n', context)
        obj_id = super (CenitApi, self).create (
            cr, uid, vals, context=context
        )

        local = False
        if isinstance (context, dict):
            local = context.get ('local', False)

        _logger.info ('\n\nLocal?: %s\n', local)
        if local:
            return obj_id

        rc = False
        try:
            rc = self.cenit_push (cr, uid, obj_id, context=context)
        except requests.ConnectionError as e:
            _logger.exception (e)
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Cenit refused the connection. It is probably down.')
            }
            return False # {'warning': warning}
        except Exception as e:
            _logger.exception (e)
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Something wicked happened.')
            }
            return False # {'warning': warning}

        if not rc:
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Something wicked happened.')
            }
            return False # {'warning': warning}

        return obj_id

    @api.cr_uid_ids_context
    def write (self, cr, uid, ids, vals, context=None):
        _logger.info ('\n\nWriting with context: %s\n', context)
        push = True
        if isinstance (context, dict):
            push = not (context.get ('noPush', False))

        if isinstance (ids, (int, long)):
            ids = [ids]

        res = super (CenitApi, self).write (
            cr, uid, ids, vals, context=context
        )

        cp = vals.copy ()
        if cp.pop ('cenitID', False):
            if len (cp.keys ()) == 0:
                return res

        try:
            if push:
                for obj in self.browse (cr, uid, ids, context=context):
                    self.cenit_push (cr, uid, obj.id, context=context)
        except requests.ConnectionError as e:
            _logger.exception (e)
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Cenit refused the connection. It is probably down.')
            }
            return False # {'warning': warning}
        except Exception as e:
            _logger.exception (e)
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Something wicked happened.')
            }
            return False # {'warning': warning}

        #~ if not rc:
            #~ warning = {
                #~ 'title': _('Error!'),
                #~ 'message' :
                    #~ _('Something wicked happened.')
            #~ }
            #~ return {'warning': warning}
            #~
        return res

    def unlink(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            try:
                rc = self.cenit_drop (cr, uid, rec.id, context=context)
            except requests.ConnectionError as e:
                _logger.exception (e)
                warning = {
                    'title': _('Error!'),
                    'message' :
                        _('Cenit refused the connection. It is probably down.')
                }
                return False # {'warning': warning}
            except Exception as e:
                _logger.exception (e)
                warning = {
                    'title': _('Error!'),
                    'message' :
                        _('Something wicked happened.')
                }
                return False # {'warning': warning}
            if rc:
                rc = super (CenitApi, self).unlink (
                    cr, uid, rec.id, context=context
                )

        if not rc:
            warning = {
                'title': _('Error!'),
                'message' :
                    _('Something wicked happened.')
            }
            return False # {'warning': warning}
