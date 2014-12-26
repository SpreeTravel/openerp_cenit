# -*- coding: utf-8 -*-

from openerp import models
from openerp.addons.oe_cenit_client import mixin


class MarketUSDAData(mixin.CenitMixin, models.Model):
    _name = 'market.usda.data'
    _inherit = 'market.usda.data'


class MarketCommodity(mixin.CenitMixin, models.Model):
    _name = 'market.commodity'
    _inherit = 'market.commodity'


class MarketVariety(mixin.CenitMixin, models.Model):
    _name = 'market.variety'
    _inherit = 'market.variety'


class MarketPackage(mixin.CenitMixin, models.Model):
    _name = 'market.package'
    _inherit = 'market.package'
