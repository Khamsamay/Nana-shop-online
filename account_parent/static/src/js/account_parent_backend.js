/** @odoo-module **/

// account_parent_backend.js
import { Component, useState ,onWillStart} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Layout } from "@web/search/layout";
import { parseHTML } from "@html_editor/utils/html";
import { useSetupAction } from "@web/search/action_hook";
import { rpc } from "@web/core/network/rpc";
import { download } from "@web/core/network/download";


function processLine(line) {
    return { ...line, lines: [], isFolded: true };
}

export class CoaHierarchy extends Component {
    static template = "CoaHierarchy";
    static components = { Layout };
    setup() {
        this.ui = useService("ui");
        this.orm = useService("orm");
        this.actionService = useService("action");

        useSetupAction({
            getLocalState: () => ({
                lines: [...this.state.lines],
                heading: this.state.heading,
            }),
        });

        this.state = useState({
            html:'',
            lines: this.props.state?.lines || [],
            heading: this.props.state?.heading || '',
        });

        this.given_context = this.props.action.context;
        this.controller_url = this.props.action.context.url;

        if (this.props.action.context.context) {
            this.given_context = this.props.action.context.context;
        }

        onWillStart(this.onWillStart);

    }

    async onWillStart() {
        var self = this
        if (!this.state.lines.length) {
            const report_data = await this.orm.call("account.open.chart", "get_html", [
                this.given_context,
            ]);
            const mainLines = report_data.lines;
            const heading = report_data.heading;

           if (mainLines) {
                const updatedData = Object.entries(mainLines).map(([index, value]) => {
                    return Object.entries(value).reduce((acc, [key, value]) => {
                        if (["initial_balance", "debit", "credit", "ending_balance", "balance"].includes(key)) {
                            let tempDiv = document.createElement("div");
                            if (typeof value === "object") {
                                tempDiv.innerHTML = JSON.stringify(value);
                            } else {
                                tempDiv.innerHTML = value;
                            }
                            acc[key] = tempDiv.textContent;
                        }
                        else {
                            acc[key] = value;
                        }
                        return acc;
                    }, {});
                });
                self.state.lines = updatedData.map(processLine);
           }

            this.state.heading = heading;
            this.state.html = report_data;
        }
    }

    async toggleLine(line) {

        line.isFolded = !line.isFolded;
        if (!line.lines.length) {
            const report_data = await this.orm.call("account.open.chart", "get_lines", [line.wiz_id, line.id], {
                model_id: line.model_id,
                model_name: line.model,
                level: line.level + 1 || 1,
            })
            if (report_data) {
                const updatedData = Object.entries(report_data).map(([index, value]) => {
                    return Object.entries(value).reduce((acc, [key, value]) => {
                        if (["initial_balance", "debit", "credit", "ending_balance", "balance"].includes(key)) {
                            let tempDiv = document.createElement("div");
                            if (typeof value === "object") {
                                tempDiv.innerHTML = JSON.stringify(value);
                            } else {
                                tempDiv.innerHTML = value;
                            }
                            acc[key] = tempDiv.textContent;
                        }
                        else {
                            acc[key] = value;
                        }
                        return acc;
                    }, {});
                });
                line.lines = updatedData.map(processLine);
           }
            else {
               line.lines = report_data.map(processLine);
            }
        }
    }

    async onClickBoundLink(line) {
        var account_name = "d/d/d/d/d/d/d/d/d/d/"; 

        const [domain, context] = await this.orm.call(
            'account.open.chart',
            'build_domain_context',
            [Math.abs(parseInt(line.wiz_id, 10)) , Math.abs(parseInt(line.id, 10)) ]
        );

        await this.actionService.doAction({
            name: `Journal Items (${account_name})`,
            type: 'ir.actions.act_window',
            res_model: 'account.move.line',
            domain: domain,
            context: context,
            views: [[false, 'list'], [false, 'form']],
            view_type: "list",
            view_mode: "form",
            target: 'current'
        });
    }

    async exportXLS() {
        var self = this
        await this.ui.block();
        await download({
            url: "/account_parent/export/xls",
            data: { wiz_id: this.given_context['active_id'] },
        });
        await this.ui.unblock();
    }

    async exportPDF() {
        var action = {
            'type': 'ir.actions.report',
            'report_type': 'qweb-pdf',
            'report_name': 'account_parent.report_coa_hierarchy_print',
            'report_file': 'account_parent.report_coa_hierarchy_print',
            'context': {
                'active_ids': [this.given_context['active_id']],
                'active_model': 'account.open.chart',
                'landscape': true,
            },
            'data':  {
                model: 'account.open.chart',
                wiz_id: this.given_context['active_id'],
            },
        }
        await this.actionService.doAction(action);
    }
}

registry.category("actions").add("coa_hierarchy", CoaHierarchy);
