openerp.jjuice_fedex = function(instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    local.print_shipment = instance.Widget.extend({
        init:function(parent,options){
        	this._super(parent)
        	this.options = options
        	this.shipment=false;
        },
    	convertDataURIToBinary:function(dataURI) {
    		var BASE64_MARKER = ';base64,'
    		var base64Index = dataURI.indexOf(BASE64_MARKER) + BASE64_MARKER.length;
    		var base64 = dataURI.substring(base64Index);
    		var raw = window.atob(base64);
    		var rawLength = raw.length;
    		var array = new Uint8Array(new ArrayBuffer(rawLength));

    		for (i = 0; i < rawLength; i++) {
    		    array[i] = raw.charCodeAt(i);
    		}
    		return array;
		},
		generate_pdf:function(shipment,shipment_id){
			var self = this;
			if (!shipment_id){
				alert("No shipment defined");
				return
			}else{
        		shipment.call('generate_pdf_file',[[shipment_id],'jjuice_fedex.report_print_label',undefined,self.session.user_context]).done(function(pdf){
        			blob = new Blob([self.convertDataURIToBinary("data:application/pdf;base64, " + pdf.base64)], {type: 'application/pdf'});
			        url = URL.createObjectURL(blob);
			        _iFrame = document.createElement('iframe');
    			    _iFrame.setAttribute('src', url);
    			    _iFrame.setAttribute('width', '100%');
    			    _iFrame.setAttribute('height', '600px');
    			    _iFrame.setAttribute('align', 'center');
    			    self.$el.append(_iFrame)
    			    button_shipment = $("<button style='width:100%;background:#7C7BAD;' class = 'oe_highlight' type='button'>Back to Shipment</button>")
    			    button_shipment.click('on',function(event){
    					var view_id= new instance.web.Model("ir.model.data");
    		    		view_id.call('get_object_reference',['jjuice_fedex','create_shipment_form']).done(function(view_id){
    					var action = {};
    					action = {
    			             'name':"Print Labels",
    						 'type': 'ir.actions.act_window',
    			             'view_type': 'form',
    			             'res_id':shipment_id,
    			             'view_mode': 'form',
    			             'res_model': 'create.shipment.fedex',
    			             'views': [[view_id[1], 'form']],
    			             'nodestroy':false,
    			             'view_id': view_id[1],
    			             'target': 'current',
    			             'context':{'invisible':false}
    			               };
    						self.do_action(action)
    		    		});
    			    });
    			    self.$el.prepend(button_shipment)
    			    if (self.isInArray(pdf.picking_state,states_show)){
        			    $button = $("<button style='width:100%;' class = 'oe_highlight' type='button'>Tranfer Picking</button>")
        			    self.$el.prepend($button)    		
        			    var options = {}
        			    options.on_close = function(){
        			    	shipment.query(['picking_state']).filter([['id','=',shipment_id]]).all().then(function(result){
        			    		if (!self.isInArray(result[0].picking_state,states_show)){
        			    			$button.hide();
        			    		}
        			    	});
        			    }
        			    $button.on('click',function(e){
        			    	shipment.call('transfer_picking',[shipment_id]).done(function(action){
        			    		self.do_action(action,options)
        			    	});
        			    });
    			    }
        		});//				
			}
		},
		isInArray:function(value, array) {
			  return array.indexOf(value) > -1;
		},		
		start: function() {
        	this._super();
        	var self=this;
        	if (this.options.context && this.options.context.active_model == 'create.shipment.fedex' && this.options.context.active_id){
        		var shipment_id = this.options.context.active_id
        		var shipment= new instance.web.Model("create.shipment.fedex");
        		states_show = ['assigned','partially_available']
        		if (this.options.context && this.options.context.print_pdf){
        			self.generate_pdf(shipment,shipment_id)
        			return
        		}
        		var packages= new instance.web.Model("fedex.package.shipment");
        		report_url = "/report/pdf/jjuice_fedex.report_print_label/"+shipment_id
        		report_type = "qweb-pdf"
                
        		shipment.call('create_shipment',[shipment_id]).then(function(res){
        			if (typeof(res) == "object"){
        				self.do_action(res)
        			}
        			self.generate_pdf(shipment,shipment_id)
        		})
        	}
        },
    });

    instance.web.client_actions.add(
        'print.shipment', 'instance.jjuice_fedex.print_shipment');
}