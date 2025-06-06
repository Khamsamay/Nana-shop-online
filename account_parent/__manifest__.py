# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 - 2020 Steigend IT Solutions (Omal Bastin)
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
{
    'name': "Parent Account (Chart of Account Hierarchy)",
    'summary': """
        Adds Parent account and ability to open chart of account list view based on the date and moves""",
    'description': """
This module 
        * Adds new type 'view' in account type
        * Adds parent account in account
        * Adds Chart of account hierarchy view
        * Adds credit, debit and balance in account
        * Shows chart of account based on the date and target moves we have selected
        * Provide PDF and XLS reports
    - Need to set the group show chart of account structure to view the chart of account hierarchy.
    For any support contact o4odoo@gmail.com or omalbastin@gmail.com
    """,

    'author': 'Omal Bastin / O4ODOO',
    'live_test_url': 'https://accountparent.o4odoo.com/',
    'license': 'OPL-1',
    'website': 'http://o4odoo.com',
    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'depends': ['account'],
    'data': [
        'security/account_parent_security.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/open_chart.xml',
        # 'data/account_type_data.xml',
        # 'views/account_parent_template.xml', #moved to assests tag
        'views/report_coa_hierarchy.xml',
        'report/coa_report.xml',
        'views/res_config_view.xml'
    ],
    'demo': [
    ],
    'assets': {
        # 'web.assets_common': [
        #     'account_parent/static/src/scss/coa_hierarchy.scss',
        # ],
        # 'web.assets_backend': [
        #     'account_parent/static/src/js/account_parent_backend.js',
        #     'account_parent/static/src/js/account_parent_widgets.js'
        # ],
        # 'web.assets_qweb': [
        #     'account_parent/static/src/xml/account_parent_backend.xml',
        #     'account_parent/static/src/xml/account_parent_line.xml',
        # ]
        'web.assets_frontend': [
            'account_parent/static/src/scss/coa_hierarchy.scss',
        ],
        'web.assets_backend': [
            'account_parent/static/src/js/account_parent_backend.js',
            'account_parent/static/src/xml/account_parent_backend.xml',
            'account_parent/static/src/xml/account_parent_line.xml',
            'account_parent/static/src/scss/coa_hierarchy.scss',
        ]
    },

    'currency': 'USD',
    'price': '25.0',
    'images': ['static/description/account_parent_9.png'],
    'installable': True,
    'post_init_hook': '_assign_account_parent',
}
