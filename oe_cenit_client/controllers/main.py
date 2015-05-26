# -*- coding: utf-8 -*-

import logging
import inflect
# import werkzeug
from openerp import http
from openerp import SUPERUSER_ID
from openerp.http import request
from openerp.modules.registry import RegistryManager
# import simplejson

_logger = logging.getLogger(__name__)


class WebhookController(http.Controller):

    @http.route(
        ['/cenit/<string:action>',
         '/cenit/<string:action>/<string:root>'],
        type='json', auth='none'
    )
    def consume(self, action, root=None):
        status_code = 400
        environ = request.httprequest.headers.environ.copy()

        key = environ.get('HTTP_X_HUB_STORE', False)
        token = environ.get('HTTP_X_HUB_ACCESS_TOKEN', False)
        db_name = environ.get('HTTP_TENANT_DB', False)

        if not db_name:
            host = environ.get('HTTP_HOST', "")
            db_name = host.replace(".", "_")

        if db_name in http.db_list():
            registry = RegistryManager.get(db_name)
            with registry.cursor() as cr:
                connection_model = registry['cenit.connection']
                domain = [('key', '=', key), ('token', '=', token)]
                rc = connection_model.search(cr, SUPERUSER_ID, domain)
                if rc:
                    p = inflect.engine()
                    _logger.info("\n\nJSonRequest: %s\n", request.jsonrequest)
                    flow_model = registry['cenit.flow']
                    context = {'sender': 'client', 'action': action}
                    if root is None:
                        for root, data in request.jsonrequest.items():
                            root = p.singular_noun(root) or root
                            rc = flow_model.receive (cr, SUPERUSER_ID, root,
                                                     data, context)
                            if rc:
                                status_code = 200
                    else:
                        root = p.singular_noun(root) or root
                        rc = flow_model.receive (cr, SUPERUSER_ID, root,
                                                 request.jsonrequest, context)
                        if rc:
                            status_code = 200
                    _logger.info ("\n\nAction status: %s\n", rc)
                else:
                    status_code = 404
        _logger.info("\n\nStatusCode: %s\n", status_code)
        return True
#         return werkzeug.wrappers.Response(status=status_code,
#                                           content_type="application/json")
