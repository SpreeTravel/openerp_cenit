        # -*- coding: utf-8 -*-

from openerp import http
from openerp.http import request
from openerp.addons.oe_cenit_webhook.csv_utils import CsvUnicodeReader


class WebhookController(http.Controller):

    @http.route('/cenit/<string:path>', type='json', auth='none')
    def consume(self, path):
        db = request.httprequest.headers.environ['HTTP_X_HUB_STORE']
        pwd = request.httprequest.headers.environ['HTTP_X_HUB_TOKEN']
        if db in http.db_list():
            uid = request.session.authenticate(db, 'admin', 'admin')
            if uid is not False:
                action, model = path.split('_')
                flow_obj = request.registry.models.get('cenit.flow')
                context = {'sender': 'client', 'action': action}
                flow_obj.receive(request.cr, request.uid, model,
                                 request.jsonrequest[model], context)
        return False

    @http.route('/oscar/usdadata', type='json', auth='none')
    def add_usdadata(self):
        file_path = request.jsonrequest['filepath']
        delimiter = '@'
        db = request.httprequest.headers.environ['HTTP_X_HUB_STORE']
        if db in http.db_list():
            uid = request.session.authenticate(db, 'admin', 'admin')
            if uid is not False:
                market_price = request.registry.models.get('market.price.by.date')
                row_number = 0
                for row in CsvUnicodeReader(open(file_path, 'rb'),
                                            delimiter=delimiter, quotechar='"',
                                            escapechar='\\'):
                    row_number += 1
                    vals = {}
                    if row_number > 1:
                        vals['markettype'] = row[0]
                        vals['commodityname'] = row[1]
                        vals['cityname'] = row[2]
                        vals['variety'] = row[3]
                        vals['color'] = row[4]
                        vals['origin'] = row[5]
                        vals['date'] = row[6]
                        vals['per_lb'] = row[7]
                        market_price.create(request.cr, request.uid, vals,
                                            request.context)
        return "<h1>This is a test</h1>"
