from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController
import json
from werkzeug import urls


class CustomReportController(ReportController):
     @http.route([
          '/report/<converter>/<reportname>',
          '/report/<converter>/<reportname>/<docids>',
     ], type='http', auth='user', website=True)
     def report_routes(self, reportname, docids=None, converter=None, **data):
          if converter == 'html':
               context = dict(request.env.context)
               # Apply additional context from request data
               if data.get("with_company"):
                    context['with_company'] = int(data['with_company'])
               if data.get("cid"):
                    context['allowed_company_ids'] = data['cid']

               if 'allowed_company_ids' in context:
                    company_id = request.env['res.users'].sudo().browse(int(context['allowed_company_ids'].split(',')[0]))
               else:
                    company_id = request.env.company

               if data.get("cid"):
                    allowed_company_ids = [int(i) for i in data["cid"].split(",")]
                    context.update(allowed_company_ids=allowed_company_ids)

               request.env = request.env(context=context)

               # Prepare document IDs
               if docids:
                    docids = [int(i) for i in docids.split(",")]
                    report = request.env['ir.actions.report']._get_report_from_name(reportname)
                    records = request.env[report.model].browse(docids)
                    records.check_access_rule('read')
               else:
                    report = request.env['ir.actions.report']._get_report_from_name(reportname)

               # Render html
               report = report.with_company(company_id)
               html = report.with_context(request.env.context)._render_qweb_html(reportname, docids, data=data)[0]
               return request.make_response(html)

          # Prepare context and custom logic for PDF
          if converter == 'pdf':
               context = dict(request.env.context)
               if data.get("with_company"):
                    context['with_company'] = int(data['with_company'])
               if data.get("cid"):
                    context['allowed_company_ids'] = data['cid']
               if 'allowed_company_ids' in context:
                    allowed_company_ids = context['allowed_company_ids']
                    if isinstance(allowed_company_ids, list):
                         company_id = request.env['res.users'].sudo().browse(allowed_company_ids[0])
                    else:
                         company_id = request.env['res.users'].sudo().browse(int(allowed_company_ids.split(',')[0]))
                    # company_id = request.env['res.users'].sudo().browse(int(context['allowed_company_ids'].split(',')[0]))
               else:
                    company_id = request.env.company

               # Set allowed companies explicitly if provided
               if data.get("cid"):
                    allowed_company_ids = [int(i) for i in data["cid"].split(",")]
                    context.update(allowed_company_ids=allowed_company_ids)

               request.env = request.env(context=context)

               # Prepare document IDs
               if docids:
                    docids = [int(i) for i in docids.split(",")]
                    report = request.env['ir.actions.report']._get_report_from_name(reportname)
                    records = request.env[report.model].browse(docids)
                    records.check_access_rule('read')
               else:
                    report = request.env['ir.actions.report']._get_report_from_name(reportname)

               # Render PDF
               report = report.with_company(company_id)
               pdf = report.with_context(**context)._render_qweb_pdf(reportname, docids, data=data)[0]
               pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
               return request.make_response(pdf, headers=pdfhttpheaders)

          return super().report_routes(reportname, docids=docids, converter=converter, **data)
