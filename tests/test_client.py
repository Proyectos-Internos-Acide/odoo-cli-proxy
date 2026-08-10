import unittest
from unittest.mock import patch, MagicMock
from odoo_cli.client import OdooClient

class TestOdooClient(unittest.TestCase):
    @patch('odoo_cli.client.Config')
    @patch('xmlrpc.client.ServerProxy')
    def test_connect(self, mock_server, mock_config):
        # Setup mock config
        mock_config.ODOO_URL = 'http://test'
        mock_config.ODOO_DB = 'db'
        mock_config.ODOO_USER = 'user'
        mock_config.ODOO_PASSWORD = 'pass'
        mock_config.ODOO_VERIFY_SSL = False
        
        # Setup mock XML-RPC
        mock_common = MagicMock()
        mock_common.authenticate.return_value = 1
        mock_server.return_value = mock_common
        
        client = OdooClient()
        uid = client.connect()
        
        self.assertEqual(uid, 1)
        mock_common.authenticate.assert_called_with('db', 'user', 'pass', {})

    def _client(self, mock_server, mock_config):
        """Cliente conectado contra un ServerProxy simulado."""
        mock_config.ODOO_URL = 'http://test'
        mock_config.ODOO_DB = 'db'
        mock_config.ODOO_USER = 'user'
        mock_config.ODOO_PASSWORD = 'pass'
        mock_config.ODOO_VERIFY_SSL = False
        proxy = MagicMock()
        proxy.authenticate.return_value = 1
        mock_server.return_value = proxy
        client = OdooClient()
        client.connect()
        return client, proxy

    @staticmethod
    def _positional(proxy):
        """Los argumentos posicionales que recibio execute_kw."""
        call = proxy.execute_kw.call_args[0]
        return call[3], call[4], list(call[5])

    @patch('odoo_cli.client.Config')
    @patch('xmlrpc.client.ServerProxy')
    def test_write_pasa_ids_y_vals_por_separado(self, mock_server, mock_config):
        client, proxy = self._client(mock_server, mock_config)
        client.write('res.partner', [1, 2], {'name': 'x'})
        model, method, args = self._positional(proxy)
        self.assertEqual((model, method), ('res.partner', 'write'))
        self.assertEqual(args, [[1, 2], {'name': 'x'}])

    @patch('odoo_cli.client.Config')
    @patch('xmlrpc.client.ServerProxy')
    def test_unlink_pasa_los_ids_directamente(self, mock_server, mock_config):
        client, proxy = self._client(mock_server, mock_config)
        client.unlink('res.partner', [1, 2])
        model, method, args = self._positional(proxy)
        self.assertEqual((model, method), ('res.partner', 'unlink'))
        self.assertEqual(args, [[1, 2]])

    @patch('odoo_cli.client.Config')
    @patch('xmlrpc.client.ServerProxy')
    def test_create_pasa_un_solo_dict(self, mock_server, mock_config):
        client, proxy = self._client(mock_server, mock_config)
        proxy.execute_kw.return_value = 7
        new_id = client.create('res.partner', {'name': 'x'})
        model, method, args = self._positional(proxy)
        self.assertEqual((model, method), ('res.partner', 'create'))
        self.assertEqual(args, [{'name': 'x'}])
        self.assertEqual(new_id, 7)

if __name__ == '__main__':
    unittest.main()
