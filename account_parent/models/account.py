# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 - 2020 Steigend IT Solutions (Omal Bastin)
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
from odoo import api, fields, models, _
from odoo.osv import expression


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"


	def _query_get(self, domain=None):
		context = dict(self._context or {})
		domain = domain or []
		date_field = 'date'
		if context.get('aged_balance'):
			date_field = 'date_maturity'
		if context.get('date_to'):
			domain += [(date_field, '<=', context['date_to'])]
		if context.get('date_from'):
			if not context.get('strict_range'):
				domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
			elif context.get('initial_bal'):
				domain += [(date_field, '<', context['date_from'])]
			else:
				domain += [(date_field, '>=', context['date_from'])]

		if context.get('journal_ids'):
			domain += [('journal_id', 'in', context['journal_ids'])]

		state = context.get('state')
		if state and state.lower() != 'all':
			domain += [('parent_state', '=', state)]

		if context.get('company_id'):
			domain += [('company_id', '=', context['company_id'])]
		elif context.get('allowed_company_ids'):
			domain += [('company_id', 'in', self.env.companies.ids)]
		else:
			domain += [('company_id', '=', self.env.company.id)]

		if context.get('reconcile_date'):
			domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.max_date', '>', context['reconcile_date']), ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

		if context.get('account_tag_ids'):
			domain += [('account_id.tag_ids', 'in', context['account_tag_ids'])]

		if context.get('account_ids'):
			if isinstance(context['account_ids'], list):
				domain += [('account_id', 'in', context['account_ids'])]
			else:    
				domain += [('account_id', 'in', context['account_ids'].ids)]
		if context.get('analytic_tag_ids'):
			domain += [('analytic_tag_ids', 'in', context['analytic_tag_ids'])]

		if context.get('analytic_account_ids'):
			domain += [('analytic_account_id', 'in', context['analytic_account_ids'])]
		if context.get('partner_ids'):
			domain += [('partner_id', 'in', context['partner_ids'])]

		if context.get('partner_categories'):
			domain += [('partner_id.category_id', 'in', context['partner_categories'])]

		tables = ''
		if domain:
			domain.append(('display_type', 'not in', ('line_section', 'line_note')))
			domain.append(('parent_state', '!=', 'cancel'))

		return domain



class AccountAccount(models.Model):
	_inherit = "account.account"

	parent_id = fields.Many2one('account.account', string='Parent Account', ondelete="set null")
	child_ids = fields.One2many('account.account', 'parent_id', string='Child Accounts')
	parent_path = fields.Char(index=True)
	initial_balance = fields.Float(compute="compute_values", digits=(16, 4), string='Initial Balance')
	balance = fields.Float(compute="compute_values", digits=(16, 4), string='Balance')
	credit = fields.Float(compute="compute_values", digits=(16, 4), string='Credit')
	debit = fields.Float(compute="compute_values", digits=(16, 4), string='Debit')
	move_line_ids = fields.One2many('account.move.line', 'account_id', string='Journal Entry Lines')
	account_type = fields.Selection(selection_add=[('view', 'View')], ondelete={'view': 'cascade'})

	_parent_name = "parent_id"
	_parent_store = True
	_parent_order = 'code, name'
	_order = 'code, id'

	@api.depends('move_line_ids', 'move_line_ids.amount_currency', 'move_line_ids.debit', 'move_line_ids.credit')
	def compute_values(self):
		company_dict = {}
		target_currency = self.env.context.get('target_currency_id') and self.env['res.currency'].browse(
			self.env.context['target_currency_id'])

		for account in self:
			sub_accounts = self.with_context(show_parent_account=True).search([('id', 'child_of', [account.id])])
			balance = credit = debit = initial_balance = initial_deb = initial_cre = 0.0
			context = dict(self.env.context, account_ids=sub_accounts.ids)
			# tables, where_clause, where_params = self.env['account.move.line'].with_context(context)._query_get()
			domain = self.env['account.move.line'].with_context(context)._query_get(domain=None)
			query = self.env['account.move.line']._where_calc(domain=domain)
			query_str, params = query.select('account_move_line.debit','account_move_line.credit', 'account_move_line.date', 'account_move_line.company_id')
			self._cr.execute(query_str, params)
			for deb, cre, date, company_id in self.env.cr.fetchall():
				if company_id not in company_dict:
					company_dict[company_id] = self.env['res.company'].browse(company_id)
				if target_currency:
					deb = company_dict[company_id].currency_id._convert(deb, target_currency, company_dict[company_id],
																		date)
					cre = company_dict[company_id].currency_id._convert(cre, target_currency, company_dict[company_id],
																		date)

				balance += deb - cre
				credit += cre
				debit += deb
			account.balance = balance
			account.credit = credit
			account.debit = debit

			if context.get('show_initial_balance'):
				context.update(initial_bal=True)
				domain_initial = self.env['account.move.line'].with_context(context)._query_get(domain=None)
				query_init = self.env['account.move.line']._where_calc(domain=domain)
				query_init_str, query_init_params = query_init.select('account_move_line.debit','account_move_line.credit', 'account_move_line.date', 'account_move_line.company_id')
				self.env.cr.execute(query_init_str, query_init_params)
				for deb, cre, date, company_id in self.env.cr.fetchall():
					if company_id not in company_dict:
						company_dict[company_id] = self.env['res.company'].browse(company_id)
					if target_currency:
						deb = company_dict[company_id].currency_id._convert(deb, target_currency,
																			company_dict[company_id], date)
						cre = company_dict[company_id].currency_id._convert(cre, target_currency,
																			company_dict[company_id], date)
					initial_cre += cre
					initial_deb += deb
				initial_balance += initial_deb - initial_cre
				account.initial_balance = initial_balance
			else:
				account.initial_balance = 0

	@api.model
	def _search(self, args, offset=0, limit=None, order=None):
		context = self._context or {}
		new_args = []
		for arg in args:
			if isinstance(arg, (list, tuple)) and arg[0] == 'name' and isinstance(arg[2], str):
				new_args.append('|')
				new_args.append(arg)
				new_args.append(['code', arg[1], arg[2]])
			else:
				new_args.append(arg)
		if not context.get('show_parent_account', False):
			new_args = expression.AND([[('account_type', '!=', 'view')], new_args])
		return super(AccountAccount, self)._search(
			new_args, offset=offset, limit=limit, order=order)

	
class AccountJournal(models.Model):
	_inherit = "account.journal"
	
	@api.model
	def _prepare_liquidity_account(self, name, company, currency_id, type):
		res = super(AccountJournal, self)._prepare_liquidity_account(name, company, currency_id, type)
		if type == 'bank':
			account_code_prefix = company.bank_account_code_prefix or ''
		else:
			account_code_prefix = company.cash_account_code_prefix or company.bank_account_code_prefix or ''

		parent_id = self.env['account.account'].with_context({'show_parent_account':True}).search([
														('code', '=', account_code_prefix),
														('company_id', '=', company.id),
														('user_type_id.type', '=', 'view')], limit=1)
		
		if parent_id:
			res.update({'parent_id': parent_id.id})
		return res

