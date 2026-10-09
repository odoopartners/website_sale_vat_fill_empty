{
    "name": "Website Sale VAT Fill Empty",
    "version": "18.0.2.0.0",
    "summary": "Allow customers to provide a missing NIF during checkout",
    "description": """
Website Sale VAT Fill Empty
===========================

Allow an ecommerce customer to provide a missing VAT/NIF during checkout.
The value is stored on the commercial partner, so Odoo's native commercial
field propagation fills the related contacts and addresses. Existing VAT
values remain protected by Odoo's native lock and validations.
    """,
    "author": "Ganemo",
    "maintainer": "Ganemo",
    "website": "https://www.ganemo.co",
    "category": "Website/Website",
    "depends": ["website_sale", "account"],
    "data": [
        "views/website_sale_templates.xml",
    ],
    "icon": "/website_sale_vat_fill_empty/static/description/icon.png",
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
