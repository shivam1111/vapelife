#JJUICE
------

- Change Sales person of Multiple Customers by opening wizard from the More Menu in tree view of customers. 
- Hide Title in Customer and Partners
- Stock Picking order by creation date (field:date) (sale_stock.py)

## Sale

- [x] When "Confirm Sale" is clicked the related partner turns into lead if it is a lead (sale_order.py function action_wait())

## Interface

> Interface for creating Sales Order from Customers Form

- Added Stock Check Availability Functionality
	* ISSUE SOLVED: The input fields remained red after repeated click on check availability button
- Marketing package functionality (Javascript)
- If it is a new record of partner the interface will not be generated. (jjuice.js line no.935)
 	 

##Partner

- Added fields (fields.py)
	1. Skype Id
	2. Type Of Account
	3. Account Classification(For Finance)
	4. Resale No
- Added Filter Customer Wizard to the tree View (jjuice.js)
	- Pass {"'filter":True} from action context in order to display the Button in Partner Tree view
	- [x] Filter based on Last Order date
	- [x] Filter based on Type of Account (model:res.partner)
	- [x] Filter all customer/lead who have never ordered a particular product line (For us right now,product line means volume)
	- [x] Filter based on  Account Classification (for Finance) 
	- [x] Filter based on sales person 
	- [x] Filter based on Account Source of Partner (mode:res.partner)
	- [x] Filter based on Account Source Name of Partner (mode:res.partner)

##Leads/Potential Customers 

> This is our own workflow for leads

- [x] A new Menu item Leads/Potential Customers is created (res_partner_view.xml)
- [x] A customer cannot be a partner and lead at the same time (res_partner.py) 
- [x] By default when creating a new lead the lead checkbox should be ticked (res_partner.py)	
- [x] Quotation button to view all the quotations created for the lead (res_partner_view.xml)
- [x] Added Smart Button 'Quotation'. It shows the quotations associated with the partner (res_partner.py,field:"draft_order_count") 
- [x] Add the  filter button in tree view for marketing   (jjuice.js search_customer())

## Reporting

- Treasury Analysis report (report/account_treasury_report.py)
	- [x] Can be filtered based on "Type of Account" field of Partner(model:res.partner)
	- [x] Can be filtered based on "Account Classification(for Finance)" field of Partner(model:res.partner)
	- [x] Can be filtered based on Invoice Partner(field:partner_id)
- Sales Analysis Report (report/sale_report.py)
	- [x] Can be filtered based on following Product Attribute(model:product.attribute.value)
		- [x] Concentration (field:conc)
		- [x] Volume (field:vol)
	- [x] Can be filtered based on the following related partner fields
		- [x] Type of Account
		- [x] Account Classification (for Finance)
- Invoice Analysis (report/invoice_report.py)
	- [x] Can be filtered based on the following related partner fields
		- [x] Type of Account
		- [x] Account Classification (for Finance)
		
