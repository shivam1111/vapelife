openerp.jjuice= function (instance,local) {
    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    instance.web.jjuice = instance.web.jjuice || {};
    
// Filter customer wizard button *******************************************************************
    instance.web.views.add('open_filter_wizard_customer','instance.web.jjuice.openp_filter_wizard');
    instance.web.jjuice.openp_filter_wizard = instance.web.ListView.include({
    	do_search:function(domain, context, group_by){
    		var self = this;
            this.last_domain = domain;
            this.last_context = context;
            this.last_group_by = group_by;
            this.old_search = _.bind(this._super, this);
            return self.search_customer();
    	},
    	search_customer:function(){
            var self = this;
            domain = []
            /* If the last_context has the param:
             * 'search_default_leads'   -> This means the menu item is a Leads/Potential Customer
             * 'seach_default_customer' -> This means the menu item is a Customer Menu
             */
            if (self.last_context){
                if ('search_default_leads' in self.last_context){
                	domain = [['leads','=',true]]
                }else if ('search_default_customer' in self.last_context){
                	domain = [['customer','=',true]]
                }            	
            }
            if (self.res){
            	domain.push(['id','in',self.res]);
            }
        	var compound_domain = new instance.web.CompoundDomain(self.last_domain, domain);
            self.dataset.domain = compound_domain.eval();
            return self.old_search(compound_domain, self.last_context, self.last_group_by);            	            	    	
    	},
    	load_list:function(){
    		var self=this;
    		var tmp = this._super.apply(this, arguments);
    		// if filter:True is passed in action context only then display the button
    		if (self.options && self.options.action && self.options.action.context && self.options.action.context.filter){
	    		if (this.model && this.model == 'res.partner'){
					$button = $(QWeb.render("group_expand",{'name':'Filter Customers'}))
		            if ($("button[name = 'group_expand']").length == 0){
		                $('div.oe_list_buttons').append($button);            	
		            }
		    		$button.click(function(e){
		    			// open the filter wizard and display the customer accordingly
		    			var view_id= new instance.web.Model("ir.model.data");
		    			var wizard = new instance.web.Model("customer.filter.wizard")
		    			wizard.call('create',[{}]).done(function(id){
			        		view_id.call('get_object_reference',['jjuice','customer_filter_wizard_form']).done(function(view_id){
			    			var action = {};
			    			action = {
			    	             'type': 'ir.actions.act_window',
			    	             'view_type': 'form',
			    	             'view_mode': 'form',
			    	             'res_model': 'customer.filter.wizard',
			    	             'res_id':id,
			    	             'views': [[view_id[1], 'form']],
			    	             'view_id': view_id[1],
			    	             'target': 'new',
			    	             'context':{'jjuice':true} // This context is paased so that only volume product.attrbute.values are shown. Check in file product.py
			    	               };
			    				var options = {}
			    				options.on_close = function(){
			    					wizard.call('filter_customers',[[id],{'javascript':true}]).done(function(res){
			    						self.res=res;
			    						if (res.length == 0){
			    							alert('Sorry! No records match your search criteria')
			    							return
			    						}
			    						self.do_search(self.last_domain, self.last_context, self.last_group_by);            	            	
			    					});
			    				}
			    				self.do_action(action,options)
		    				})
		        		});
	    			})				
				}
    		}
    	}
    })
// Filter customer wizard button *******************************************************************
    
    instance.web.views.add('tree_group_expand', 'instance.web.jjuice.group_expandView');
    instance.web.jjuice.group_expandView = instance.web.ListView.extend({
        init: function() {
        this._super.apply(this, arguments);
        var self = this;
        },
        load_list: function() {
            var self = this;
            var tmp = this._super.apply(this, arguments);
            $button = $(QWeb.render("group_expand", {'name':'Expand/Collapse'}));
            if ($("button[name = 'group_expand']").length == 0){
                $('div.oe_list_buttons').append($button);            	
            }
            $button.click(function(e){
            	$('tr.oe_group_header').click();
        	})
        }
    });	

//======================================================================================================
    
	get_perm = function(conc_id,rows){
		if ($.inArray(conc_id,rows.conc_id) > -1){
			return true;
		}
		else {
			return false;
		}
	}
    
    var context = {'marketing_package':[],'marketing':[],'extra':[],'misc':[],'page':[],'vols':[],'conc_id_internal' :[],'get_perm':get_perm,'employ':[],'price':false,'free_attr':0,'free_attr_name':""}
	var vol_id = new instance.web.Model("ir.model.data");
	vol_id.call('get_object_reference',['jjuice','attribute_vol']).done(function(vol){
		var vol_ids = new instance.Model('product.attribute.value');
		vol_ids.query(['name','id']).filter([['attribute_id','=',vol[1]]]).all().then(function(vol_records){
			vol_records.forEach(function(records){
				context.page.push({'id':records.id,'name':records.name});
			});
			var dict_values = new instance.web.Model("product.product");
			dict_values.call('get_values_product_vol_tax',[context.page]).done(function(records){
				records.extra.forEach(function(sample){
					context.extra.push(sample)
				});
				context.tax = records.taxes;
				context['free_attr'] = records['vol_id'];
				context['free_attr_name'] = records['vol_name'];
				records.normal.forEach(function(vol_info){
					context.vols.push(vol_info);
				});
				records.misc.forEach(function(misc_product){
					context.misc.push(misc_product)
				});
				records.marketing.forEach(function(marketing_product){
					context.marketing.push(marketing_product)
				});				
				var marketing_package = new instance.web.Model("marketing.package");
				marketing_package.call('search',[[['active','=',true]]]).then(function(results){
					marketing_package.call('get_marketing_package',[results]).then(function(res){
						context.marketing_package = res
					});					
				})
				var conc_id = new instance.web.Model("ir.model.data");
	    		vol_id.call('get_object_reference',['jjuice','attribute_conc']).done(function(conc){
	    			var conc_ids = new instance.Model('product.attribute.value');
	    			conc_ids.query(['name','id']).filter([['attribute_id','=',conc[1]]]).all().then(function(conc_records){
	    				conc_records.forEach(function(conc){
	    					context.conc_id_internal.push(conc);
	    				});
	    			});
	    		});
			});
		});
	});

//======================================================================================================	
	
//======================Widget for marketing package start================================================
	instance.web.jjuice.marketing_package_widget = instance.Widget.extend({
		init:function(parent,record){
			this._super(parent);
			this.name = record.name;
			this.id = record.id;
			this.line_ids = record.line_ids;
			this.set({
                'total': record.total ,
                'unit_total': record.total,
                'qty':1,
                'select':false
            });
		},
    	renderElement:function(){
    		var self = this;
    		var $document= $(QWeb.render("marketing_package", {
                "name": self.name,
                "total":self.get('total'),
                "qty":self.get('qty'),
            }));
    		self.$el = $document
    		self.$el.find('button').bind("click",function(event){
    			self.openWindow();
    		})
    	},
    	on_close:function(){
    		this.reload_values();
    	},
    	openWindow:function() {
    		var self = this;
			var view_id= new instance.web.Model("ir.model.data");
    		view_id.call('get_object_reference',['jjuice','marketing_package_view_form2']).done(function(view_id){
			var action = {};
			action = {
	             'type': 'ir.actions.act_window',
	             'view_type': 'form',
	             'res_id':self.id,
	             'view_mode': 'form',
	             'res_model': 'marketing.package',
	             'views': [[view_id[1], 'form']],
	             'view_id': view_id[1],
	             'target': 'new',
	             'context':{'invisible':false}
	               };
				wizard_click_widget = self.id;
				self.do_action(action,self)
    		});    		
    	},

    	calculate_total:function(){
    		var self = this
    		if (self.get('select')){
    			total = (self.get('qty') || 0) * (self.get('unit_total') || 0)
    		}else{
    			total = 0
    		}
    		self.set({'total':total.toFixed(2)});
    	},
    	
    	reload_values:function(){
			var self = this;
    		var marketing_package = new instance.web.Model("marketing.package");
			marketing_package.call('get_marketing_package',[self.id]).done(function(result){
			self.reinitialize(result[0])
			});
    	},
    	
    	reinitialize:function(record){
			this.name = record.name;
			this.id = record.id;
			this.line_ids = record.line_ids;
			qty = this.get('qty')
			this.set({
                'total': record.total * qty ,
                'unit_total': record.total,
            });			    		
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
    			}
    		})
    		//on change total
    		self.on('change:total',self,function(event){
				self.$el.find('input#subtotal_marketing').attr("value",self.get('total'));
				self.trigger("total_changed",false,self);
    		});
    		self.$el.change(function(event){
    			self.set({
						 'qty': parseFloat(self.$el.find('input#qty').val()),
						 'select':self.$el.find('input#select').is(":checked")
    				})
    		});
		},
	})
	
	
