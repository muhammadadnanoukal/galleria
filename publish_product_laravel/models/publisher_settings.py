from odoo import fields, models, api


class PublisherSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    laravel_sync_url = fields.Char(string='Laravel synchronize URL',
                                    default="http://laravel.com/server/api",
                                    help="Laravel API link,to synchronize  products.")

    def set_values(self):
        res = super(PublisherSetting, self).set_values()
        config_parameters = self.env['ir.config_parameter']
        config_parameters.set_param("laravel_sync_url", self.laravel_sync_url)
        return res

    @api.model
    def get_values(self):
        res = super(PublisherSetting, self).get_values()
        laravel_sync_url = self.env['ir.config_parameter'].get_param('laravel_sync_url')
        if not laravel_sync_url:
            laravel_sync_url = "http://laravel.com/server/api"
        res.update(laravel_sync_url=laravel_sync_url)

        return res
