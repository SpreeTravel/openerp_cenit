        # -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/cenit/<string:path>', type='json', auth='none')
    def consume(self, path):
        res = False
        db = request.httprequest.headers.environ['HTTP_X_HUB_STORE']
        pwd = request.httprequest.headers.environ['HTTP_X_HUB_TOKEN']
        if db in http.db_list():
            request.session.authenticate(db, 'admin', 'admin')
            action, model = path.split('_')
            wh = request.registry.models.get('cenit.handler')
            context = {'sender': 'client'}
            res = getattr(wh, action)(request.cr, request.uid,
                                      request.jsonrequest[model],
                                      model, context)
        return res and True or res
