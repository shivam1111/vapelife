openerp.jjuice= function (instance,local) {
	openerp.jjuice.pos(instance,local);
	openerp.jjuice.marketing_package(instance,local)
    var _t = instance.web._t,
    _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    instance.web.jjuice = instance.web.jjuice || {};
    

    //********************************* Filter customer wizard button ****************************
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

    
    // *******************************Filter customer wizard button ********************
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
};

