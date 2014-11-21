        # -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/wombat/<string:path>', type='json', auth='none')
    def consume(self, path):
        res = False
        db = request.httprequest.headers.environ['HTTP_X_HUB_STORE']
        pwd = request.httprequest.headers.environ['HTTP_X_HUB_TOKEN']
        if db in http.db_list():
            request.session.authenticate(db, 'admin', pwd)
            action, model = path.split('_')
            wh = request.registry.models.get('wombat.handler')
            res = getattr(wh, action)(request.cr, request.uid,
                                      request.jsonrequest[model], model)
        return res and True or res
