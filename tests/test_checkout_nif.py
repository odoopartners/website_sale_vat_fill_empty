from odoo.tests import TransactionCase

from ..models.res_partner import CHECKOUT_VAT_CONTEXT


class TestWebsiteSaleCheckoutNif(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.partner'].create({'name': 'Empresa checkout'})
        cls.contact = cls.env['res.partner'].create({
            'name': 'Contacto checkout',
            'parent_id': cls.company.id,
            'type': 'contact',
        })

    def test_child_without_company_nif_can_edit_in_checkout(self):
        self.assertFalse(self.contact.can_edit_vat())
        self.assertTrue(self.contact.with_context(
            **{CHECKOUT_VAT_CONTEXT: True}
        ).can_edit_vat())

    def test_checkout_vat_is_stored_on_commercial_partner(self):
        self.contact._set_checkout_vat_on_commercial_partner(' ESA12345674 ')
        self.assertEqual(self.company.vat, 'ESA12345674')
        self.assertEqual(self.contact.vat, 'ESA12345674')

    def test_existing_company_nif_keeps_native_lock(self):
        self.company.vat = 'ESA12345674'
        self.assertFalse(self.contact.with_context(
            **{CHECKOUT_VAT_CONTEXT: True}
        ).can_edit_vat())
