# -*- coding: utf-8 -*-

from openerp.addons.web import http
from openerp.addons.web.http import request


class consumer(http.Controller):

    @http.route('/wombat/add_product', type="http", auth="none")
    def add_product(self, **kwargs):
        params = str(request.params)
        return "<h1>This is a test" + params + "</h1>"