//======================Widget for marketing package end==================================================
	instance.web.form.custom_widgets.add('jjuice', 'instance.jjuice.action');
	instance.jjuice.action = instance.web.form.FormWidget.extend({
    	init: function(field_manager, node) {
    		this._super(field_manager, node);
    		this.field_manager_arr = [];
    		this.parent = parent;
    		this.index = 0;
    		this.price = 0;
    		this.total = 0.00;
    		this.subtotal = 0.00;
    		this.marketing_package = [] ;
    		this.product_availability = {};
    		this.create_right_fields = {
    				paid: {
    	                id: "paid",
    	                index: 5,
    	                corresponding_property: "paid",
    	                label: _t("Paid"),
    	                required: true,
    	                tabindex: 10,
    	                constructor: instance.web.form.FieldFloat,
    	                field_properties: {
    	                    string: _t("Paid"),
    	                    type: "float",
    	                },
    	            },
		            balance: {
		                id: "balance",
		                index: 5,
		                corresponding_property: "balance",
		                label: _t("Balance"),
		                required: true,
		                tabindex: 10,
		                constructor: instance.web.form.FieldFloat,
		                field_properties: {
		                    string: _t("Balance"),
		                    type: "float",
		                },
	            },   		
                method_of_payment: {
                    id: "method_of_payment",
                    index: 5,
                    corresponding_property: "method_of_payment", // a account.move field name
                    label: _t("Method"),
                    required: true,
                    tabindex: 10,
                    constructor: instance.web.form.FieldMany2One,
                    field_properties: {
                    	relation: "account.journal",
                        string: _t("Method"),
                        type: "many2one",
                        domain: [['type','in',['cash', 'bank']]],
                    },
                },
    		};
    		this.create_form_fields = {
                date: {
                    id: "date",
                    index: 5,
                    corresponding_property: "date", // a account.move field name
                    label: _t("Date"),
                    required: true,
                    tabindex: 10,
                    constructor: instance.web.form.FieldDate,
                    field_properties: {
                        string: _t("Date"),
                        type: "date",
                    },
                },
	            amount: {
	                id: "amount",
	                index: 5,
	                corresponding_property: "amount",
	                label: _t("Amount"),
	                required: true,
	                tabindex: 10,
	                constructor: instance.web.form.FieldFloat,
	                field_properties: {
	                    string: _t("Amount"),
	                    type: "float",
	                },
	            },
                method_of_payment: {
                    id: "method_of_payment",
                    index: 5,
                    corresponding_property: "method_of_payment", // a account.move field name
                    label: _t("Method"),
                    required: true,
                    tabindex: 10,
                    constructor: instance.web.form.FieldMany2One,
                    field_properties: {
                    	relation: "account.journal",
                        string: _t("Method"),
                        type: "many2one",
                        domain: [['type','in',['cash', 'bank']]],
                    },
                },
    		
    		};   
    	},
    	extract_packages:function(packages){
    		var self = this;
    		_.each(self.marketing_package,function(p){
				if (p.get('select')){
					packages.push({
						'id':p.id,
						'name':p.name,
						'line_ids':p.line_ids,
						'qty':p.get('qty'),
					})					
				}
			})
    	},
    	
    	extract_info_input_record:function(list,input_records){
			for (i = 0; i<input_records.length;i++){
				if (input_records[i].extra == true){
					list.push({'id':parseInt($(input_records[i].record).attr('id')),'extra':true,'qty':parseFloat($(input_records[i].record).val()),'price':0,'class_list':input_records[i].record.parentNode.classList})
				}
				else if (input_records[i].misc == true){
					list.push({'id':parseInt(input_records[i].record.attributes[4].nodeValue),'misc':true,'qty':parseFloat($(input_records[i].record).val()),'price':input_records[i].price})
				}
				else if (input_records[i].marketing == true){
					list.push({'discount':parseFloat(input_records[i].discount),'id':parseInt(input_records[i].record.attributes[4].nodeValue),'marketing':true,'qty':parseFloat($(input_records[i].record).val()),'price':input_records[i].price})
				}				
				else {
					list.push({'misc':false,'qty':$(input_records[i].record).val(),'price':input_records[i].price,'class_list':input_records[i].record.parentNode.classList})					
				}
			}
    	},
		
    	next:function(index,input_records,id,def,paid_line,discount_rate,tax_rate){
			var self = this;
			list = [];
			self.extract_info_input_record(list, input_records)
			//Pushing marketing packages
			packages  = []
			self.extract_packages(packages)
    		var product = new instance.web.Model("product.product");
    		product.call('create_sale_order',[list,id,paid_line,discount_rate,tax_rate,packages]).then(function(product_array){
    					def.resolve({'id':id,'paid_line':paid_line})
    		});			
			return true
		},
		
		calculate_amount_tax:function(event){
			sub_total = parseFloat($("input#total_without_tax").val());
			if ($(event.srcElement).attr('id') == 'discount'){
				discount = parseFloat($("#discount").val())
				discount_rate = ((discount*100)/sub_total).toFixed(2);
				$("#discount_rate").val(discount_rate);
			}else{
				discount_rate = parseFloat($("#discount_rate").val());
				discount = (sub_total * discount_rate)/100;				
				$("input#discount").val(discount.toFixed(2));
			}

			sub_total = sub_total - discount;
			tax_check = document.querySelectorAll("input[name='tax'][type='checkbox']:checked");
			var tax_rate = 0
			amount_after_tax = sub_total;
			if (tax_check.length > 0 ){
				_.each (tax_check,function(tax){
					factor = 1+parseFloat($(tax).val());
					amount_after_tax = amount_after_tax*factor;
				});				
			}
			tax = amount_after_tax - sub_total;
			final_amount = sub_total + tax  + parseFloat($("#shipping").val()) ;
			$("input#main_total").val(final_amount.toFixed(2));
			
			$("input#tax").val(tax.toFixed(2));
			
		},
		
		total_strength:function(){
			total_strength = 0;
			_.each($("input#qty_total"),function(record){
				if(! isNaN(parseInt($(record).val()))){
					total_strength = total_strength + parseInt($(record).val()); 
				}
			});
			$("input#total_strength").val(total_strength);
		},
		
		calculate_quantity:function(event){
			var self = this;
			qty_total = 0;
			if ($(event.srcElement).attr('attribute') == 'extra' && $(event.srcElement).hasClass('qty')){
				_.each($("input[attribute='extra'][conc="+$(event.srcElement).attr('conc')+"].qty.jjuice"),function(qty){
					if (! isNaN(parseFloat($(qty).val()))){
						qty_total = qty_total + parseFloat($(qty).val())
					}
				});			
				$("input#qty_total[name = 'extra'][conc='"+$(event.srcElement).attr('conc')+"']").val(qty_total);
			}
			if ($(event.srcElement).attr('attribute') == 'misc' && $(event.srcElement).hasClass('qty')){
				_.each($("input[attribute='misc'].qty"),function(qty){
					if (! isNaN(parseFloat($(qty).val()))){
						qty_total = qty_total + parseFloat($(qty).val());
					}
				});
				$("input#qty_total[name = 'misc']").val(qty_total);
			}
			if ($(event.srcElement).attr('attribute') == 'marketing' && $(event.srcElement).hasClass('qty')){
				_.each($("input[attribute='marketing'].qty"),function(qty){
					if (! isNaN(parseFloat($(qty).val()))){
						qty_total = qty_total + parseFloat($(qty).val());
					}
				});
				$("input#qty_total[name = 'marketing']").val(qty_total);
			}			
			else{
				_.each($("input[name='charge'][conc="+$(event.srcElement).attr('conc')+"][vol="+$(event.srcElement).attr('vol')+"].qty.jjuice"),function(record){
					if (! isNaN(parseFloat($(record).val()))){
						qty_total = qty_total + parseFloat($(record).val());					
					}
				});
				$(event.srcElement).parent().parent().parent().find("input#qty_total[conc="+$(event.srcElement).attr('conc')+"][vol="+$(event.srcElement).attr('vol')+"]").val(qty_total);				
			}
			
			self.total_strength();
		},
		
		calculate_amount_untax:function(event){
			var self = this
			self.total = 0.00;
			_.each($("input#subtotal"),function(record){
				self.total = self.total + parseFloat($(record).val());
			});
			// adding marketing packages
			_.each(self.marketing_package,function(packages){
				if (packages.get('select')){
					self.total = self.total + parseFloat(packages.get('total'));
					}
				})
			$("input#total_without_tax").val(self.total.toFixed(2));
		},
		
		calculate_subtotal:function(event){
			self.subtotal = 0.00;
			price = 0.00;
			if ($(event.srcElement).hasClass('price')){
				price = $(event.srcElement).val();
			}
			else{
				price = $(event.srcElement).parent().parent().find("input.price.jjuice").val();
			}
			// Calculating for miscellaneus product
			if ($(event.srcElement).attr('attribute') == 'misc' || $(event.srcElement).attr('attribute') == 'misc_sub_total'){
				self.subtotal = $("input[attribute='misc'][id="+$(event.srcElement).attr('id')+"].qty").val() * price;
			}
			if ($(event.srcElement).attr('attribute') == 'marketing' || $(event.srcElement).attr('attribute') == 'marketing_sub_total' || $(event.srcElement).attr('attribute') == 'marketing_discount'){
				self.subtotal = ($("input[attribute='marketing'][id="+$(event.srcElement).attr('id')+"].qty").val() * price)*(100-parseFloat($("input[id="+$(event.srcElement).context.id+"][attribute='marketing_discount']").val() || 0))/100;
			}			
			else{
				_.each($("input[id="+$(event.srcElement).attr('id')+"][vol="+$(event.srcElement).attr('vol')+"].qty.jjuice"),function(record){
					if (! isNaN(parseFloat($(record).val()) * parseFloat(price))){
						self.subtotal = self.subtotal + (parseFloat($(record).val()) * parseFloat(price));
					}
				});				
			}
			$(event.srcElement).parent().parent().find("#subtotal").val(self.subtotal.toFixed(2));
		},
		
		extract_records_fields:function(input_records){
			_.each($("input.qty.jjuice"),function(record){
				if ($(record).attr('attribute') == 'extra' && $(record).val()>0 && ! isNaN($(record).val())){
					input_records.push({'record':record,'price':0,'extra':true,'misc':false,'extra':true})
				}
				else if ($(record).attr('attribute') == 'misc' && $(record).val()>0 && ! isNaN($(record).val())){
					input_records.push({'record':record,'price':$(record).parent().parent().find("input.price").val(),'misc':true})
				}
				else if ($(record).attr('attribute') == 'marketing' && $(record).val()>0 && ! isNaN($(record).val())){
					discount = $("input[attribute='marketing_discount'][id ="+$(record).context.id+"]").val()
					input_records.push({'discount':discount,'record':record,'price':$(record).parent().parent().find("input.price").val(),'marketing':true})
				}				
				else if ($(record).val() > 0 && ! isNaN($(record).val())){
					input_records.push({'record':record,'price':$(record).parent().parent().find("input.price").val(),'misc':false});  //----------------------
				}
			});			
		},
		confirm_order:function(queryDict,self){
			var def = $.Deferred();
			input_records = [];
			internal_sale = $('input.internal_sale')[0].checked
			order_note = $('textarea#order_note').val()
			payment_lines = []
			sale_rep = []
			for (i = 0 ; i < $('input.select').length ; i++){
				if ($('input.select')[i].checked){
					sale_rep.push(parseInt($('input.select')[i].value));
				}
			}
			_.each(self.field_manager_arr,function(line){
				payment_lines.push(line.datarecord)
			})
			if (self.field_manager_right.datarecord.paid && self.field_manager_right.datarecord.paid > 0){
					self.field_manager_right.datarecord.state = 'paid'
					payment_lines.push(self.field_manager_right.datarecord)				
			}

			self.extract_records_fields(input_records)
			var sale_order = new instance.web.Model("product.product");
			div_html = "";
			$('input.jjuice,#subtotal,#qty_total,#total_strength,#order_note').each(function() {
				if ( $(this).hasClass('price') ){
					if(isNaN(parseFloat(this.value))){
						this.value = 0;
					}
					$("<span />", { text: this.value, "class":"view" }).insertAfter(this);
					  $(this).hide();										
				}else if (this.value > 0){
					$("<span />", { text: this.value, "class":"view" }).insertAfter(this);
					  $(this).hide();					
					}else if (this.getAttribute('id') == "order_note"){
					$("<span />", { text: this.value, "class":"view" }).insertAfter(this);
					  $(this).hide();					
				}
			});
			
			_.each($('tr.delete'),function(record){
				if ($(record).find('span').length <= 2){
					$(record).remove();
				}
			});
			
			_.each($("div[perm_print = 'print']"),function(record){
				if ($(record).hasClass('pull-left')){
					div_html = div_html + "<b>"+$(record).attr('print_name')+"</b>"+" " + $($(record).children()[0]).html();
				}
				else if ($(record).find('tbody > tr').length > 1){
					div_html = div_html + "<b>"+$(record).attr('print_name')+"</b>"+" " + $(record).html()
				}
				
			});
			tax_rate = []
			tax_check = document.querySelectorAll("input[name='tax'][type='checkbox']:checked");
			_.each (tax_check,function(tax_line){
				tax_rate.push(parseInt(tax_line.getAttribute('id')))
			});
			shipping = parseFloat($("input#shipping").val());
			discount_rate = parseFloat($("input#discount_rate").val());
    		sale_order.call('first_create_sale_order',[shipping,queryDict,sale_rep,internal_sale,order_note,div_html,payment_lines]).done(function(data){
    			self.next(self.index,input_records,data.sale_order,def,data.paid_line,discount_rate,tax_rate);
    		});
    		return def
		},
		
		//Arrow keys functionality
		checkKey:function(e) {
			
		    e = e || window.event;
		    index = $(e.srcElement).parent().index()
		    if (e.keyCode == '38') {
		    	e.preventDefault();
		    	//up arrow key
		    	$($(e.srcElement).parent().parent().prev().children()[index]).children().focus();
		    }
		    else if (e.keyCode == '40') {
		    	e.preventDefault();
		    	//down arrow key
		    	$($(e.srcElement).parent().parent().next().children()[index]).children().focus();
		    }
		    else if (e.keyCode == '37') {
		       // left arrow
		    	e.preventDefault();
		    	$(e.srcElement).parent().prev().children().focus();
		    }
		    else if (e.keyCode == '39') {
		    	// right arrow key
		    	e.preventDefault();
	    		$(e.srcElement).parent().next().children().focus();
		    }

		},
//-------------------------------------
		createFormrightWidgets: function() { 
		    var self = this;
		    var create_form_fields = self.create_right_fields;
		    var create_form_fields_arr = [];
		    for (var key in create_form_fields)
		        if (create_form_fields.hasOwnProperty(key))
		            create_form_fields_arr.push(create_form_fields[key]);
		    create_form_fields_arr.sort(function(a, b){ return b.index - a.index });
		    // field_manager
		    var dataset = new instance.web.DataSet(this, "payment.plan", self.context);
		    dataset.ids = [];
		    dataset.arch = {
		        attrs: { string: "Shivam Goyal", version: "7.0", class: "oe_form_container" },
		        children: [],
		        tag: "form"
		    };
		    var field_manager = new instance.web.FormView (
		        this, dataset, false, {
		            initial_mode: 'edit',
		            disable_autofocus: false,
		            $buttons: $(),
		            $pager: $()
		    });
		
		    field_manager.load_form(dataset);
		
		    // fields default properties
		    var Default_field = function() {
		        this.context = {};
		        this.domain = [];
		        this.help = "";
		        this.readonly = false;
		        this.required = true;
		        this.selectable = true;
		        this.states = {};
		        this.views = {};
		    };
		    var Default_node = function(field_name) {
		        this.tag = "field";
		        this.children = [];
		        this.required = true;
		        this.attrs = {
		            invisible: "False",
		            modifiers: '{"required":true}',
		            name: field_name,
		            nolabel: 'True',
		        };
		    };
		    // Append fields to the field_manager
		    field_manager.fields_view.fields = {};
		    for (var i=0; i<create_form_fields_arr.length; i++) {
		        field_manager.fields_view.fields[create_form_fields_arr[i].id] = _.extend(new Default_field(), create_form_fields_arr[i].field_properties);
		    }
		    // generate the create "form"
		    var create_form = [];
		    for (var i=0; i<create_form_fields_arr.length; i++) {
		        var field_data = create_form_fields_arr[i];
		        var $super_container = $(QWeb.render("fields_right_create", {label:field_data.label}));
		        // create widgets
		        var node = new Default_node(field_data.id);

		        if (field_data.id == 'balance'){
		        	node.attrs.modifiers = '{"required":true,"readonly":true}'
		        } 
		        node.attrs.placeholder = field_data.label;
		        if (! field_data.required) node.attrs.modifiers = "";
		        var field = new field_data.constructor(field_manager, node);
		        self[field_data.id+"_field"] = field;
		        create_form.push(field);
		        // on update : change the last created line
		        field.corresponding_property = field_data.corresponding_property;
		        field.on("change:value", self, function(event){
		        	event.field_manager.datarecord[event.name]= event.get('value');
		        	if (event.name == 'paid'){
		        		event.field_manager.ViewManager.balance_field.$el[0].innerText = $("input#main_total").val() - event.get('value');
		        		self.find_total_balance();
		        	}
		        });    
		        // append to DOM
		        var $field_container = $(QWeb.render("form_create_field_jjuice_right", {id: field_data.id, label: field_data.label}));
		        field.appendTo($field_container.find("td"));
		        $super_container.find('td#field').append($field_container);
		        $("div#final_bill > table > tbody").append($super_container);
		        // now that widget's dom has been created (appendTo does that), bind events and adds tabindex
		        if (field_data.field_properties.type != "many2one") {
		            // Triggers change:value TODO : moche bind ?
		        	field.$el.find("input").keyup(function(e, field){ field.commit_value(); }.bind(null, null, field));
		        }
		        field.$el.find("input").attr("tabindex", field_data.tabindex);
		    }
		    field_manager.do_show();
		    field_manager.payment_line = $super_container;
		    return field_manager;
		},
//-------------------------------------
		find_total_balance:function(){
			var self =this;
    		total = 0.00;
    		for (i = 0;i<self.field_manager_arr.length;i++){
    			total  = total + self.field_manager_arr[i].datarecord.amount;
    		}
    		$(self.field_manager_right.ViewManager.balance_field.$el)[0].innerHTML = $("input#main_total").val()-total - ((self.field_manager_right.datarecord.paid) ? self.field_manager_right.datarecord.paid : 0 )  ;
		},
        createFormWidgets: function() { 
            var self = this;
            var create_form_fields = self.create_form_fields;
            var create_form_fields_arr = [];
            for (var key in create_form_fields)
                if (create_form_fields.hasOwnProperty(key))
                    create_form_fields_arr.push(create_form_fields[key]);
            create_form_fields_arr.sort(function(a, b){ return b.index - a.index });
            // field_manager
            var dataset = new instance.web.DataSet(this, "payment.plan", self.context);
            dataset.ids = [];
            dataset.arch = {
                attrs: { string: "Shivam Goyal", version: "7.0", class: "oe_form_container" },
                children: [],
                tag: "form"
            };
    
            var field_manager = new instance.web.FormView (
                this, dataset, false, {
                    initial_mode: 'edit',
                    disable_autofocus: false,
                    $buttons: $(),
                    $pager: $()
            });
    
            field_manager.load_form(dataset);
    
            // fields default properties
            var Default_field = function() {
                this.context = {};
                this.domain = [];
                this.help = "";
                this.readonly = false;
                this.required = true;
                this.selectable = true;
                this.states = {};
                this.views = {};
            };
            var Default_node = function(field_name) {
                this.tag = "field";
                this.children = [];
                this.required = true;
                this.attrs = {
                    invisible: "False",
                    modifiers: '{"required":true}',
                    name: field_name,
                    nolabel: 'True',
                };
            };
            // Append fields to the field_manager
            field_manager.fields_view.fields = {};
            for (var i=0; i<create_form_fields_arr.length; i++) {
                field_manager.fields_view.fields[create_form_fields_arr[i].id] = _.extend(new Default_field(), create_form_fields_arr[i].field_properties);
            }
            // generate the create "form"
            self.create_form = [];
            serial_no = $("div.payment_line").length
            var $super_container = $(QWeb.render("payment_line_create", {length:serial_no}));
            for (var i=0; i<create_form_fields_arr.length; i++) {
                var field_data = create_form_fields_arr[i];
                // create widgets
                var node = new Default_node(field_data.id);
                node.attrs.placeholder = field_data.label;
                if (! field_data.required) node.attrs.modifiers = "";
                var field = new field_data.constructor(field_manager, node);
                self[field_data.id+"_field"] = field;
                self.create_form.push(field);
                // on update : change the last created line
                field.corresponding_property = field_data.corresponding_property;
                field.on("change:value", self, function(event){
                	event.field_manager.datarecord[event.name]= event.get('value');
                	if (event.name == 'amount'){
                		self.find_total_balance();
                	}
                });    
                // append to DOM
                var $field_container = $(QWeb.render("form_create_field_jjuice", {id: field_data.id, label: field_data.label}));
                field.appendTo($field_container.find("td"));
                $super_container.find("div.oe_form.create_form > div.fields_liners").prepend($field_container);
    
                // now that widget's dom has been created (appendTo does that), bind events and adds tabindex
                if (field_data.field_properties.type != "many2one") {
                    // Triggers change:value TODO : moche bind ?
                	field.$el.find("input").keyup(function(e, field){ field.commit_value(); }.bind(null, null, field));
                }
                field.$el.find("input").attr("tabindex", field_data.tabindex);
    
            }
            $('div.action_pane.create').prepend($super_container);
            field_manager.do_show();
            field_manager.payment_line = $super_container;
            return field_manager;
        },
		
        push_product_availability:function(product_id,available_qty,required_qty){
        	/* First check if the product is already present in the list. In that case just add the qty to required quantity
        	 * If not then create a dictionary and push to product_availability object
        	 */
        	var self = this ;
        	if (product_id in self.product_availability){
        		self.product_availability[product_id].required_qty = self.product_availability[product_id].required_qty  + parseFloat(required_qty)
        	}else{
        		self.product_availability[product_id] = {
        				'available_qty': parseFloat(available_qty),
        				'required_qty':parseFloat(required_qty),
        		}
        	}
        },
        
        locate_cell_update_value:function(info,type){
		/* This function recieves dictionary in different format and located the cell with the info in the dictionary
    		if type marketing then the dictionary format will be {'available_qty': 0.0, 'individual': True, 'id': [1], 'not_available': True,'qty': 12,
    		'product_id':61}
    	 */ 
        	var self = this
        	cells = []
        	if (type == 'marketing'){
    			// First check if it is package. The list of 'id' is the package list
        		if (info.id && info.id.length > 0){
        			// This means we have to locate the package in the list
        			_.each(info.id,function(package_id){
        				console.log(self.marketing_package)
        				marketing_package = self.marketing_package[package_id]
        				if (info.not_available){
        					marketing_package.$el.find('input#qty').css('background-color','red')
        					// info.qty is the total of marketing package and marketing tab products
        					self.push_product_availability(info.product_id,info.available_qty,info.qty)
        				}
        			})
        			if (info.not_available){ // Check if it required at individual level
        				$("input#"+info.product_id+"[attribute='marketing']").css('background-color','red')
        			}
        		}
        		// check whether it is present as an individual product only  or not
        		else if (info.individual){
        			if (info.not_available){
        				$("input#"+info.product_id+"[attribute='marketing']").css('background-color','red')
        			}
        		}
        	}
        	else if (type == 'misc'){
        		//{'available_qty': 0.0, 'price': '0', 'misc': True, 'id': 62, 'not_available': True, 'qty': 1} = info
        		if (info.not_available){
        			$("input#"+info.id+"[attribute='misc']").css('background-color','red')
        			self.push_product_availability(info.id,info.available_qty,info.qty)
        		}
        	}
        	// {'product_id': 57, 'extra': True, 'price': 0, 'available_qty': 20.0, 'not_available': False, 'qty': 1, 
    		//'class_list': {'1': '10', '0': '6', '2': '1'}, 'id': 1}
        	else if (type == "extra"){
        		if (info.not_available){
        			$("input[attribute='extra'][conc='"+info.class_list['0']+"'][vol='"+info.class_list['1']+"'][id='"+info.class_list['2']+"']").css('background-color','red')
        			self.push_product_availability(info.product_id,info.available_qty,info.qty)
        		}
        	}else if (type == 'product_line'){
        		if (info.not_available){
        			$("input[name='charge'][conc='"+info.class_list['0']+"'][vol='"+info.class_list['1']+"'][id='"+info.class_list['2']+"']").css('background-color','red')
        			self.push_product_availability(info.product_id,info.available_qty,info.qty)
        		}        		
        	}
        },
        
		start:function(){	
			var self = this;
    		var queryDict = {};
//    		self.field_manager.bind('change',function(){
//    		})
    		//    		location.hash.substr(1).split("&").forEach(function(item) {queryDict[item.split("=")[0]] = item.split("=")[1]})
			
    		$(document).ready(function(){
				self.field_manager.on("change",self,function(){
//					self.start();
				});
    			if (self.field_manager.datarecord && self.field_manager.datarecord.id){
	    			queryDict = {'action':'graph.action',
	    						 'active_id':self.field_manager.datarecord.id
	    			}
	    		}
				customer = new instance.web.Model('res.partner');
// customer dependent
    			customer = new instance.web.Model('res.partner');
				customer.call('set_price',[queryDict.active_id]).done(function(price_list){
					context.price = price_list;
					if ($("div[name = 'jjuice_action_start']")){
						$("div[name = 'jjuice_action_start']").parent().empty();
					}
					self.marketing_package = {}
					if (!self.field_manager.datarecord.id){
						return
					}
					self.$el.append(QWeb.render("jjuice.action",context))
					_.each(context.marketing_package,function(packages){
						var marketing_package = new instance.web.jjuice.marketing_package_widget(self,packages)
						marketing_package.appendTo(self.$el.find('div#marketing > table#marketing_package > tbody'));
						marketing_package.on('total_changed',this,function(a,b){
							// recalculate the totals
							self.total = 0.00;
							self.subtotal = 0.00;
							self.calculate_amount_untax(event);
							self.calculate_amount_tax(event);
							input_field  = $(self.field_manager_right.ViewManager.paid_field.$el[0]).find('input').val();
							self.field_manager_right.ViewManager.balance_field.$el[0].innerText = $("input#main_total").val() - parseFloat(input_field);
							self.find_total_balance();	
						})
						self.marketing_package[marketing_package.id] = marketing_package
					});
					$("a.add_line").bind('click',function(event){
						self.field_manager_arr.unshift(self.createFormWidgets());
					})
					$("li.tab_head").click(function(){
						if (event.srcElement.text == 'Other Info'){
							div_id = "other_info";
						} 
						else{
							div_id = event.srcElement.getAttribute('href').split('#')[1];
						}
						$("li.tab_head").removeClass('change_color');
						$(event.srcElement).parent().addClass('change_color');
						$("div.tab_body").attr("class" ,"hide_tab tab_body");
						$("#"+div_id).attr("class" ,"tab_body");
					});
					
					document.onkeydown = self.checkKey;
					
					$("input[name='tax'][type='checkbox']").change(function(){
						self.calculate_amount_tax(event);
						self.find_total_balance();
					});
					
					$("input.bill").bind("keyup change",function(event){
						self.calculate_amount_tax(event);
						self.find_total_balance();
					});
					$("input#discount").bind("keyup change",function(event){
						self.calculate_amount_tax(event);
						self.find_total_balance();						
					});
					$("input.jjuice").bind("keyup change",function(event){
						if ($(event.srcElement).hasClass('qty')){
							self.calculate_quantity(event);
						}
						self.total = 0.00;
						self.subtotal = 0.00;
						self.calculate_subtotal(event);
						self.calculate_amount_untax(event);
						self.calculate_amount_tax(event);
						input_field  = $(self.field_manager_right.ViewManager.paid_field.$el[0]).find('input').val();
						self.field_manager_right.ViewManager.balance_field.$el[0].innerText = $("input#main_total").val() - parseFloat(input_field);
						self.find_total_balance();
					});
					$(document).on('click','a#x',function(event){
						event.stopImmediatePropagation();
						for (i = 0 ;i < self.field_manager_arr.length;i++){
							if (self.field_manager_arr[i].payment_line[0] == $(event.srcElement).parent().parent()[0]){
								console.log(self.field_manager_arr[i].datarecord.amount);
								self.field_manager_arr.splice(i,1);
								$(event.srcElement).parent().parent().css('display','none');
								break;
							}							
						}
						self.find_total_balance();
					});
					self.field_manager_right = self.createFormrightWidgets();
					$("#check_availability").on('click',function(event){
						self.$el.find('input.qty').css('background-color','')
						input_records= []
						self.extract_records_fields(input_records)
						packages=[]
						list = []
						self.product_availability = {} // Product Availabilty list will be refreshed everytime the check is made
						self.extract_packages(packages)
						self.extract_info_input_record(list, input_records)
			    		var product = new instance.web.Model("product.product");
			    		product.call('check_availability_product',[list,packages]).then(function(res){
						/* The res is a dictionary [package_dict,line_list]. package_dict has following format
						 * package_dict = {61: {'available_qty': 0.0, 'individual': True, 'id': [1], 'not_available': True, 'qty': 12,'product_id':61}}
						 * line_list = [{'class_list': {'1': '11', '0': '6', '2': '1'}, 'price': '0', 'misc': False, 'available_qty': 0.0, 'not_available': True, 'qty': '1'}, 
						 * 				{'class_list': {'1': '10', '0': '6', '2': '1'}, 'price': '0', 'misc': False, 'available_qty': 20.0, 'not_available': True, 'qty': '1'}, 
						 * 				{'class_list': {'1': '10', '0': '6', '2': '1'}, 'available_qty': 20.0, 'extra': True, 'price': 0, 'id': 1, 'not_available': False, 'qty': 1}, 
						 * 				{'available_qty': 0.0, 'price': '0', 'misc': True, 'id': 62, 'not_available': True, 'qty': 1}, 
						 * 				{'discount': 0, 'price': '0', 'qty': 2, 'id': 61, 'marketing': True}]
						 */
			    		_.each(res[0],function(pakage){
			    				self.locate_cell_update_value(pakage,'marketing')
			    			});
			    		_.each(res[1],function(line){
			    				if (_.has(line,'misc') && line.misc){// This means it is a miscellaneous tab product
			    					self.locate_cell_update_value(line, 'misc')
			    				}else if (_.has(line,'extra') && line.extra){
			    					self.locate_cell_update_value(line, 'extra')
			    				}else if (_.has(line,'misc') && !line.misc ){//has misc but value false mean main product line
			    					console.log("This is entry is product_line")
			    					self.locate_cell_update_value(line, 'product_line')
			    				} 
			    			})
			    			if (!$.isEmptyObject(self.product_availability)){
					    		var model = new instance.web.Model("dispaly.product.availability");
					    		model.call('prepare_wizard',[self.product_availability]).done(function(res){
					    			// res = [view_id,wizard_id]
					    			console.log(res)
					    			action = {
					    		             'type': 'ir.actions.act_window',
					    		             'view_type': 'form',
					    		             'res_id':res[1],
					    		             'view_mode': 'form',
					    		             'res_model': 'dispaly.product.availability',
					    		             'views': [[res[0], 'form']],
					    		             'view_id': res[0],
					    		             'target': 'new',		    								
			    						  }
			    						self.do_action(action)
					    		})			    				
			    			}
			    		});			
					})
					$("#confirm_order").on('click',function(event){
						$(event.currentTarget).prop('disabled',true);
						event.preventDefault();
						//making sure that the method_of_payment field is not left empty
						if (self.field_manager_right.datarecord.paid != undefined){
							console.log(self.field_manager_right);
							if (self.field_manager_right.datarecord.method_of_payment == undefined){
								self.do_notify("Payment Method","Cannot leave a Payment Method field blank")
								$(event.currentTarget).prop('disabled',false)
								return 							
							}
						}						
						for (i = 0;i < self.field_manager_arr.length;i++){
							if (self.field_manager_arr[i].datarecord.amount == undefined){
								self.do_notify("Amount","Cannot leave Amount field blank")
								return 								
							}
							if (self.field_manager_arr[i].datarecord.method_of_payment == undefined){
								self.do_notify("Payment Method","Cannot leave a Payment Method field blank")
								return 
							}
							if (self.field_manager_arr[i].datarecord.date == undefined){
								self.do_notify("Date","Cannot leave the date field blank");
								return 
							}
						}
		    			$.when(self.confirm_order(queryDict,self)).then(function(defi){
		    				//{'ref': 'sale.order,817'}
		    				if (self.field_manager.dataset.context.lead){
		    					if (!self.field_manager.dataset.context.crm_lead_id){
		    						self.do_notify("Invalid","The current Lead ID is not defined")
		    						return
		    					}
		    					var lead = new instance.web.Model("crm.lead");
		    					lead.call('write',[self.field_manager.dataset.context.crm_lead_id,{'ref':'sale.order,'+defi.id}]).done(function(){
		    						self.destroy();
		    					});
		    				}
		    				if (defi.paid_line){
		    					var model = new instance.web.Model("sale.order");
		    					model.call('confirm_sales_order',[defi.id,defi.paid_line]).done(function(info){
		    						data = info.res;
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
		    								'name':_("Pay Invoice"),
		    								'type': 'ir.actions.act_window',
					    		             'view_type': 'form',
					    		             'view_mode': 'form',
					    		             'res_model': 'account.voucher',
					    		             'views': [[info.invoice_info.view_id, 'form']],
					    		             'view_id': info.invoice_info.view_id,
					    		             'target': 'new',	
					    		             'context':info.invoice_info.context,
			    						  }
		    						self.do_action(action).done(function(){
	    							self.destroy();
		    							})
		    						})
		    					});
		    				}
		    				else{
			    				var view_id= new instance.web.Model("ir.model.data");
					    		view_id.call('get_object_reference',['sale','view_order_form']).done(function(view_id){
			        			var action = {};
			        			action = {
			    		             'type': 'ir.actions.act_window',
			    		             'view_type': 'form',
			    		             'res_id':defi.id,
			    		             'view_mode': 'form',
			    		             'res_model': 'sale.order',
			    		             'views': [[view_id[1], 'form']],
			    		             'view_id': view_id[1],
			    		             'target': 'current',
			    		               };
			        				self.do_action(action).done(function(){
			        					self.destroy();
			        				});
					    		});		    					
		    				}
		    			}); 
					});
				});
			});    
		}
	});
};

