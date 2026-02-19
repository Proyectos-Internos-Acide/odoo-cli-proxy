import os
import unittest
from unittest.mock import patch, MagicMock

from odoo_cli.client import OdooClient
from odoo_cli.target import get_target_client


class TestOdooClientExplicitCredentials(unittest.TestCase):
    """Test OdooClient with explicit url/db/username/password kwargs."""

    @patch('xmlrpc.client.ServerProxy')
    def test_connect_explicit(self, mock_server):
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 42
        mock_server.return_value = mock_common

        client = OdooClient(
            url='https://target.odoo.com',
            db='target_db',
            username='admin@test.com',
            password='secret-key',
        )
        uid = client.connect()

        self.assertEqual(uid, 42)
        self.assertEqual(client.url, 'https://target.odoo.com')
        self.assertEqual(client.db, 'target_db')
        self.assertEqual(client.username, 'admin@test.com')
        mock_common.authenticate.assert_called_with(
            'target_db', 'admin@test.com', 'secret-key', {}
        )

    @patch('xmlrpc.client.ServerProxy')
    def test_explicit_does_not_call_config_validate(self, mock_server):
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 1
        mock_server.return_value = mock_common

        # If Config.validate() were called, it would raise because
        # ODOO_URL etc. may not be set in test environment.
        # The explicit path should bypass Config entirely.
        with patch('odoo_cli.client.Config') as mock_config:
            mock_config.validate.side_effect = ValueError("should not be called")
            client = OdooClient(
                url='https://x.odoo.com', db='x', username='u', password='p')
            # Should NOT raise
            self.assertEqual(client.db, 'x')

    @patch('odoo_cli.client.Config')
    @patch('xmlrpc.client.ServerProxy')
    def test_legacy_mode_unchanged(self, mock_server, mock_config):
        """OdooClient() with no args still reads from Config."""
        mock_config.ODOO_URL = 'https://legacy.odoo.com'
        mock_config.ODOO_DB = 'legacy_db'
        mock_config.ODOO_USER = 'user'
        mock_config.ODOO_PASSWORD = 'pass'
        mock_config.ODOO_VERIFY_SSL = False

        mock_common = MagicMock()
        mock_common.authenticate.return_value = 1
        mock_server.return_value = mock_common

        client = OdooClient()
        self.assertEqual(client.url, 'https://legacy.odoo.com')
        self.assertEqual(client.db, 'legacy_db')
        mock_config.validate.assert_called_once()


class TestGetTargetClient(unittest.TestCase):
    """Test the get_target_client() factory function."""

    @patch.dict(os.environ, {
        'TARGET_MIGRATION_URL': '',
        'TARGET_MIGRATION_DB': '',
        'TARGET_MIGRATION_USERNAME': '',
        'TARGET_MIGRATION_PASSWORD': '',
    })
    def test_returns_none_when_all_empty(self):
        self.assertIsNone(get_target_client())

    @patch.dict(os.environ, {
        'TARGET_MIGRATION_URL': 'https://target.odoo.com',
        'TARGET_MIGRATION_DB': '',
        'TARGET_MIGRATION_USERNAME': 'user',
        'TARGET_MIGRATION_PASSWORD': 'pass',
    })
    def test_returns_none_when_partial(self):
        self.assertIsNone(get_target_client())

    @patch.dict(os.environ, {}, clear=False)
    def test_returns_none_when_not_set(self):
        # Remove target vars if they happen to exist
        for key in ['TARGET_MIGRATION_URL', 'TARGET_MIGRATION_DB',
                     'TARGET_MIGRATION_USERNAME', 'TARGET_MIGRATION_PASSWORD']:
            os.environ.pop(key, None)
        self.assertIsNone(get_target_client())

    @patch.dict(os.environ, {
        'TARGET_MIGRATION_URL': 'https://target.odoo.com',
        'TARGET_MIGRATION_DB': 'target_db',
        'TARGET_MIGRATION_USERNAME': 'admin@test.com',
        'TARGET_MIGRATION_PASSWORD': 'secret',
    })
    def test_returns_client_when_configured(self):
        client = get_target_client()
        self.assertIsNotNone(client)
        self.assertIsInstance(client, OdooClient)
        self.assertEqual(client.url, 'https://target.odoo.com')
        self.assertEqual(client.db, 'target_db')
        self.assertEqual(client.username, 'admin@test.com')

    @patch.dict(os.environ, {
        'TARGET_MIGRATION_URL': '  https://target.odoo.com  ',
        'TARGET_MIGRATION_DB': '  target_db  ',
        'TARGET_MIGRATION_USERNAME': '  admin@test.com  ',
        'TARGET_MIGRATION_PASSWORD': '  secret  ',
    })
    def test_strips_whitespace(self):
        client = get_target_client()
        self.assertIsNotNone(client)
        self.assertEqual(client.url, 'https://target.odoo.com')
        self.assertEqual(client.db, 'target_db')


class TestDiffLogic(unittest.TestCase):
    """Test the _diff helper from compare_instances."""

    def setUp(self):
        # Import here to avoid sys.path issues
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'compare_instances',
            os.path.join(os.path.dirname(__file__), '..',
                         'business_units', 'hotel-trip-agency',
                         'compare_instances.py'))
        self.mod = importlib.util.module_from_spec(spec)
        # Patch imports the module needs
        import sys as _sys
        _sys.modules['odoo_cli'] = MagicMock()
        spec.loader.exec_module(self.mod)

    def test_diff_all_missing(self):
        src = [{'name': 'A'}, {'name': 'B'}]
        tgt = []
        result = self.mod._diff(src, tgt, key_fn=lambda r: r['name'])
        self.assertEqual(result['missing'], ['A', 'B'])
        self.assertEqual(result['present'], [])
        self.assertEqual(result['extra'], [])

    def test_diff_all_present(self):
        src = [{'name': 'A'}]
        tgt = [{'name': 'A'}]
        result = self.mod._diff(src, tgt, key_fn=lambda r: r['name'])
        self.assertEqual(result['missing'], [])
        self.assertEqual(result['present'], ['A'])

    def test_diff_mixed(self):
        src = [{'name': 'A'}, {'name': 'B'}]
        tgt = [{'name': 'B'}, {'name': 'C'}]
        result = self.mod._diff(src, tgt, key_fn=lambda r: r['name'])
        self.assertEqual(result['missing'], ['A'])
        self.assertEqual(result['present'], ['B'])
        self.assertEqual(result['extra'], ['C'])

    def test_diff_tuple_key(self):
        src = [{'model': 'sale.order', 'name': 'x_is_tour'}]
        tgt = [{'model': 'sale.order', 'name': 'x_other'}]
        result = self.mod._diff(src, tgt,
                                key_fn=lambda r: (r['model'], r['name']))
        self.assertEqual(result['missing'], [('sale.order', 'x_is_tour')])
        self.assertEqual(result['extra'], [('sale.order', 'x_other')])


if __name__ == '__main__':
    unittest.main()
