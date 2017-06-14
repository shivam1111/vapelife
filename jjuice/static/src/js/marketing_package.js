openerp.jjuice.marketing_package = function(instance,local){
	
	var _t = instance.web._t,
    _lt = instance.web._lt;
	var QWeb = instance.web.qweb;
	instance.web.jjuice = instance.web.jjuice || {};	
	
	/**
	 * This tiny script just helps us demonstrate
	 * what the various example callbacks are doing
	 */
	
	local.marketing_pakcage_wizard = instance.Widget.extend({
		template:"products_list",
		init:function(parent){
			this._super(parent);
			this.parent = parent;
			console.log(parent);
			this.tab_style = this.parent.parent.data.tab_style;
			this.fields = ['qty','price','discount']
			this.subtotal = {} // line id: subtotal
		},
		recalculate_subtotal:function(line){
			var self = this;
			console.log(line);
			subtotal_field = self.subtotal[line.id];
			qty = parseFloat(line.qty) || 0;
			price = parseFloat(line.price) || 0;
			discount = parseFloat(line.discount) || 0;
			subtotal = (qty * price)*((100.00-discount)/100.00);
			subtotal = subtotal.toFixed(2)
			line.subtotal = subtotal;
			subtotal_field.set_value(subtotal)
			self.trigger("recalculate_final_total",true)
		},
		recalculate_final_total:function(line){
			var self = this;
			total = 0;
			_.each(self.subtotal,function(cell){
				subtotal = parseFloat(cell.get_value()) || 0;
				total = total + subtotal;
			});
			self.final_total.set_value(total)
			self.parent.data.total = total;
		},
		renderElement:function(){
			var self = this;
			this._super();

			_.each(self.parent.line_ids,function(line){
    			console.log(line);
    			$row = $("<tr><td><strong>%NAME%</strong></td></tr>".replace("%NAME%",line.name))
				_.each(self.fields,function(field){
					$col = $("<td></td>")
					widget = new instance.web.form.FieldFloat(self.parent.dfm,{
		                attrs: {
		                    name: field+remove_spaces(line.name),
		                    type: "float",
		                    context: {
		                    },
		                    modifiers: '{"required": false}',
		                },
		            });
					widget.set_value(line[field])
	    			widget.on("change:value",widget,function(){
	    				value = this.get_value();
	    				if (widget.is_valid()){
	    					line[field] = value;
	    				}
	    				self.trigger("recalculate_subtotal",line)
	    			})
	    			widget.appendTo($col);
					$row.append($col);
				})//end each
				subtotal = new instance.web.form.FieldFloat(self.parent.dfm,{
		                attrs: {
		                    name: remove_spaces(line.name),
		                    type: "float",
		                    context: {
		                    },
		                    modifiers: '{"required": false}',
		                },
	            });
				
				$col = $("<td></td>");
				subtotal.appendTo($col)
				self.subtotal[line.id] = subtotal;
				subtotal.set_value(line.subtotal)
				$row.append($col)
				self.$el.find("#main_body").append($row);
    		})//end each
    		$row = $("<tr class='danger'><td>Total</td><td></td><td></td><td></td></tr>")
    		$col = $("<td></td>");
			self.final_total = new instance.web.form.FieldFloat(self.parent.dfm,{
                attrs: {
                    name: "final_total",
                    type: "float",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            });
			self.final_total.appendTo($col)
			$row.append($col)
			self.final_total.set_value(self.parent.data.total);
    		self.$el.find("#main_body").append($row);
    		self.on("recalculate_subtotal",self,self.recalculate_subtotal)
    		self.on("recalculate_final_total",self,self.recalculate_final_total)
    		
		},
	});
	
	local.marketing_package_line = instance.Widget.extend({
		init:function(parent,record){
			this._super(parent);
			this.name = record.name;
			this.id = record.id;
			this.parent = parent;
			this.data = record;
			this.dfm = new instance.web.form.DefaultFieldManager(self);
			this.line_ids = record.line_ids;
			this.set({
                'total': record.total.toFixed(2) || 0 ,
                'unit_total': record.total.toFixed(2) || 0,
                'qty':1,
                'select':false
            });
		},
    	renderElement:function(){
    		var self = this;
    		var $document= $(QWeb.render("marketing_package_line", {
                "name": self.name,
                "total":self.get('total'),
                "qty":self.get('qty'),
            }));
    		self.$el = $document
    		self.$el.find('button').bind("click",function(event){
    			self.openWindow();
    		})
    	},
    	openWindow:function() {
    		var self = this;
    		var wizard = new local.marketing_pakcage_wizard(self)
    		wizard.renderElement();

    		bootbox.dialog({
    			  message: wizard.$el,
    			  size: "large",
    			  title: self.name,
    			  animate:true,
    			  buttons: {
    			    success: {
    			      label: "OK",
    			      className: "btn-success",
    			      callback: function(trial) {
    			    	  final_total = wizard.final_total.get_value()
    			    	  self.set({"unit_total":final_total});
    			      }
    			    }
    			  }
    		})
    	},

    	calculate_total:function(){
    		var self = this
			total = (self.get('qty') || 0) * (self.get('unit_total') || 0)
    		self.set({'total':total.toFixed(2)});
			self.$el.find('input#subtotal_marketing').attr("value",self.get('total'));
			self.parent.trigger("subtotal_money_widget_changed",true)
    	},
    	
    	start:function(){ //working
			var self = this;
    		this._super();
    		//on change qty
    		self.on('change:qty',self,function(event){
    			self.calculate_total();
				
    		});
    		//on change select
    		self.on('change:select',self,function(event){
    			if (self.get('select')){
    				self.calculate_total();
    			}else{
    				self.set({'total':0})
					self.parent.trigger("subtotal_money_widget_changed",true)
    			}
    		})
    		//on change total
    		self.on('change:unit_total',self,function(event){
    			self.calculate_total();
				self.$el.find('input#subtotal_marketing').attr("value",self.get('total'));
    		});
    		self.$el.change(function(event){
    			self.set({
						 'qty': parseFloat(self.$el.find('input#qty').val()),
						 'select':self.$el.find('input#select').is(":checked")
    				})
    		});
		},
	});	
	
	local.marketing_package = instance.Widget.extend(local.AbstractWidget,{
		init:function(tab_parent,tab_data){
			this._super(tab_parent);
			this.tab_parent = tab_parent;
			this.data = tab_data;
			this.price = {};
			this.discount = {};
			this.marketing_package_widget = {}
			this.dfm = new instance.web.form.DefaultFieldManager(self);
			this.subtotal_money = {}; // It will contain flavor key and widget of subtotals
			this.subtotal_qty = {};// product_id:widget
			this.final_total_qty = 0;
			this.final_total_money = 0.00;			
		},
		get_width:function(){
			return this.data.input_width
		},
		
		get_price:function(product){
			return product.lst_price;
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
		
		calculate_subtotal_money:function(product_id){
			var self = this;
			price = parseFloat(self.price[product_id].get_value()) || 0;
			qty = parseFloat(self.subtotal_qty[product_id].get_value()) || 0;
			discount = parseFloat(self.discount[product_id].get_value()) || 0;
			discount = 1 - (discount/100)
			total = (price * qty) * discount;
			self.set_value(self.subtotal_money[product_id],total,self.tab_parent);
			self.trigger("subtotal_money_widget_changed")
		},
		renderElement:function(){
			var self=this;
			width = self.get_width();
			$widget_render =  $(QWeb.render('marketing_package',{}))
			self.$el.append($widget_render) 
			//marketing packages
			_.each(self.data.marketing_packages_ids,function(package_id){
				widget = new local.marketing_package_line(self,package_id)
				widget.appendTo(self.$el.find("tbody#package_body"));
				self.marketing_package_widget[package_id.id] = widget;
				widget.data = package_id
			});
			$body = $(QWeb.render('products_list',{'tab_style':self.data.tab_style}))
			self.$el.append($body)
			_.each(self.data.product_ids,function(product){
				$row = $("<tr><td><strong>%NAME%</strong></td></tr>".replace("%NAME%",product.name))
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
					self.calculate_subtotal_money(product.id)
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
				self.$el.find("#main_body").append($row);
				
				// Discount% column
				$col = $("<td></td>")
				widget = new instance.web.form.FieldFloat(self.dfm,{
	                attrs: {
	                    name: "discount_"+remove_spaces(product.name),
	                    type: "float",
	                    context: {
	                    },
	                    modifiers: '{"required": false}',
	                },
	            });
				self.discount[product.id] = widget;
				widget.appendTo($col);
				self.set_value(widget,0,self.tab_parent);
				widget.on("changed_value",widget,function(event){
					self.calculate_subtotal_money(product.id)
				});
				widget.set_dimensions("auto",width)
				$row.append($col);
				
				//Subtotal Column
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
			}) //end each
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
			items = []
			_.each(self.subtotal_qty,function(product){
				product_id = product.data.id;
				qty = parseFloat(product.get_value()) || 0
				if (qty == 0){
					return
				}
				price = parseFloat(self.price[product_id].get_value()) || 0
				discount = parseFloat(self.discount[product_id].get_value()) || 0
				self.prepare_order_line(items,product_id,qty,price,discount)
			});
			//marketing packages
			_.each(self.marketing_package_widget,function(packages){
				if (packages.get("select") == true){
					_.each(packages.line_ids,function(line){
						self.prepare_order_line(items,line.product_id,line.qty,line.price,line.discount)
					});					
				}
			})
			return items
		},
		calculate_final_qty_total:function(data){
			var self = this;
			total = parseFloat(self.final_subtotal_qty.get_value()) || 0
			self.final_total_qty = total;
			self.tab_parent.parent.trigger("subtotal_change",true);
		},				
		calculate_final_money_total:function(){
			var self = this;
			total = 0;
			_.each(self.subtotal_money,function(subtotal){
				val = parseFloat(subtotal.get_value()) || 0;
				total = total + val
			});
			// addition of subtotal of marketing widgets
			_.each(self.marketing_package_widget,function(packages){
				if (packages.get("select") == true){
					final_total = parseFloat(packages.get("total"))|| 0
					total = total + final_total					
				}
			})
			self.final_total_money = total
			self.tab_parent.parent.trigger("subtotal_money_changed",true)
		},
		start:function(){
			var self = this;
			self.on("subtotal_money_widget_changed",self,self.calculate_final_money_total)
			self.on("subtotal_qty_widget_changed",self,self.calculate_final_qty_total)
		},
	});	

};