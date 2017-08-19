openerp.vapelife_pos = function(instance) {

    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    var module = instance.point_of_sale;
    var round_di = instance.web.round_decimals;
    var round_pr = instance.web.round_precision;
    var cash_register = {};
    var mixture_options = [['quarter','Quarter'],['half','Half'],['three_quarters','Three Quarters'],['full','Full']]

    var EventBus = {};
    _.extend(EventBus, Backbone.Events);

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
    module.Order = module.Order.extend({
        initialize: function(attributes){
            Backbone.Model.prototype.initialize.apply(this, arguments);
            this.pos = attributes.pos;
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.uid =     this.generateUniqueId();
            this.set({
                creationDate:   new Date(),
                orderLines:     new module.OrderlineCollection(),
                paymentLines:   new module.PaymentlineCollection(),
                name:           _t("Order ") + this.uid,
                client:         null,
                note:           "",
            });
            this.selected_orderline   = undefined;
            this.selected_paymentline = undefined;
            this.screen_data = {};  // see ScreenSelector
            this.receipt_type = 'receipt';  // 'receipt' || 'invoice'
            this.temporary = attributes.temporary || false;
            return this;
        },
        getNote:function(){
            return this.get('note') || "";
        },
        export_as_JSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            (this.get('orderLines')).each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            (this.get('paymentLines')).each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            EventBus.trigger("clear_note");
            return {
                name: this.getName(),
                amount_paid: this.getPaidTotal(),
                amount_total: this.getTotalTaxIncluded(),
                amount_tax: this.getTax(),
                amount_return: this.getChange(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos.pos_session.id,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.cashier ? this.pos.cashier.id : this.pos.user.id,
                uid: this.uid,
                sequence_number: this.sequence_number,
                note:this.get('note'),
            };
        },
    })
    var orderline_id = 1;
    module.Orderline = module.Orderline.extend({
        initialize: function(attr,options){
            this.pos = options.pos;
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
        },
        set_discount: function(discount){
            var self = this;
            var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
            self.discount = disc;
            self.discountStr = '' + disc;
            self.trigger('change',self);
            // get the user group
//            var user_model = new instance.web.Model("res.users");
//            user_model.call("has_group",["point_of_sale.group_pos_manager"]).done(function(is_manager){
//                if (!is_manager && disc > 20){
//                    self.pos.pos_widget.screen_selector.show_popup('error',{
//                        'message': _t('Warning!'),
//                        'comment': _t('Cannot exceed 20% discount.'),
//                    });
//                    return
//                }
//                self.discount = disc;
//                self.discountStr = '' + disc;
//                self.trigger('change',self);
//            })
        },
        export_as_JSON: function() {
            return {
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                discount: this.get_discount(),
                product_id: this.get_product().id,
                mixture_line_id:this.mixture_line_id,
            };
        },
    })

    module.JJuiceBarPopupWidget = module.PopUpWidget.extend({
        template:'JJuiceBarPopupWidget',
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
            this.jjuice_bars = [];
            this.total_parts = 0;
            var data_model = new instance.web.Model('pos.order');
            this.def1 = data_model.call('get_details',[])
        },
        get_product_image_url: function(product){
            return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product.id;
        },
        set_heading:function(text,options){
            var self = this;
            return;
            self.header.text(text);
        },
        render_product:function(product){
            var self = this;
            var image_url = self.get_product_image_url(product);
            var product_render = $(QWeb.render('Product',{'product':product,'image_url':image_url,'widget':self}));
            return product_render
        },
        click_product_handler:function(elem,product){
            var self = this;
            if (self.db.has(product.id)){
                self.db.set(product.id,self.db.get(product.id) + 1);
            }else{
                self.db.set(product.id,1);
            }
        },
        render_pages:function(options){
            var self = this;
            self.pages = {}
            self.tab_buttons = {};
            console.log(options)
            self.conc_ids = new Backbone.Collection(options.conc_ids);
            var products = [];
            self.conc_ids.each(function(conc_id,index){
                self.pages[conc_id.get("id")] = $(QWeb.render('ProductListWidget',{}));
                self.pages[conc_id.get("id")].appendTo(self.wrapper)
                var button = $("<button class='button' >%NAME%</button>".replace("%NAME%",conc_id.get("name")))
                self.tab_buttons[conc_id.get("id")] = button;
                self.header.append(button);
                self.pages[conc_id.get("id")].css({"width":"70%",'top':'85px','bottom':'61px','float':'left'})
                _.each(self.pos.db.product_by_id,function(value,key){
                    if (value.vol_id[0] == options.vol_350_id.id && value.conc_id[0] == conc_id.get("id")){
                        var product_render = self.render_product(value);
                        product_render.appendTo(self.pages[conc_id.get("id")].find("div.product-list"));
                        product_render.data('id',value.id)
                        products.push(product_render);
                        product_render.on("click",function(){
                            self.click_product_handler(this,value)
                        });
                    }
                });
                if (index == 0){
                    button.removeClass("button")
                }else{
                    self.pages[conc_id.get("id")].hide();
                }
                button.on("click",function(){
                    _.each(self.pages,function(elem,key){
                        if (key == conc_id.get("id")){
                            self.tab_buttons[key].removeClass("button")
                            elem.show();
                        }else{
                            self.tab_buttons[key].addClass("button")
                            elem.hide();
                        }
                    })
                })
            })
        },
        _get_mix_ratio:function(mix_part){
            var self = this;
            return mix_part/self.total_parts;
        },
        _get_line_concentration:function(){
            var self = this;
            var line_concentration_value = 0.00;
            _.each(self.db.attributes,function(value,key){
                if (self.pos.db.product_by_id[key].conc_id){
                    var conc = self.conc_ids.get(self.pos.db.product_by_id[key].conc_id[0]);
                    line_concentration_value = line_concentration_value + (conc.get("actual_value") * self._get_mix_ratio(value));
                }
            });
            return line_concentration_value;
        },
        on_change_db:function(){
            var self = this;
            var summary = [];
            var total = 0;
            self.summary_page.empty();
            line_concentration_value = 0.00;
            _.each(self.db.attributes,function(value,key){
                var  p = self.pos.db.product_by_id[key]
                summary.push({
                    id:p.id,
                    name:p.display_name,
                    qty:value,
                })
                total = total + value;
            })
            self.total_parts = total;
            self.line_concentration_value = self._get_line_concentration();
            var summary_elem = $(QWeb.render('PopUpSummary',{'summary':summary,total_length : self.total_parts}))
            summary_elem.appendTo(self.summary_page);
            $("td#reduce").on("click",function(){
                var product_id = $(this).data().productId;
                var qty  = self.db.get(product_id);
                if (qty == 1){
                    self.db.unset(product_id)
                }else{
                    self.db.set(product_id, self.db.get(product_id) - 1)
                }
                if (Object.keys(self.db.attributes).length <= 0){
                    self.summary_page.empty();
                }
            })
            summary_elem.find("caption").text("Conc. %REPLACE% mg".replace("%REPLACE%",self.line_concentration_value))
            summary_elem.find("button.button").on('click',function(){
                self.add_order_line();
            })
        },

        show: function(options){
            var self = this;
            self.product = options.product;
            options = options || {};
            self.db = new Backbone.Model();
            self.db.on("change",function(){
                self.on_change_db();
            })
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
            this.header = $('<div class="header" style="width:66%;"></div>')
            this.wrapper = $('<div class="wrapper"><div style="width:66%;" >%REPLACE%</div></div>'.replace("%REPLACE%",self.product.display_name));
            this.wrapper.prependTo(self.$el.find("div.popup.jjuicebarspopup"))
            this.header.insertAfter(self.$el.find("div.footer"))
            $.when(self.def1).done(function(res){
                var products1 = self.render_pages(res)
            });
            self.summary_page = $("<div></div>")
            self.summary_page.css({"width":"30%",'top':'85px','bottom':'61px','float':'right','position':'relative','font-size':"14px",'font-weight':"normal"})
            self.summary_page.appendTo(self.wrapper);
            this.$('.footer .button').click(function(){
                self.pos_widget.screen_selector.close_popup();
            });
        },
        add_order_line:function(options){
            var self = this;
            var order = self.pos.get('selectedOrder')
            self.addProduct(order,options);
        },
        get_display_name:function(product){
            var self = this;
            var name = product.display_name;
            _.each(self.db.attributes,function(value,key){
                name = name + ' - ' + self.pos.db.product_by_id[key].display_name.split(" ")[0]
            })
            return name;

        },
        addProduct:function(order,options){
            var self = this;
            var product = Object.assign({}, self.pos.db.product_by_id[self.product.id]);
            if(order._printed){
                order.destroy();
                return order.pos.get('selectedOrder').addProduct(product, {});
            }
            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;

            var line = new module.Orderline({}, {pos: order.pos, order: order, product: product});
            line.mixture_line_id = [];
            _.each(self.db.attributes,function(val,key){
                line.mixture_line_id.push([0,0,{
                    product_id:parseInt(key),
                    mix:self._get_mix_ratio(val)
                }])
            })
            product.display_name = product.display_name + " - REPLACE mg".replace("REPLACE",self.line_concentration_value)

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
        close:function(){
            var self = this;
            this._super();
            this.model.destroy();

        },
    });

    module.AddNotesPopUp = module.PopUpWidget.extend({
        template:'AddNotesPopUp',
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
        },
        renderElement:function(){
            var self = this;
            this._super();
            EventBus.on('clear_note',function(){
                console.log("Event Triggered")
                self.$("textarea").val("");
            })
            this.$('.footer .button').click(function(){
                var order = self.pos.get('selectedOrder');
                self.pos_widget.screen_selector.close_popup();
                order.set('note',self.$("textarea").val() || "")
            });
        },
        show:function(options){
            var self = this;
            this._super();
        },
    })
    module.AddNotesButton = module.PosBaseWidget.extend({
        template: 'AddButtonWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.name = "Add Note"
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$el.click(function(){
                self.pos_widget.screen_selector.show_popup('add_notes_popup',{})
            })
        }
    });

    module.AddMassDiscountPopUp = module.PopUpWidget.extend({
        template:'AddDiscountPopUp',
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
        },
        renderElement:function(){
            var self = this;
            this._super();
            this.$('div.button.set').click(function(){
                event.stopImmediatePropagation()
                var lines = self.pos.get('selectedOrder').get('orderLines');
                var discount = self.$("input").val() || "0.00";
                lines.forEach(function(model,index){
                    model.set_discount(discount)
                })
                self.pos_widget.screen_selector.close_popup();
                self.$("input").val("0.00");
            });
            this.$('.footer .button.cancel').click(function(){
                self.pos_widget.screen_selector.close_popup();
            });
        },
        show:function(options){
            var self = this;
            this._super();
        },
    });


    module.MassDiscountButton = module.PosBaseWidget.extend({
        template: 'AddButtonWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.name = "Mass Discount";
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$el.click(function(){
                self.pos_widget.screen_selector.show_popup('AddMassDiscountPopUp',{})
            })
        }
    });

    module.JJuiceBarsWidget = module.PosBaseWidget.extend({
        init: function(parent, options){
            this._super(parent, options);
            this.start();
        },
        renderElement: function() {
            // RenderElement will not work until we are not appending the $el of this widget into DOM but start will work always
            var self = this;
            this._super();
        },
        start:function(){
            // RenderElement will not work until we are not appending the $el of this widget into DOM but start will work always
            var self = this;
            this._super();
            this.popup_widget = new module.JJuiceBarPopupWidget(this.pos_widget,{});
            this.popup_widget.appendTo(self.pos_widget.$el);
            this.add_notes_popup = new module.AddNotesPopUp(this.pos_widget,{});
            this.add_notes_popup.appendTo(self.pos_widget.$el);
            this.AddMassDiscountPopUp = new module.AddMassDiscountPopUp(this.pos_widget,{});
            this.AddMassDiscountPopUp.appendTo(self.pos_widget.$el);
            // In the widget.js when error pop is initialized it is then added to screenSelector -> pop_set. Then it is hidden manually
            // to confirm check screen.js -> module.ScreenSelector -> init()
            this.popup_widget.hide();
            this.add_notes_popup.hide();
            this.AddMassDiscountPopUp.hide();

            this.pos_widget.screen_selector.popup_set.jjuicebarspopup = this.popup_widget;
            this.pos_widget.screen_selector.popup_set.add_notes_popup = this.add_notes_popup;
            this.pos_widget.screen_selector.popup_set.AddMassDiscountPopUp = this.AddMassDiscountPopUp;

            this.AddNotespadButton = new module.AddNotesButton(this, {});
            this.AddMassDiscountButton = new module.MassDiscountButton(this,{})
            this.AddNotespadButton.appendTo(self.pos_widget.$el.find('.paypad.touch-scrollable'));
            this.AddMassDiscountButton.appendTo(self.pos_widget.$el.find('.paypad.touch-scrollable'));
        },
    });

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            this.jjuice_bars = new module.JJuiceBarsWidget(this,{});
        },
    })
}