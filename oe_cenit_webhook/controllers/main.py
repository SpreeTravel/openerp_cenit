        # -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request


class WebhookController(http.Controller):

    @http.route('/cenit/<string:path>', type='json', auth='none')
    def consume(self, path):
        db = request.httprequest.headers.environ['HTTP_X-Hub-Store']
        pwd = request.httprequest.headers.environ['HTTP_X-Hub-Access-Token']
        if db in http.db_list():
            uid = request.session.authenticate(db, 'admin', 'admin')
            if uid is not False:
                action, model = path.split('_')
                wh = request.registry.models.get('cenit.handler')
                context = {'sender': 'client'}
                return getattr(wh, action)(request.cr, request.uid,
                                           request.jsonrequest[model],
                                           model, context)
        return False
