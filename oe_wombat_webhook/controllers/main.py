# -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/wombat/<string:db>/<string:path>', type="http", auth="none")
    def consume(self, db, path, **kwargs):
        response = False
        if db in http.db_list():
            request.session.authenticate(db, 'admin', 'admin')
            action, obj = path.split('_')
            model = request.registry.models.get(obj + '.handler', False)
            if model:
                model.process(request.cr, request.uid, action, request.params, request.context)
            response = "<h1>Logged</h1>"
        else:
            response = "<h1>No existe la base de datos</h1>"
        return response
