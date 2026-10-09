from odoo import models


CHECKOUT_VAT_CONTEXT = "website_sale_vat_fill_empty"


class ResPartner(models.Model):
    _inherit = "res.partner"

    def can_edit_vat(self):
        result = super().can_edit_vat()
        if self.env.context.get(CHECKOUT_VAT_CONTEXT):
            return result or not self.commercial_partner_id.vat
        return result

    def _set_checkout_vat_on_commercial_partner(self, vat):
        """Store a newly supplied checkout VAT on the commercial partner only."""
        self.ensure_one()
        commercial_partner = self.commercial_partner_id
        if commercial_partner.vat or not vat:
            return False
        commercial_partner.with_context(no_vat_validation=True).write({
            'vat': vat.strip(),
        })
        return True
