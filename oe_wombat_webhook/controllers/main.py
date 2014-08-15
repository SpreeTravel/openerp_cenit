# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/wombat/<string:path>', type="json", auth="none")
    def consume(self, path, **kwargs):
        res = False
        db = request.httprequest.headers.environ['HTTP_X_HUB_STORE']
        pwd = request.httprequest.headers.environ['HTTP_X_HUB_TOKEN']
        if db in http.db_list():
            request.session.authenticate(db, 'admin', pwd)
            action, obj = path.split('_')
            model = request.registry.models.get(obj + '.handler', False)
            if model:
                res = getattr(model, action)(request.cr, request.uid,
                                             request.jsonrequest[obj],
                                             request.context)
        return res and True or res
