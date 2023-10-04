/* global ace */
odoo.define('state_selection_colors.state', function (require) {
    "use strict";
    var basic_fields = require('web.basic_fields')
    basic_fields.StateSelectionWidget.include({
        _prepareDropdownValues: function () {
            var self = this;
            var _data = [];
            var current_stage_id = self.recordData.stage_id && self.recordData.stage_id[0];
            var stage_data = {
                id: current_stage_id,
                legend_normal: this.recordData.legend_normal || undefined,
                legend_blocked: this.recordData.legend_blocked || undefined,
                legend_done: this.recordData.legend_done || undefined,
            };
            _.map(this.field.selection || [], function (selection_item) {
                var value = {
                    'name': selection_item[0],
                    'tooltip': selection_item[1],
                };
                if (selection_item[0] === 'normal') {
                    value.state_name = stage_data.legend_normal ? stage_data.legend_normal : selection_item[1];
                } else if (selection_item[0] === 'done') {
                    value.state_class = 'o_status_green';
                    value.state_name = stage_data.legend_done ? stage_data.legend_done : selection_item[1];
                } else if (selection_item[0] === 'blocked') {
                    value.state_class = 'o_status_red';
                    value.state_name = stage_data.legend_blocked ? stage_data.legend_blocked : selection_item[1];
                } else {
                    value.state_class = selection_item[0];
                    value.state_name = selection_item[1];
                }
                _data.push(value);
            });
            return _data;
        },
        _render: function () {
            var self = this;
            this._super.apply(this, arguments);
            const states = this._prepareDropdownValues();
            states.forEach(function (state) {
                if (state.name.includes("_")) {
                    var color = state.state_class.split("_");
                    if (color.length == 2) {
                        self.$('.' + state.state_class).css('background-color', "#" + color[1]);
                    } else {
                        self.$('.' + state.state_class).css('background-color', "gray");
                    }
                }
            });
        }
    });
});