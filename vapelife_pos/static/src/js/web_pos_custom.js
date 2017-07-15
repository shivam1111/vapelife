openerp.vapelife_pos = function(instance) {

    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    var module = instance.point_of_sale;
    var round_di = instance.web.round_decimals;
    var round_pr = instance.web.round_precision;
    var cash_register = {};
    var mixture_options = [['quarter','Quarter'],['half','Half'],['three_quarters','Three Quarters'],['full','Full']]

    module.ProductListWidget.include ({
        init:function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.click_product_handler = function(event){
                var product = self.pos.db.get_product_by_id(this.dataset['productId']);
                if (product.is_bar){
                    self.pos_widget.screen_selector.show_popup('jjuicebarspopup',{'product':product})
                }else{
                    options.click_product_action(product);
                }
            };
        },
    })
    module.PosModel = module.PosModel.extend({
        models: [
            {
                model:  'res.users',
                fields: ['name','company_id'],
                ids:    function(self){ return [self.session.uid]; },
                loaded: function(self,users){ self.user = users[0]; },
            },{
                model:  'res.company',
                fields: [ 'currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'tax_calculation_rounding_method'],
                ids:    function(self){ return [self.user.company_id[0]] },
                loaded: function(self,companies){ self.company = companies[0]; },
            },{
                model:  'decimal.precision',
                fields: ['name','digits'],
                loaded: function(self,dps){
                    self.dp  = {};
                    for (var i = 0; i < dps.length; i++) {
                        self.dp[dps[i].name] = dps[i].digits;
                    }
                },
            },{
                model:  'product.uom',
                fields: [],
                domain: null,
                context: function(self){ return { active_test: false }; },
                loaded: function(self,units){
                    self.units = units;
                    var units_by_id = {};
                    for(var i = 0, len = units.length; i < len; i++){
                        units_by_id[units[i].id] = units[i];
                        units[i].groupable = ( units[i].category_id[0] === 1 );
                        units[i].is_unit   = ( units[i].id === 1 );
                    }
                    self.units_by_id = units_by_id;
                }
            },{
                model:  'res.users',
                fields: ['name','ean13'],
                domain: null,
                loaded: function(self,users){ self.users = users; },
            },{
                model:  'res.partner',
                fields: ['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','ean13','write_date'],
                domain: [['customer','=',true]],
                loaded: function(self,partners){
                    self.partners = partners;
                    self.db.add_partners(partners);
                },
            },{
                model:  'res.country',
                fields: ['name'],
                loaded: function(self,countries){
                    self.countries = countries;
                    self.company.country = null;
                    for (var i = 0; i < countries.length; i++) {
                        if (countries[i].id === self.company.country_id[0]){
                            self.company.country = countries[i];
                        }
                    }
                },
            },{
                model:  'account.tax',
                fields: ['name','amount', 'price_include', 'include_base_amount', 'type', 'child_ids', 'child_depend', 'include_base_amount'],
                domain: null,
                loaded: function(self, taxes){
                    self.taxes = taxes;
                    self.taxes_by_id = {};
                    _.each(taxes, function(tax){
                        self.taxes_by_id[tax.id] = tax;
                    });
                    _.each(self.taxes_by_id, function(tax) {
                        tax.child_taxes = {};
                        _.each(tax.child_ids, function(child_tax_id) {
                            tax.child_taxes[child_tax_id] = self.taxes_by_id[child_tax_id];
                        });
                    });
                },
            },{
                model:  'pos.session',
                fields: ['id', 'journal_ids','name','user_id','config_id','start_at','stop_at','sequence_number','login_number'],
                domain: function(self){ return [['state','=','opened'],['user_id','=',self.session.uid]]; },
                loaded: function(self,pos_sessions){
                    self.pos_session = pos_sessions[0];

                    var orders = self.db.get_orders();
                    for (var i = 0; i < orders.length; i++) {
                        self.pos_session.sequence_number = Math.max(self.pos_session.sequence_number, orders[i].data.sequence_number+1);
                    }
                },
            },{
                model: 'pos.config',
                fields: [],
                domain: function(self){ return [['id','=', self.pos_session.config_id[0]]]; },
                loaded: function(self,configs){
                    self.config = configs[0];
                    self.config.use_proxy = self.config.iface_payment_terminal ||
                                            self.config.iface_electronic_scale ||
                                            self.config.iface_print_via_proxy  ||
                                            self.config.iface_scan_via_proxy   ||
                                            self.config.iface_cashdrawer;

                    self.barcode_reader.add_barcode_patterns({
                        'product':  self.config.barcode_product,
                        'cashier':  self.config.barcode_cashier,
                        'client':   self.config.barcode_customer,
                        'weight':   self.config.barcode_weight,
                        'discount': self.config.barcode_discount,
                        'price':    self.config.barcode_price,
                    });

                    if (self.config.company_id[0] !== self.user.company_id[0]) {
                        throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                    }
                },
            },{
                model: 'stock.location',
                fields: [],
                ids:    function(self){ return [self.config.stock_location_id[0]]; },
                loaded: function(self, locations){ self.shop = locations[0]; },
            },{
                model:  'product.pricelist',
                fields: ['currency_id'],
                ids:    function(self){ return [self.config.pricelist_id[0]]; },
                loaded: function(self, pricelists){ self.pricelist = pricelists[0]; },
            },{
                model: 'res.currency',
                fields: ['name','symbol','position','rounding','accuracy'],
                ids:    function(self){ return [self.pricelist.currency_id[0]]; },
                loaded: function(self, currencies){
                    self.currency = currencies[0];
                    if (self.currency.rounding > 0) {
                        self.currency.decimals = Math.ceil(Math.log(1.0 / self.currency.rounding) / Math.log(10));
                    } else {
                        self.currency.decimals = 0;
                    }

                },
            },{
                model: 'product.packaging',
                fields: ['ean','product_tmpl_id'],
                domain: null,
                loaded: function(self, packagings){
                    self.db.add_packagings(packagings);
                },
            },{
                model:  'pos.category',
                fields: ['id','name','parent_id','child_id','image'],
                domain: null,
                loaded: function(self, categories){
                    self.db.add_categories(categories);
                },
            },{
                model:  'product.product',
                fields: ['display_name', 'list_price','price','pos_categ_id', 'taxes_id', 'ean13', 'default_code',
                         'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description',
                         'product_tmpl_id','is_bar','max_volume','vol_id','conc_id'],
                domain: [['sale_ok','=',true],['available_in_pos','=',true]],
                context: function(self){ return { pricelist: self.pricelist.id, display_default_code: false, }; },
                loaded: function(self, products){
                    self.db.add_products(products);
                },
            },{
                model:  'account.bank.statement',
                fields: ['account_id','currency','journal_id','state','name','user_id','pos_session_id'],
                domain: function(self){ return [['state', '=', 'open'],['pos_session_id', '=', self.pos_session.id]]; },
                loaded: function(self, bankstatements, tmp){
                    self.bankstatements = bankstatements;

                    tmp.journals = [];
                    _.each(bankstatements,function(statement){
                        tmp.journals.push(statement.journal_id[0]);
                    });
                },
            },{
                model:  'account.journal',
                fields: [],
                domain: function(self,tmp){ return [['id','in',tmp.journals]]; },
                loaded: function(self, journals){
                    self.journals = journals;

                    // associate the bank statements with their journals.
                    var bankstatements = self.bankstatements;
                    for(var i = 0, ilen = bankstatements.length; i < ilen; i++){
                        for(var j = 0, jlen = journals.length; j < jlen; j++){
                            if(bankstatements[i].journal_id[0] === journals[j].id){
                                bankstatements[i].journal = journals[j];
                            }
                        }
                    }
                    self.cashregisters = bankstatements;
                },
            },{
                label: 'fonts',
                loaded: function(self){
                    var fonts_loaded = new $.Deferred();

                    // Waiting for fonts to be loaded to prevent receipt printing
                    // from printing empty receipt while loading Inconsolata
                    // ( The font used for the receipt )
                    waitForWebfonts(['Lato','Inconsolata'], function(){
                        fonts_loaded.resolve();
                    });

                    // The JS used to detect font loading is not 100% robust, so
                    // do not wait more than 5sec
                    setTimeout(function(){
                        fonts_loaded.resolve();
                    },5000);

                    return fonts_loaded;
                },
            },{
                label: 'pictures',
                loaded: function(self){
                    self.company_logo = new Image();
                    var  logo_loaded = new $.Deferred();
                    self.company_logo.onload = function(){
                        var img = self.company_logo;
                        var ratio = 1;
                        var targetwidth = 300;
                        var maxheight = 150;
                        if( img.width !== targetwidth ){
                            ratio = targetwidth / img.width;
                        }
                        if( img.height * ratio > maxheight ){
                            ratio = maxheight / img.height;
                        }
                        var width  = Math.floor(img.width * ratio);
                        var height = Math.floor(img.height * ratio);
                        var c = document.createElement('canvas');
                            c.width  = width;
                            c.height = height
                        var ctx = c.getContext('2d');
                            ctx.drawImage(self.company_logo,0,0, width, height);

                        self.company_logo_base64 = c.toDataURL();
                        logo_loaded.resolve();
                    };
                    self.company_logo.onerror = function(){
                        logo_loaded.reject();
                    };
                        self.company_logo.crossOrigin = "anonymous";
                    self.company_logo.src = '/web/binary/company_logo' +'?_'+Math.random();

                    return logo_loaded;
                },
            },
        ],
    })
    var orderline_id = 1;
    module.Orderline = module.Orderline.extend({
        initialize: function(attr,options){
            this.pos = options.pos;
            console.log(options)
            this.order = options.order;
            this.product = options.product;
            this.price   = options.product.price;
            this.quantity = 1;
            this.quantityStr = '1';
            this.discount = 0;
            this.discountStr = '0';
            this.type = 'unit';
            this.selected = false;
            this.id       = orderline_id++;
            this.product_mix_a_id = options.product_mix_a_id;
            this.product_mix_b_id = options.product_mix_b_id;
            this.mixture = 'quarter'
        },
        set_discount: function(discount){
            var self = this;
            var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
            // get the user group
            var user_model = new instance.web.Model("res.users");
            user_model.call("has_group",["point_of_sale.group_pos_manager"]).done(function(is_manager){
                if (!is_manager && disc > 20){
                    self.pos.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Warning!'),
                        'comment': _t('Cannot exceed 20% discount.'),
                    });
                    return
                }
                self.discount = disc;
                self.discountStr = '' + disc;
                self.trigger('change',self);
            })
        },
        get_product_mix_a_id:function(){
            return this.product_mix_a_id;
        },
        get_product_mix_b_id:function(){
            return this.product_mix_b_id;
        },
        get_mixture:function(){
            return this.mixture;
        },

        export_as_JSON: function() {
            return {
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                discount: this.get_discount(),
                product_id: this.get_product().id,
                product_mix_a_id:this.get_product_mix_a_id(),
                product_mix_b_id:this.get_product_mix_b_id(),
                mixture:this.get_mixture(),
            };
        },
    })

    module.JJuiceBarPopupWidget = module.PopUpWidget.extend({
        template:'JJuiceBarPopupWidget',
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
            this.jjuice_bars = [];
            var data_model = new instance.web.Model("ir.model.data");
            this.def1 = data_model.call('get_object_reference',['jjuice','attribute_12']);
            this.def2 = data_model.call('get_object_reference',['jjuice','attribute_0']);
            this.def3 = data_model.call('get_object_reference',['jjuice','attribute_350ml']);
        },
        get_product_image_url: function(product){
            return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product.id;
        },
        set_heading:function(text,options){
            var self = this;
            self.header.text(text);
        },
        render_product:function(product){
            var self = this;
            var image_url = self.get_product_image_url(product);
            var product_render = $(QWeb.render('Product',{'product':product,'image_url':image_url,'widget':self}));
            return product_render
        },
        render_step1:function(options){
            var self = this;
            var products = []
            self.set_heading("Select Volume of Juice Bar");
            self.product_list_widget = $(QWeb.render('ProductListWidget',{}));
            self.product_list_widget.appendTo(self.wrapper);
            console.log(self.product_list_widget);
            self.product_list_widget.css('top','45px')
            self.product_list_widget.css('bottom','60px')
            _.each(self.jjuice_bars,function(product){
                var product_render = self.render_product(product)
                product_render.appendTo(self.product_list_widget.find("div.product-list"));
                product_render.data('id',product.id)
                products.push(product_render)
            })
            return products
        },
        render_step2:function(conc_0_id,vol_350_id,options){
            /*
                Get 0mg , 350 ml products from the db and display it
            */
            var self = this;
            var products = [];
            self.set_heading("Select 0mg Flavor");
            self.product_list_widget.find("div.product-list").empty();
            _.each(self.pos.db.product_by_id,function(value,key){
                if (value.vol_id[0] == vol_350_id[1] && value.conc_id[0] == conc_0_id[1]){
                    var product_render = self.render_product(value);
                    product_render.appendTo(self.product_list_widget.find("div.product-list"));
                    product_render.data('id',value.id)
                    products.push(product_render);
                }
            });
            return products
        },
        render_step3:function(options){
            // Render the mixture to select the composition of the mixture
            var self = this;
            self.product_list_widget.find("div.product-list").empty();
//            self.wrapper.empty();
            var ratio_columns = [];
            self.set_heading("Select 0mg mix ratio");
            self.product_list_widget.find("div.product-list").append("<table><tbody><tr></tr></tbody></table>");
            _.each(mixture_options,function(mix){
                var mix_render = $(QWeb.render('mixture_options',{'name':mix[1],'key':mix[0]}));
                mix_render.data('name',mix[0]);
                switch(mix[0]){
                    case 'quarter':
                        mix_render.find('div.fill').css('height','62.5');
                        mix_render.find('div.unfill').css('height','187.5');
                        break;
                    case 'half':
                        mix_render.find('div.fill').css('height','125');
                        mix_render.find('div.unfill').css('height','125');
                        break;
                    case 'three_quarters':
                        mix_render.find('div.fill').css('height','187.5');
                        mix_render.find('div.unfill').css('height','62.5');
                        break;
                    case 'full':
                        mix_render.find('div.fill').css('height','250');
                        break;
                }
                self.product_list_widget.find("div.product-list").find('tr').append(mix_render)
                ratio_columns.push(mix_render);
            })
            self.product_list_widget.css('top','0px')
            self.product_list_widget.css('bottom','0px')
            self.product_list_widget.find('div.product-list-scroller').css('overflow-y','hidden')
            return ratio_columns;
        },
        render_step4:function(conc_12_id,vol_350_id,options){
            var self = this;
            var products = []
            self.product_list_widget.find("div.product-list").empty();
            if (options.mix_ratio == 'full'){
                self.add_order_line({});
            }else{
                self.set_heading("Select 12mg Flavor");
                _.each(self.pos.db.product_by_id,function(value,key){
                    if (value.vol_id[0] == vol_350_id[1] && value.conc_id[0] == conc_12_id[1]){
                        var product_render = self.render_product(value);
                        product_render.appendTo(self.product_list_widget.find("div.product-list"));
                        product_render.data('id',value.id)
                        products.push(product_render);
                    }
                });
                self.product_list_widget.css('top','45px')
                self.product_list_widget.css('bottom','60px')
                self.product_list_widget.find('div.product-list-scroller').css('overflow-y','auto')
            }
            return products
        },
        add_order_line:function(options){
            var self = this;
            var order = self.pos.get('selectedOrder')
            self.addProduct(order,options);
        },
        get_display_name:function(product){
            var self = this;
            var name = product.display_name;
//            try{
                if (self.model.get('product_mix_a_id')){
                    name = name + ' - ' + self.pos.db.product_by_id[self.model.get('product_mix_a_id')].display_name.split(" ")[0];
                }
                if (self.model.get('product_mix_b_id')){
                    name = name + ' / ' + self.pos.db.product_by_id[self.model.get('product_mix_b_id')].display_name.split(" ")[0];
                }
//            }catch(err){
                //pass
//            }
            return name;

        },
        addProduct:function(order,options){
            var self = this;
            var product = Object.assign({}, self.pos.db.product_by_id[self.model.get('product_id')]);
            product.display_name = self.get_display_name(product);
            if(order._printed){
                order.destroy();
                return order.pos.get('selectedOrder').addProduct(product, {});
            }
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;

            var line = new module.Orderline({}, {pos: order.pos, order: order, product: product});
            line.product_mix_a_id = self.model.get('product_mix_a_id');
            line.product_mix_b_id = self.model.get('product_mix_b_id');
            line.mixture = self.model.get('mixture');

            if(options.quantity !== undefined){
                line.set_quantity(1);
            }

            if(options.price !== undefined){
                line.set_unit_price(options.price);
            }

            if(options.discount !== undefined){
                line.set_discount(options.discount);
            }

            var last_orderline = order.getLastOrderline();
            order.get('orderLines').add(line);
            order.selectLine(order.getLastOrderline());
            self.pos_widget.screen_selector.close_popup();
        },
        show: function(options){
            options = options || {};
            var self = this;
            this._super();
            // We reset the model information every time we show this popup
            this.model = new Backbone.Model()
            if (self.jjuice_bars.length <= 0){ // only add the first time
                _.each(self.pos.db.product_by_id,function(value,key){
                    if (value.is_bar){
                        self.jjuice_bars.push(self.pos.db.product_by_id[key])
                    }
                })
            }
            this.renderElement();
            this.header = $('<div class="header"></div>');
            this.wrapper = $('<div class="wrapper"></div>');
            this.wrapper.prependTo(self.$el.find("div.popup.jjuicebarspopup"))
            this.header.insertAfter(self.$el.find("div.footer"))
            $.when(self.def1,self.def2,self.def3).done(function(conc_12_id,conc_0_id,vol_350_id){
                var products1 = self.render_step1({})
                _.each(products1,function(product1){
                    if (options.hasOwnProperty('product')){
                        if (options.product.id == $(product1).data('product-id')){
                            $(product1).css("border","orange solid 5px")
                        }
                    }
                    product1.on('click',function(){
                        self.model.set({'product_id':$(this).data('product-id')})
                        // get product id $(this).data('product-id')
                        var products2 = self.render_step2(conc_0_id,vol_350_id,{});
                        _.each(products2,function(product2){
                            product2.on('click',function(){
                                self.model.set({'product_mix_a_id':$(this).data('product-id')})
                                // get product id $(this).data('product-id')
                                var ratio_columns = self.render_step3({});
                                _.each(ratio_columns,function(col){
                                    col.on('click',function(){
                                        self.model.set({'mixture':$(this).data('name')})
                                        // access data -: this,$(this).data('name')
                                        var mix_ratio = $(this).data('name');
                                        var products4 = self.render_step4(conc_12_id,vol_350_id,{'mix_ratio':mix_ratio});
                                        _.each(products4,function(product4){
                                            product4.on('click',function(){
                                                self.model.set({'product_mix_b_id':$(this).data('product-id')})
                                                self.add_order_line({});
                                            })

                                        })
                                    })
                                })
                            })
                        })
                    })
                })
            });
            this.$('.footer .button').click(function(){
                self.pos_widget.screen_selector.close_popup();
            });
        },
        close:function(){
            var self = this;
            this._super();
            this.model.destroy();

        },
    });

    module.JJuiceBarsWidget = module.PosBaseWidget.extend({
        template: 'JJuiceBarsWidget',
        init: function(parent, options){
            this._super(parent, options);
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.popup_widget = new module.JJuiceBarPopupWidget(this.pos_widget,{});
            this.popup_widget.appendTo(self.pos_widget.$el);
            // In the widget.js when error pop is initialized it is then added to screenSelector -> pop_set. Then it is hidden manually
            // to confirm check screen.js -> module.ScreenSelector -> init()
            this.popup_widget.hide();
            this.pos_widget.screen_selector.popup_set.jjuicebarspopup = this.popup_widget
            this.$el.on('click',function(){
                self.pos_widget.screen_selector.show_popup('jjuicebarspopup',{})
            })
        },
    });

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            this.jjuice_bars = new module.JJuiceBarsWidget(this,{});
            this.jjuice_bars.prependTo(this.paypad.$el)
        },
    })
}