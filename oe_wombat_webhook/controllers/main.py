# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/wombat/<string:db>/<string:path>', type="json", auth="none")
    def consume(self, db, path, **kwargs):
        res = False
        if db in http.db_list():
            request.session.authenticate(db, 'admin', 'admin')
            action, obj = path.split('_')
            model = request.registry.models.get(obj + '.handler', False)
            if model:
                res = getattr(model, action)(request.cr, request.uid,
                                             request.jsonrequest[obj],
                                             request.context)
        return res and True or res
