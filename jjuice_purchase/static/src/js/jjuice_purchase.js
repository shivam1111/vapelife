openerp.jjuice_purchase = function(instance) {
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    var module = instance.point_of_sale;
    var round_di = instance.web.round_decimals;
    var round_pr = instance.web.round_precision;

    instance.web.ListView.Groups = instance.web.ListView.Groups.extend({
        render_groups: function (datagroups) {
            var self = this;
            var placeholder = this.make_fragment();
            _(datagroups).each(function (group) {
                if (self.children[group.value]) {
                    self.records.proxy(group.value).reset();
                    delete self.children[group.value];
                }
                var child = self.children[group.value] = new (self.view.options.GroupsType)(self.view, {
                    records: self.records.proxy(group.value),
                    options: self.options,
                    columns: self.columns
                });
                self.bind_child_events(child);
                child.datagroup = group;
                var $row = child.$row = $('<tr class="oe_group_header">');
                if (group.openable && group.length) {
                    $row.click(function (e) {
                        if (!$row.data('open')) {
                            $row.data('open', true)
                                .find('span.ui-icon')
                                    .removeClass('ui-icon-triangle-1-e')
                                    .addClass('ui-icon-triangle-1-s');
                            child.open(self.point_insertion(e.currentTarget));//working
                        } else {
                            $row.removeData('open')
                                .find('span.ui-icon')
                                    .removeClass('ui-icon-triangle-1-s')
                                    .addClass('ui-icon-triangle-1-e');
                            child.close();
                            // force recompute the selection as closing group reset properties
                            var selection = self.get_selection();
                            $(self).trigger('selected', [selection.ids, this.records]);
                        }
                    });
                }
    //===============================================================================================
                var flag = 0;
                var $button_picking;
                _(child.datagroup.context.__contexts).each(function(context){
                    if (context.hasOwnProperty("product_receive")){
                        if (child.datagroup.grouped_on == "picking_id"){
                            picking_id = child.datagroup.value[0]
                            $button_picking = child.$button_picking = $("<button title='Transfer the whole Order at once' id = "+picking_id+" class='oe_button oe_highlight'><img src='/web/static/src/img/icons/gtk-go-forward.png'></button>")
                        	$row.append($button_picking);
                            flag = 1;
                            $button_picking.on('click',function(){
                        		var model = new instance.web.Model('stock.picking');
                            	model.call('do_enter_transfer_details',[[picking_id]]).then(function(action){
                            		instance.client.action_manager.do_action(action).done(function(e){
                            			console.log(self.view.ViewManager.ActionManager.dialog);
                            			self.view.ViewManager.ActionManager.dialog.$el.on('remove',function(){
                            				self.view.reload_content();
                            			});
                            		});
                            	});
                            });                 
                        }
                    };                
                });  
    //=================================================================================================          

                placeholder.appendChild($row[0]);

                var $group_column = $('<th class="oe_list_group_name">').appendTo($row);
                // Don't fill this if group_by_no_leaf but no group_by
                if (group.grouped_on) {
                    var row_data = {};
                    row_data[group.grouped_on] = group;
                    var group_label = _t("Undefined");
                    var group_column = _(self.columns).detect(function (column) {
                        return column.id === group.grouped_on; });
                    if (group_column) {
                        try {
                            group_label = group_column.format(row_data, {
                                value_if_empty: _t("Undefined"),
                                process_modifiers: false
                            });
                        } catch (e) {
                            group_label = _.str.escapeHTML(row_data[group_column.id].value);
                        }
                    } else {
                        group_label = group.value;
                        if (group_label instanceof Array) {
                            group_label = group_label[1];
                        }
                        if (group_label === false) {
                            group_label = _t('Undefined');
                        }
                        group_label = _.str.escapeHTML(group_label);
                    }
                        
                    // group_label is html-clean (through format or explicit
                    // escaping if format failed), can inject straight into HTML
                    $group_column.html(_.str.sprintf(_t("%s (%d)"),
                        group_label, group.length));

                    if (group.length && group.openable) {
                        // Make openable if not terminal group & group_by_no_leaf
                        $group_column.prepend('<span class="ui-icon ui-icon-triangle-1-e" style="float: left;">');
                    } else {
                        // Kinda-ugly hack: jquery-ui has no "empty" icon, so set
                        // wonky background position to ensure nothing is displayed
                        // there but the rest of the behavior is ui-icon's
                        $group_column.prepend('<span class="ui-icon" style="float: left; background-position: 150px 150px">');
                    }
                }
                self.indent($group_column, group.level);

                if (self.options.selectable) {
                    $row.append('<td>');
                }
                _(self.columns).chain()
                    .filter(function (column) { return column.invisible !== '1'; })
                    .each(function (column) {
                        if (column.meta) {
                            // do not do anything
                        } else if (column.id in group.aggregates) {
                            var r = {};
                            r[column.id] = {value: group.aggregates[column.id]};
                            $('<td class="oe_number">')
                                .html(column.format(r, {process_modifiers: false}))
                                .appendTo($row);
                        } else {
                            $row.append('<td>');
                        }
                    });
                if (self.options.deletable) {
                    $row.append('<td class="oe_list_group_pagination">');
                }
                if (flag == 1 ){
//                	$row.append($button_picking);
                	$row.find("td:last-child").remove();
                }
            });
            return placeholder;
        },
    });
};