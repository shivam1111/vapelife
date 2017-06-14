openerp.jjuice.pos = function (instance,local) {
	
	var _t = instance.web._t,
    _lt = instance.web._lt;
	var QWeb = instance.web.qweb;
	instance.web.jjuice = instance.web.jjuice || {};

	main_defs = $.Deferred();
	$(document).ready(function(){
    	var mod = new instance.web.Model("product.tab", {}, []); // MODEL,CONTEXT,DOMAIN
    	mod.call("fetch_static_data",[]).done(function(res){ //search_read method will automatically not load active = False records
    		main_defs.resolve(res)
    	})//end call
	})
	
	instance.web.form.FieldFloat.include({
		navigate_interface:function(e){
			switch (e.which) {
            case $.ui.keyCode.UP:
            	tr = $(e.srcElement).parents('tr:first');
            	td_index = $($(e.srcElement).parents('td')[0]).index();
            	tr_prev = tr.prev();
            	tr_prev.children("td").eq(td_index).find("input").focus();
            	break;
            case $.ui.keyCode.DOWN:
            	parent = $(e.srcElement).parents('tr:first');
            	td_index = $($(e.srcElement).parents('td')[0]).index();
            	tr_next = parent.next();
            	tr_next.children("td").eq(td_index).find("input").focus();
                break;
            case $.ui.keyCode.RIGHT:
            	parent = $(e.srcElement).parents('td:first');
            	td_next = parent.next();
            	td_next.find("input").focus();	            		            	
            	break;
            case $.ui.keyCode.LEFT:
            	parent = $(e.srcElement).parents('td:first');
            	td_next = parent.prev();
            	td_next.find("input").focus();	            		            		            	
            	break;
			}
		},
		renderElement:function(){
			var self =this
			this._super();
			$input_field = this.$el.find('input')
			if ($input_field.length > 0){
				$input_field.on("keydown",self,self.navigate_interface)
			}
		},
	})
	
	function sortProperties(obj,type='asc')
	{
	   if (!type){
		   type = 'asc'
	   }
	  // convert object into array
	    var sortable=[];
	    for(var key in obj)
	        if(obj.hasOwnProperty(key))
	            sortable.push([key, obj[key]]); // each item is an array in format [key, value]
	    
	    // sort items by value
	    sortable.sort(function(a, b)
	    {
	    	if (type == 'asc'){
	    		return a[1].localeCompare(b[1]); // compare numbers
	    	}else{
	    		return b[1].localeCompare(a[1]); // compare numbers
	    	}
	    	
	    });
	    return sortable; // array in format [ [ key1, val1 ], [ key2, val2 ], ... ]
	}	
	
	remove_spaces = function(string){
		return string.replace(/\s/g, "");
	}

	local.AbstractWidget = {
		prepare_order_line :function(items,product_id,qty,price,discount){
			items.push([0,0,{
				'product_id':product_id,
				'product_uom_qty':qty,
				'price_unit':price,
				'discount':discount,
			}])
		},
		get_product_information:function(product_ids,fields){
			if (product_ids.length > 0) {
				product = new openerp.Model('product.product');
				return product.call("read",[product_ids,fields])
			}else{
				return false
			}
		},
		calculate_availability:function(product){
			virtual = product.virtual_available;
			incoming = product.incoming_qty;
			available = virtual - incoming;
			return available ;
		},
		set_availability:function (product,self){
			available = self.calculate_availability(product)
			tab = product['tab_id']
			product = self.product_ids[product.id]
			qty = parseFloat(product.get_value()) || 0
			if (available >= qty){
				product.set({'availability':true});
			}else{
				product.set({'availability':false});
			}
			return product
		},
		on_check_availability:function(product,self){ //self is tab object
			product.$("input").keydown(function(event){
				if (event.which == 13){
					$.when(self.get_product_information([product.data.id],['virtual_available','incoming_qty','tab_id'])).done(function(data){
						// empty tabs
						if (data){
							_.each(data,function(product){
								product = self.set_availability(product,self.tab_parent.parent);
								if (product.get("availability")){
									self.tab_parent.do_notify("Availability Status:","Available")
								}else{
									self.tab_parent.do_warn("Availability Status:","Not Available")
								}
							})
						}
					});
				}
			});
		},
		should_set_float_value:function(val){
			if (isNaN(val) || val == undefined || typeof(val) == 'string'){
				return false
			}else{
				return true
			}
		},
		set_value:function(widget,val,parent){
			var self = this;
			if (self.should_set_float_value(val)){
				val = val.toFixed(2)
				widget.set_value(val)
			}else{
				parent.do_warn("Invalid Value","")
			}
		},
		calculate_final_money_total:function(){
			var self = this;
			total = 0;
			_.each(self.subtotal_money,function(subtotal){
				val = parseFloat(subtotal.get_value()) || 0;
				total = total + val
			});
			self.final_total_money = total
			self.tab_parent.parent.trigger("subtotal_money_changed",true)
		},
		order_report:function(){
			return
		},
	}
	
local.product_lists = instance.Widget.extend(local.AbstractWidget,{
		init:function(tab_parent,tab_data){
			this._super(tab_parent);
			this.tab_parent = tab_parent;
			this.data = tab_data;
			this.dfm = new instance.web.form.DefaultFieldManager(self);
			this.price = {};
			this.subtotal_money = {} // this is just a holder of subtotal widget
			this.subtotal_qty = {}; // this is just a holder of subtotal widget
			this.final_total_money = 0.00;
			this.final_total_qty = 0
		},

		get_width:function(){
			return this.data.input_width
		},
		
		get_price:function(product){
			return product.lst_price;
		},
		calculate_subtotal_money:function(product_id){
			var self = this;
			price = parseFloat(self.price[product_id].get_value()) || 0;
			qty = parseFloat(self.subtotal_qty[product_id].get_value()) || 0;
			total = price * qty;
			self.set_value(self.subtotal_money[product_id],total,self.tab_parent);
			self.trigger("subtotal_money_widget_changed")
		},
		calculate_subtotal_qty:function(){ //calculate_subtotal_money
			var self = this;
			total = 0;
			_.each(self.subtotal_qty,function(cell){
				total = total + parseFloat(cell.get_value() || 0);
			})
			self.set_value(self.final_subtotal_qty,total,self.tab_parent);
			self.trigger("subtotal_qty_widget_changed",true)
		},
		calculate_final_qty_total:function(data){
			var self = this;
			total = parseFloat(self.final_subtotal_qty.get_value()) || 0
			self.final_total_qty = total;
			self.tab_parent.parent.trigger("subtotal_change",true);
		},				
		
		renderElement:function(){
			var self=this;
			width = self.get_width();
			//Fetch Volume Prices first
			self.$el = $(QWeb.render('products_list',{'tab_style':self.data.tab_style}))
			_.each(self.data.product_ids,function(product){
				$row = $("<tr><td class = 'col-md-3'><strong>%NAME%</strong></td></tr>".replace("%NAME%",product.name))
				// Qty Column
				$col= $("<td></td>")
				widget = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "qty_input_"+remove_spaces(product.name),
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false}',
	                },
	            });
				widget.set({
					"availability":true,
				});
				self.subtotal_qty[product.id] = widget;
				widget.appendTo($col);
				widget.set_dimensions("auto",width);
				$row.append($col);
				widget.on("changed_value",widget,function(event){
					if (self.data.tab_style == 2){
						self.calculate_subtotal_money(product.id)
					}
					self.calculate_subtotal_qty();
				});
				widget.data = product;
				self.on_check_availability(widget,self);
				self.tab_parent.parent.product_ids[product.id] = widget
				widget.on("change:availability",widget,function(widget){
					if (widget.get("availability") == false){
						widget.$el.find("input").css('background-color','red')
					}else{
						widget.$el.find("input").css('background-color','')
					}
				})
				if (self.data.tab_style != 2){
					self.$el.find("#main_body").append($row);
					return
				}
				// Unit price column
				$col = $("<td></td>")
				widget = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "unit_price_input_"+remove_spaces(product.name),
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false}',
	                },
	            });
				self.price[product.id] = widget;
				widget.appendTo($col);
				self.set_value(widget,self.get_price(product),self.tab_parent);
				widget.on("changed_value",widget,function(event){
					self.calculate_subtotal_money(product.id)
				});
				widget.set_dimensions("auto",width)
				$row.append($col);
				
				// Subtotal column
				$col = $("<td></td>")
				widget = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "subtotal_money_input_"+remove_spaces(product.name),
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false,"readonly":true}',
	                },
	            });
				self.subtotal_money[product.id] = widget;
				widget.appendTo($col);
				widget.set_dimensions("auto",width)
				$row.append($col);
				self.$el.find("#main_body").append($row);
			});//end each
			$row = $("<tr class='success'><td><strong>Total Quantity</strong></td></tr>");
			$col = $("<td></td>")
			widget = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "subtotal_qty_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                },
            });
			self.final_subtotal_qty = widget;
			widget.appendTo($col);
			widget.set_dimensions("auto",width)
			$row.append($col);
			self.$el.find("#main_body").append($row);
		},
		order_report:function(){
			var self = this;
			var items = [];
			_.each(self.subtotal_qty,function(product){
				product_id = product.data.id
				qty = parseFloat(product.get_value()) || 0;
				if (qty == 0){
					return
				}
				price = 0;
				if (self.tab_parent.dataset.tab_style == 2){
					price = parseFloat(self.price[product_id].get_value()) || 0;
				}
				discount = 0;
				self.prepare_order_line(items,product_id,qty,price,discount)
			})
			return items
		},
		start:function(){
			var self = this;
			self.on("subtotal_money_widget_changed",self,self.calculate_final_money_total)
			self.on("subtotal_qty_widget_changed",self,self.calculate_final_qty_total)
		},
	})
	
	local.flavor_conc_matrix = instance.Widget.extend(local.AbstractWidget,{
		init:function(tab_parent,tab_data){
			this._super(tab_parent);
			this.tab_parent = tab_parent;
			this.data = tab_data;
			this.product_data = {};
			this.dfm = new instance.web.form.DefaultFieldManager(self);
			this.available_flavors = {};
			this.available_conc = {}
			this.prices = {}; // It will contain flavor key and widget of price
			this.subtotal_money = {}; // It will contain flavor key and widget of subtotals
			this.subtotal_qty = {};// It will contain concentration key and widget of qty total
			this.initialize();
			this.final_total_qty = 0;
			this.final_total_money = 0.00;
		},
		initialize:function(){
			var self = this;
			$.each(self.data.product_ids,function(index,product){
				conc = product.conc_id[0];
				flavor = product.flavor_id[0];
				self.available_flavors[flavor] = product.flavor_id[1];
				self.available_conc[conc] = product.conc_id[1];
				widget = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "qty_input_"+remove_spaces(product.name),
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false}',
	                },
	            });
				widget.set({
					'availability':true,
				});
				widget.data = product;
				self.tab_parent.parent.product_ids[product.id] = widget
				widget.on("change:availability",widget,function(widget){
					if (widget.get("availability") == false){
						widget.$el.find("input").css('background-color','red')
					}else{
						widget.$el.find("input").css('background-color','')
					}
				})
				if ( _.contains(_.keys(self.product_data),String(flavor))){ // if flavor key is present in dictionary
					self.product_data[flavor][conc]=widget
				}else{
					self.product_data[flavor] = {
							[conc]:widget,
						}
				}//end else
			}) // end each
			self.available_flavors = sortProperties(self.available_flavors,'asc');
			self.available_conc = sortProperties(self.available_conc,'desc');
		},
		get_prices:function(){
			return this.tab_parent.parent.prices[this.data.vol_id[0]] || 0; 
		},
		get_width:function(){
			return this.data.input_width
		},
		order_report:function(){
			var self = this;
			var items = [];
			$.each(self.product_data,function(flavor_id,conc_ids){
				price = 0;
				if (self.tab_parent.dataset.tab_style == 1){
					price =parseFloat(self.prices[flavor_id].get_value()) || 0
				}
				_.each(conc_ids,function(conc){
					qty = parseFloat(conc.get_value()) || 0
					if (qty == 0){
						return
					}
					self.prepare_order_line(items,conc.data.id,qty,price,0)
				})//end each
			})
			return items
		},
		
		calculate_subtotal_money:function(flavor_id){
			var self = this;
			qty_total = 0;
			_.each(self.product_data[flavor_id],function(cell){
				qty_total = qty_total  + parseFloat((cell.get_value() || 0))
			})
			price = self.prices[flavor_id].get_value();
			total_value = price*qty_total;
			self.set_value(self.subtotal_money[flavor_id],total_value,self.tab_parent)
			self.trigger("subtotal_money_widget_changed",true)
		},

		calculate_subtotal_qty:function(conc_id){
			var self=this;
			total_qty = 0;
			_.each(self.product_data,function(flavor){
				if (flavor[conc_id]){
					total_qty = total_qty + parseFloat(flavor[conc_id].get_value())
				}
			})
			self.subtotal_qty[conc_id].set_value(total_qty || 0);
			self.trigger("subtotal_qty_widget_changed",true)
		},
		
		calculate_final_qty_total:function(data){
			var self = this;
			total = 0;
			_.each(self.subtotal_qty,function(qty){
				qty = parseFloat(qty.get_value()) || 0;
				total = total + qty;
			});
			self.final_total_qty = total;
			self.tab_parent.parent.trigger("subtotal_change",true);
		},		

		start:function(){
			this.on("subtotal_money_widget_changed",this,this.calculate_final_money_total);
			this.on("subtotal_qty_widget_changed",this,this.calculate_final_qty_total);
			return this._super();
		},
		renderElement:function(){
			var self=this;
			price = self.get_prices();
			width = self.get_width();
			
			//Fetch Volume Prices first
			self.$el = $(QWeb.render('flavor_conc_matrix_table',{"concentration":self.available_conc,'tab_style':self.data.tab_style}))
			$.each(self.available_flavors,function(index_flavor,flavor){
				$row = $("<tr></tr>");
				// * First render the product cells
				$row.append(("<td><strong>%NAME%<strong></td>").replace("%NAME%",flavor[1]))
				$.each(self.available_conc,function(index_conc,conc){
					$col= $("<td></td>")
					if (self.product_data[flavor[0]][conc[0]]){
						self.product_data[flavor[0]][conc[0]].appendTo($col)
						self.product_data[flavor[0]][conc[0]].set_dimensions("auto",width);
						self.product_data[flavor[0]][conc[0]].on("change:value",self.product_data[flavor[0]][conc[0]],function(event){
							if (self.data.tab_style == 1){
								self.calculate_subtotal_money(flavor[0]);
							}
							self.calculate_subtotal_qty(conc[0]);
						});
						self.on_check_availability(self.product_data[flavor[0]][conc[0]],self);
					}
					else{
						widget = new instance.web.form.FieldFloat(self.dfm,{
			                attrs: {
			                    name: "dummy",
			                    type: "float",
			                    context: {
			                    },
			                    modifiers: '{"readonly": true}',
			                },
			            });
						$input = $("<input readonly='1' style='width:%width%'/>".replace("%width%",width))
						widget.appendTo($col)
						widget.$el.find("span.oe_form_char_content").empty().append($input)
						$input.on("keydown",self,widget.navigate_interface)
					} // endif
					$row.append($col)
				}) //end each
				// * Now render the prices and subtotal cells
				if (self.data.tab_style == 1){ // flavor concentration matrix without free samples
					$col_price= $("<td></td>")
					$col_subtotal = $("<td></td>")
					widget_subtotal = new instance.web.form.FieldFloat(self.dfm,{
		                attrs: {
		                    name: "subtotal_money_input",
		                    type: "float",
		                    context: {
		                    },
		                    modifiers: '{"required": false,"readonly":true}',
		                },
		            });
					widget_price = new instance.web.form.FieldFloat(self.dfm,{
		                attrs: {
		                    name: "price_input",
		                    type: "float",
		                    context: {
		                    },
		                    modifiers: '{"required": false}',
		                },
		            });
					self.set_value(widget_price,price,self.tab_parent) 
					widget_price.appendTo($col_price)
					widget_price.set_dimensions("auto",width);
					widget_price.on("changed_value",widget_price,function(event){
						self.calculate_subtotal_money(flavor[0]);
					})
					widget_subtotal.appendTo($col_subtotal)
					widget_subtotal.set_dimensions("auto",width);
					$row.append($col_price)
					$row.append($col_subtotal)
					self.prices[flavor[0]] = widget_price
					self.subtotal_money[flavor[0]] = widget_subtotal
				}
				self.$el.find("#main_body").append($row);
			})//end each				
			// * Now rendering the subtotal_qty widget
			$row = $("<tr class='success'><td><strong>Total Per Strength</strong></td></tr>");
			$.each(self.available_conc,function(index_conc,conc){
				$col = $("<td></td>");
				widget_subtotal_qty = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "subtotal_qty_input",
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false,"readonly":true}',
	                },
	            });
				widget_subtotal_qty.appendTo($col)
				widget_subtotal_qty.set_dimensions("auto",width)
				$row.append($col);
				self.subtotal_qty[conc[0]] = widget_subtotal_qty
			});//end each
			self.$el.find("#main_body").append($row);
		},
	})
	
	local.tab = instance.Widget.extend({
		init:function(parent,class_state,dataset){ //dataset is tab data
			this._super(parent);
			this.tech_tab_name = remove_spaces(dataset.name);
			this.class_state = class_state;
			this.$tab = $(QWeb.render("nav_tabs", {'tab_name':dataset.name,'class_state':class_state,'tech_tab_name':this.tech_tab_name,'tab_id':dataset.id}));
			this.$body = $(QWeb.render("tab_panes", {'tab_name':dataset.name,'class_state':class_state,'tech_tab_name':this.tech_tab_name,'tab_id':dataset.id}));
			this.parent = parent;
			this.dataset = dataset;
		},
		start:function(){
			var self=this;
			var tmp = self._super()
			switch(self.dataset.tab_style){
				case 1://Flavor Concentration Matrix
					var tab_widget = new local.flavor_conc_matrix(self,self.dataset);
					tab_widget.appendTo(self.$body);
					self.tab_widget = tab_widget;
					break;
				case 2://Products List
					var tab_widget = new local.product_lists(self,self.dataset);
					tab_widget.appendTo(self.$body);
					self.tab_widget = tab_widget;
					break;
				case 3: //Marketing
					var tab_widget = new local.marketing_package(self,self.dataset)
					tab_widget.appendTo(self.$body);
					self.tab_widget = tab_widget;
					break;
				case 4: //Free Samples List
					var tab_widget = new local.product_lists(self,self.dataset);
					tab_widget.appendTo(self.$body);
					self.tab_widget = tab_widget;
					break;
				case 5: //Free Samples Matrix
					var tab_widget = new local.flavor_conc_matrix(self,self.dataset);
					tab_widget.appendTo(self.$body);
					self.tab_widget = tab_widget;
					break;
				default:
					break;
			}
		},
		renderElement:function(){
			var self = this;
			self.$tab.appendTo(self.parent.tabs)
			self.$body.appendTo(self.parent.panes)
		}
	});
	
	local.payment_plan_line = instance.Widget.extend({
		template:"payment_plan_line",
		init:function(parent){
			this._super(parent);
			this.parent = parent
			this.dfm = new instance.web.form.DefaultFieldManager(this);
            this.dfm.extend_field_desc({
            	payment_method: {
                    relation: "account.journal",
                },
            });			
			this.payment_method = new instance.web.form.FieldMany2One(this.dfm,{
                attrs: {
                    name: "payment_method",
                    type: "many2one",
                    context: {
                    },
                    modifiers: '{"required": true}',
                }
            });			
			this.amount = new instance.web.form.FieldFloat(this.dfm,{
                attrs: {
                    name: "amount",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": true}',
                }
            });
			this.date = new instance.web.form.FieldDate(this.dfm,{
                attrs: {
                    name: "date",
                    type: "date",
                    context: {
                    },
                    modifiers: '{"required": true}',
                }
            });	
			this.$delete = $("<span class='glyphicon glyphicon-remove-circle'></span>")
		},
		start:function(){
			var self = this;
			self.$delete.on("click",self,function(event){
				self.destroy();
			})
			self.amount.on("change",self,function(event){
				self.parent.trigger("recalculate_total",true);
			});
		},
		
		renderElement:function(){
			var self = this;
			this._super();
			self.payment_method.appendTo(self.$el.find("td#payment_method"))
			self.amount.appendTo(self.$el.find("td#amount"))
			self.date.appendTo(self.$el.find("td#date"))
			self.$el.find("td#delete").append(self.$delete)
		},
		destroy:function(){
			this._super();
			index = this.parent.line.indexOf(this);
			delete this.parent.line[index]
			this.parent.trigger("recalculate_total");
		},
		
	});
	
	local.payment_plan = instance.Widget.extend({
		template:"payment_plan",
		init:function(parent){
			this._super(parent);
			this.line = []
			this.total = 0.00;
			this.parent = parent;
		},
		order_report:function(){
			var self = this;
			items = []
			_.each(self.line,function(line){
				payment_method = line.payment_method.get_value();
				amount = parseFloat(line.amount.get_value()) || 0;
				date = line.date.get_value();
				items.push([0,0,{
					'method_of_payment':payment_method,
					'amount_original':amount,
					'date':date,
				}])
			})
			return items;
		},
		renderElement:function(){
			var self = this;
			self._super();
			self.$add_an_item = $("<tr><td><a href='#'><u>Add an item</u></a></td></tr>") 
			self.$el.append(self.$add_an_item);
		},
		recalculate_total:function(){
			var self = this;
			self.total = 0.00;
			_.each(self.line,function(line){
				self.total = self.total + parseFloat(line.amount.get_value() || 0)
			});
			self.parent.trigger("recalc_balance",true)
		},
		start:function(){
			var self = this;
			self.$add_an_item.on("click",self,function(event){
				line = new local.payment_plan_line(self)
				self.line.push(line);
				line.appendTo(self.$el)
			});
			self.on("recalculate_total",self,self.recalculate_total)
		},
	});
	
	// Main 
	instance.web.form.custom_widgets.add('jjuice', 'instance.jjuice.jjuice_interface_main');
	local.jjuice_interface_main = instance.web.form.FormWidget.extend(local.AbstractWidget,{
    	template:'interface',
    	events:{
    		"click button#rate_request":"execute_rate_request",
    		"click button#check_availability":"execute_check_availability",
    		"click button#confirm":"execute_confirm_order",
    	},
    	init: function(field_manager,node) {
    		this._super(field_manager, node);
    		this.field_manager = field_manager;
    		this.prices = {};
    		this.$prices = $.Deferred();
    		this.dfm = new instance.web.form.DefaultFieldManager(self);
    		this.taxes = [];
    		this.product_ids = {};
		},
		get_order_lines:function(){
			var self= this;
			var lines = [];
			_.each(self.tabs_object,function(tab){
				lines = $.merge(tab.tab_widget.order_report(),lines)
			});
			return lines
		},
		_execute_confirm_order:function(partner_id,lines){
			var self = this;
			var taxes = []
			if (!(parseFloat(self.balance.get_value()) == 0)){
				self.do_warn("Note","You cannot cofirm the under until the balance is 0.");
				return $.Deferred()
			}
			_.each(self.taxes,function(tax){
				if (tax.get_value() == true){
					taxes.push(tax.get("id"));
				}
			})
			var s_h = parseFloat(self.shipping_handling.get_value()) || 0
			var discount_percentage = parseFloat(self.discount_percentage.get_value()) || 0
			var order_notes = self.order_notes.get_value();
			var paid = parseFloat(self.paid.get_value()) || 0
			var payment_plan = self.payment_plan.order_report();
			if (lines.length == 0){
				self.do_warn("Invalid Order","No product Added");
				return $.Deferred()
			}
			payment_method = self.payment_method.get_value();
			result = {
				"partner_id":partner_id,
				"lines":lines,
				"taxes":[[6,0,taxes]],
				"s_h":s_h,
				"discount_percentage":discount_percentage,
				"order_notes":order_notes,
				"paid":paid,
				"payment_plan":payment_plan,
				"payment_method":payment_method,
			}
			tab = new openerp.Model("product.tab");
			return tab.call("create_order",{
				"result":result
			})			
		},
		execute_confirm_order:function(){ //working
			var self = this;
			var partner_id = self.field_manager.datarecord.id;
			var lines = self.get_order_lines();
			self._execute_confirm_order(partner_id,lines).done(function(action_data){
				if (paid > 0){
					data = action_data.res;
					var action = {}
					action = {
    		             'type': 'ir.actions.act_window',
    		             'view_type': 'form',
    		             'res_id':data.res_id,
    		             'view_mode': 'form',
    		             'res_model': 'account.invoice',
    		             'views': [[data.invoice_view_id, 'form']],
    		             'view_id': data.invoice_view_id,
    		             'target': 'current',		    								
					  }
					self.do_action(action).done(function(){
					action = {
							'name':_lt("Pay Invoice"),
							'type': 'ir.actions.act_window',
	    		             'view_type': 'form',
	    		             'view_mode': 'form',
	    		             'res_model': 'account.voucher',
	    		             'views': [[action_data.invoice_info.view_id, 'form']],
	    		             'view_id': action_data.invoice_info.view_id,
	    		             'target': 'new',	
	    		             'context':action_data.invoice_info.context,
						  }
					self.do_action(action)
					}); //
				}else{
					self.do_action(action_data)
				}
			});
		},
		execute_check_availability:function(){ 
			var self = this;
			product_ids = []
			$.each(self.product_ids,function(key,product){
				if (product.get_value() > 0 ){
					product_ids.push(product.data.id)
				}
			});
			product_not_available = []
			$.when(self.get_product_information(product_ids,['virtual_available','incoming_qty','tab_id'])).done(function(data){
				// empty tabs
				if (data){
					_.each(data,function(product){
						product = self.set_availability(product,self);
						if (! product.get("availability")){
							product_not_available.push({
								'name':product.data.name,
								'tab_name': tab[1],
								'available':available,
								'required':qty
							})
						}
					})
				}
				$pop = QWeb.render("product_not_available_list",{"products":product_not_available})
				bootbox.alert($pop,function(){
					return
				})				
			})
		},
		execute_rate_request:function(){
			var self = this;
			self.do_action({
                type: 'ir.actions.act_window',
                res_model: "rate.fedex.request",
                views: [[false, 'form']],
                context:{
                	"default_recipient_id":self.field_manager.datarecord.id
                },
                target: 'new'
			})
		},
		renderTabs:function(){
			var self = this;
			self.tabs = self.$el.find("ul[role='tablist']")
			self.panes = self.$el.find("div.tab-content")
			//Fetch Prices of current customer
			volume_prices_ids = self.field_manager.datarecord.volume_prices
			if (volume_prices_ids.length > 0){
				self.prices = {};
				vol_price = new openerp.Model('volume.prices.line'); 
				vol_price.call('read',{
					'ids':volume_prices_ids,
					'fields':['product_attribute','price']
				}).done(function(prices){
					_.each(prices,function(elem){
						if (elem.product_attribute){
							self.prices[elem.product_attribute[0]]=elem.price; 
						}
					})
					self.$prices.resolve()
				})
			}else{
				self.$prices.resolve()
			}//end if else
			$.when(main_defs,self.$prices).done(function(res){
				self.tabs_object = {}
				self.nmi_journal_id = res.nmi_journal_id;
				self.tabs_data = res.tabs; // Saving Tab data in Main widget
				// Do not required tax widget as of now
//				_.each(res.taxes,function(tax){
//					$row = $("<tr><td><span><strong>%NAME%</strong></span></td></tr>".replace("%NAME%",tax.name))
//					$col = $("<td></td>")
//					var tax_widget = new instance.web.form.FieldBoolean(self.dfm,{
//		                attrs: {
//		                    name: "tax_input",
//		                    type: "boolean",
//		                    context: {
//		                    },
//		                    modifiers: '{"required": false}',
//		                },
//					});
//					tax_widget.appendTo($col);
//					tax_widget.set({
//						'id':tax.id,
//						'amount':tax.amount,
//					});
//					tax_widget.on("change",self,self.tax_changed)
//					$row.append($col);
//					self.$el.find("tbody#taxes").append($row);
//					self.taxes.push(tax_widget)
//				});
				$.each(self.tabs_data ,function(index,tab){
					// Check first if the tab is to be displayed for this customer
					if (!tab.visible_all_customers){
						if (!_.contains(tab.specific_customer_ids,self.field_manager.datarecord.id)){
							return
						}
					}
					// state is a variable that decides whether the tab is by default active or not. In our case by default active is the first tab
					state = false
					if (jQuery.isEmptyObject(self.tabs_object) == true){
						state=true;
					}
					var tab_widget = new local.tab(self,state,tab)
					tab_widget.appendTo(self.$el)
					self.tabs_object[tab.id] = tab_widget;
				})
			}) // end when			
		},
		on_click_nmi_payment_button:function(){
			var self = this;
			// Open the the nmi payment wizard
			var lines = self.get_order_lines();
			var partner_id = self.field_manager.datarecord.id;
			var paid = parseFloat(self.paid.get_value()) || 0;
			if (paid == 0 ){
				self.do_warn("Sorry!","There is no amount to be paid!")
				return					
			}
			if (!(self.balance.get_value()==0)){
				self.do_warn("Note","You cannot move ahead until the balance = 0. Plz create payment plans if needed!")
				return
			}
			if (lines.length == 0){
				self.do_warn("Invalid Order","No product Added");
				return
			}
			bootbox.confirm({
			    message: "Are you sure you want to generate invoice and proceed with the payment ?",
			    buttons: {
			        confirm: {
			            label: 'Yes',
			            className: 'btn-success'
			        },
			        cancel: {
			            label: 'No',
			            className: 'btn-danger'
			        }
			    },
			    callback: function (result) {
			    	if (result){
			    		self.$el.find("button#confirm").remove();
						self._execute_confirm_order(partner_id,lines).done(function(action_data){
							var invoice_id = action_data.res.res_id;
							var wizard_model = new openerp.web.Model('nmi.payment.wizard') 
							wizard_model.call('create'
							,[{'partner_id':partner_id,'invoice_id':invoice_id,'register_payment':true}]).done(function(res_id){
								wizard_model.call('onchange_partner_id',[[res_id],{}]).done(function(){
									var data = {
							                type: 'ir.actions.act_window',
					    		            views: [[false, 'form']],
					    		            res_id:res_id,
							                res_model: "nmi.payment.wizard",
							                context:{
							                	"read_partner_id":true,
							                	"read_invoice_id":true,
							                },
							                target: 'new',
										}
									function on_close(){
										var data = action_data.res;
										self.do_action({
					    		             'type': 'ir.actions.act_window',
					    		             'view_type': 'form',
					    		             'res_id':data.res_id,
					    		             'view_mode': 'form',
					    		             'res_model': 'account.invoice',
					    		             'views': [[data.invoice_view_id, 'form']],
					    		             'view_id': data.invoice_view_id,
					    		             'target': 'current',		    								
										  },{clear_breadcrumbs: true})
									}
									
									self.do_action(data,{
										'on_close':on_close,
									})												
								})
							})				    		
						})
						
			    	} // end bootbox if
			    }
			});				
		},
		renderElement:function(){
			var self = this;
			console.log("renderElement")
			if (! self.field_manager.datarecord.id){
				return // This means we are creating a record. So do not render anything then
			}
			self._super();
			self.renderTabs();
			$body = self.$el.find("tbody#main_body")
			self.confirm_dialogue = self.$el.find("div#confirm")
			self.nmi_payment_button = $body.find('button#nmi_payment_button');
			self.nmi_payment_button.on('click',function(){
				self.on_click_nmi_payment_button();
			})
			
			self.total_units = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "total_unit_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                },
            });
			self.total_units.appendTo($body.find('td#total_units'))
			self.subtotal = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "subtotal_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                },
            });
			self.subtotal.appendTo($body.find('td#subtotal'))
			
			self.shipping_handling = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "s_h_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            });
			self.shipping_handling.appendTo($body.find("#s_h"))
			self.shipping_handling.on("change",self,self.trigger_recalculate);
				 
			self.order_notes = new instance.web.form.FieldText(self.dfm,{
                attrs: {
                    name: "order_notes_input",
                    type: "text",
                    placeholder:"Order Notes",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            });
			self.order_notes.appendTo($body.find("#order_notes"))
			
			self.discount_percentage = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "discount_percentage_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            });
			self.discount_percentage.appendTo($body.find("#discount_percentage"))
			self.discount_percentage.on("change",self,self.changed_discount);
			
			self.discount = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "discount_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            });
			self.discount.appendTo($body.find("#discount"))
			self.discount.on("change",self,self.changed_discount);
			
			self.tax_value = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "tax_input",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                }
            });
			self.tax_value.appendTo($body.find("td#tax_value"))
			self.total = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "total",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                }
            });
			self.total.appendTo($body.find("td#total"))			
			self.paid = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "paid",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false}',
                }
            });
			self.paid.appendTo($body.find("td#paid"))						
			self.paid.on("change",self,function(){self.trigger("recalc_balance",true)});
			self.balance = new instance.web.form.FieldFloat(self.dfm,{
                attrs: {
                    name: "balance",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false,"readonly":true}',
                }
            });
			self.balance.appendTo($body.find("td#balance"))
            
			self.dfm.extend_field_desc({
            	payment_method: {
                    relation: "account.journal",
                },
            });			
			self.payment_method = new instance.web.form.FieldMany2One(this.dfm,{
                attrs: {
                    name: "payment_method",
                    type: "many2one",
                    context: {
                    },
                    modifiers: '{"required": true}',
                }
            });	
			self.payment_method.appendTo($body.find("td#payment_method"))
			self.payment_method.on("change",self,self.changed_payment_method);
			
			self.payment_plan = new local.payment_plan(self);
			self.payment_plan.appendTo($body.find("td#payment_plans"))
		},
		trigger_recalculate:function(){
			var self = this;
			self.trigger("recalc_discount",self.discount_percentage)
			self.trigger("recalc_tax",true)
			self.trigger("recalc_total",true);
		},
		subtotal_changed:function(event_data){
			var self = this;
			total = 0;
			_.each(self.tabs_object,function(tab){
				total = total + tab.tab_widget.final_total_qty;
			});
			self.set_value(self.total_units,total,self)
		},		
		subtotal_money_changed:function(){
			var self = this;
			total = 0;
			_.each(self.tabs_object,function(tab){
				total = total + tab.tab_widget.final_total_money;
			});
			self.set_value(self.subtotal,total,self)
			self.trigger_recalculate();
		},
		tax_changed:function(tax){
			var self=this;
			amount = 0
			subtotal = parseFloat(self.subtotal.get_value()) || 0;
			s_h = parseFloat(self.shipping_handling.get_value()) || 0;
			subtotal = subtotal + s_h;
			discount = parseFloat(self.discount.get_value()) || 0;
			taxable_amount = subtotal - discount
			_.each(self.taxes,function(tax){
				tax_amount = tax.get("amount");
				if (tax.get_value()){
					amount = amount +  taxable_amount * tax_amount
				}//end if
			}); //end each
			self.set_value(self.tax_value,amount,self)
			self.trigger("recalc_total",true);
		},
		changed_payment_method:function(field){
			var self = this;
			console.log(field);
			if (self.nmi_journal_id && self.nmi_journal_id == field.get_value()){
				self.nmi_payment_button.show().slideDown('slow');
				return
			}
			self.nmi_payment_button.hide().slideUp('slow');
		},
		changed_discount:function(field){
			var self = this;
			if (field.field_manager.eval_context.stop){
				return
			}
			field.field_manager.eval_context.stop = true;
			if (field.name == "discount_percentage_input"){
				discount_percentage = parseFloat(field.get_value()) || 0
				subtotal = parseFloat(self.subtotal.get_value()) || 0;
				s_h = parseFloat(self.shipping_handling.get_value()) || 0;
				subtotal = subtotal + s_h;
				discount = (discount_percentage * subtotal)/100;
				self.set_value(self.discount,discount,self)
				
			}else if (field.name == "discount_input"){
				discount = parseFloat(field.get_value()) || 0;
				subtotal = parseFloat(self.subtotal.get_value()) || 0;
				s_h = parseFloat(self.shipping_handling.get_value()) || 0;
				subtotal = subtotal + s_h;
				if (subtotal != 0){
					discount_percentage = (discount/subtotal)*100;
					self.set_value(self.discount_percentage,discount_percentage,self)
				}
			}
			field.field_manager.eval_context.stop = false;
			self.trigger("recalc_tax",true)
			self.trigger("recalc_total",true);
		},		
		recalculate(event_data){
			var self = this;
			subtotal = parseFloat(self.subtotal.get_value()) || 0;
			shipping_handling = parseFloat(self.shipping_handling.get_value()) || 0;
			discount = parseFloat(self.discount.get_value()) || 0;
			tax_value = parseFloat(self.tax_value.get_value()) || 0;
			total = subtotal + shipping_handling - discount + tax_value
			self.set_value(self.total,total,self)
			self.trigger("recalc_balance",true)
		},
		recalculate_balance:function(event){
			var self = this;
			paid = parseFloat(self.paid.get_value()) || 0;
			total = parseFloat(self.total.get_value()) || 0;
			plan_total = self.payment_plan.total || 0;
			balance = total - paid - plan_total;
			self.set_value(self.balance,balance,self)
		},
		start:function(){
			var self = this;
			console.log("start")
			self.on("subtotal_change",self,self.subtotal_changed)
			self.on("subtotal_money_changed",self,self.subtotal_money_changed)
			self.on("recalc_total",self,self.recalculate);
			self.on("recalc_tax",self,self.tax_changed);
			self.on("recalc_discount",self,self.changed_discount);
			self.on("recalc_balance",self,self.recalculate_balance);
			self.field_manager.on("change",self,function(event){
				/*
				 * The view is not refreshed when we change the partner record. For that if we detect a change in field manager,
				 * we empty the $el of the parent and render according the new customer record
				 */
				console.log("changed")
				self.$el.empty();
				self.$prices = $.Deferred()
				self.renderElement();
			});			
		}
	});
}