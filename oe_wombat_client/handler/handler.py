# -*- coding: utf-8 -*-
'''
Created on 15/10/2014

@author: José Andrés Hernández Bustio
'''
from openerp.osv.orm import TransientModel
from matching.matching import MATCHING

# TODO: Poner de forma generica los metodos, ya que esta especifico para product
# Ver como puede leer el fichero donde esta el matching
class handler(TransientModel):
    _name = 'handler'
        
    def find(self, cr, uid, params,m_name,context=None):
        if params.get('sku', False):
            p_ids = self.pool.get(m_name).search(cr, uid,
                                   [('default_code', '=', params['sku'])],
                                   context=context)
            return p_ids
        return []

    def add(self, cr, uid, params,m_name, context=None):
        res = False
        pp = self.pool.get(m_name)
        p_ids = self.find(cr, uid, params, context)
        if not p_ids:
            vals = {v: params[k] for k, v in MATCHING.get(m_name).items()}
            res = pp.create(cr, uid, vals, context)
        return res

    def update(self, cr, uid, params,m_name, context=None):
        res = False
        pp = self.pool.get(m_name)
        p_ids = self.find(cr, uid, params, context)
        if p_ids:
            vals = {v: params[k] for k, v in MATCHING.get(m_name).items()}
            res = pp.write(cr, uid, p_ids, vals, context)
        return res
