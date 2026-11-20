import { patch } from "@web/core/utils/patch";
import { PropertiesField } from "@web/views/fields/properties/properties_field";

/**
 * Conditional intake questions: hide the questions listed in the project's computed field
 * `intake_hidden_keys` ("intake_general.third_party_contact", ...). Display only: the definitions and
 * values stay untouched, and every question shows while the questions are being edited.
 */
patch(PropertiesField.prototype, {
    get groupedPropertiesList() {
        const groups = super.groupedPropertiesList;
        const hidden = this.props.record.data.intake_hidden_keys;
        if (!Array.isArray(hidden) || !hidden.length || this.state.isInEditMode) {
            return groups;
        }
        const prefix = `${this.props.name}.`;
        return groups.map((group) => ({
            ...group,
            elements: group.elements.filter((property) => !hidden.includes(prefix + property.name)),
        }));
    },
});
