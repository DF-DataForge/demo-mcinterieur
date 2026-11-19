import { Component, onWillStart, signal, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useAutofocus, useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

const STATION_LABELS = {
    saw: _t("Paneelzaag"),
    cnc: _t("CNC"),
    assembly: _t("Montage werkplaats"),
};

/**
 * Shop floor scan station. A USB or Bluetooth scanner types the label and ends with Enter,
 * so the input keeps the focus and every Enter processes one label.
 */
export class McScanStation extends Component {
    static template = "mc_interieur.ScanStation";
    props = useProps(standardActionServiceProps);

    scanInput = signal.ref();
    feedback = signal(null);
    queue = signal([]);
    cabinets = signal([]);
    pendingCnc = signal(null);

    setup() {
        this.orm = useService("orm");
        this.station = this.props.action.context.mc_station || "saw";
        this.stationLabel = STATION_LABELS[this.station];
        useAutofocus({ ref: this.scanInput });
        onWillStart(() => this.loadQueue());
    }

    async loadQueue() {
        const data = await this.orm.call("mc.piece", "mc_station_data", [this.station]);
        this.queue.set(data.queue || []);
        this.cabinets.set(data.cabinets || []);
    }

    focusInput() {
        const input = this.scanInput();
        if (input) {
            input.value = "";
            input.focus();
        }
    }

    async onSubmit(ev) {
        ev.preventDefault();
        const code = this.scanInput().value;
        await this.processCode(code);
    }

    async processCode(code) {
        const result = await this.orm.call("mc.piece", "mc_scan", [this.station, code]);
        this.feedback.set(result);
        this.pendingCnc.set(result.awaiting_cnc ? result.piece : null);
        await this.loadQueue();
        this.focusInput();
    }

    async onClickNext() {
        const next = this.queue()[0];
        if (next) {
            await this.processCode(next.barcode);
        }
    }

    async onConfirmCnc() {
        const piece = this.pendingCnc();
        if (!piece) {
            return;
        }
        const result = await this.orm.call("mc.piece", "mc_confirm_cnc", [piece.id]);
        this.feedback.set(result);
        this.pendingCnc.set(null);
        await this.loadQueue();
        this.focusInput();
    }

    async onCabinetAssembled(cabinet) {
        const result = await this.orm.call("mc.piece", "mc_cabinet_assembled", [
            cabinet.project_id,
            cabinet.cabinet,
        ]);
        this.feedback.set(result);
        await this.loadQueue();
        this.focusInput();
    }
}

registry.category("actions").add("mc_scan_station", McScanStation);
