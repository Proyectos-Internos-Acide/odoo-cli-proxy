import json
import unittest
from unittest.mock import patch, MagicMock

import mcp_server


def _mock_client():
    """Crea un OdooClient mock y lo inyecta en mcp_server._client."""
    mock = MagicMock()
    mcp_server._client = mock
    return mock


class TestSearchRead(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_basic_search(self):
        self.client.execute.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = json.loads(mcp_server.search_read("res.partner"))
        self.assertEqual(len(result), 2)
        self.client.execute.assert_called_once_with(
            "res.partner", "search_read", [], limit=10
        )

    def test_with_domain_and_fields(self):
        self.client.execute.return_value = [{"id": 1, "name": "Alice", "email": "a@b.com"}]
        result = json.loads(
            mcp_server.search_read(
                "res.partner",
                domain='[["customer_rank", ">", 0]]',
                fields="name,email",
                limit=5,
            )
        )
        self.assertEqual(result[0]["email"], "a@b.com")
        self.client.execute.assert_called_once_with(
            "res.partner",
            "search_read",
            [["customer_rank", ">", 0]],
            fields=["name", "email"],
            limit=5,
        )

    def test_with_offset_and_order(self):
        self.client.execute.return_value = []
        mcp_server.search_read(
            "sale.order", offset=20, order="create_date desc"
        )
        self.client.execute.assert_called_once_with(
            "sale.order",
            "search_read",
            [],
            limit=10,
            offset=20,
            order="create_date desc",
        )

    def test_empty_fields_not_passed(self):
        self.client.execute.return_value = []
        mcp_server.search_read("res.partner", fields="")
        _, kwargs = self.client.execute.call_args
        self.assertNotIn("fields", kwargs)


class TestExecute(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_simple_method(self):
        self.client.execute.return_value = True
        result = json.loads(
            mcp_server.execute("sale.order", "action_confirm", args="[[42]]")
        )
        self.assertTrue(result)
        self.client.execute.assert_called_once_with(
            "sale.order", "action_confirm", [42]
        )

    def test_with_kwargs(self):
        self.client.execute.return_value = [{"id": 1}]
        mcp_server.execute(
            "res.partner",
            "search_read",
            args="[[]]",
            kwargs='{"fields": ["name"], "limit": 1}',
        )
        self.client.execute.assert_called_once_with(
            "res.partner", "search_read", [], fields=["name"], limit=1
        )

    def test_no_args(self):
        self.client.execute.return_value = {"name": {"type": "char"}}
        mcp_server.execute("res.partner", "fields_get")
        self.client.execute.assert_called_once_with("res.partner", "fields_get")


class TestReadFields(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_default_attributes(self):
        self.client.execute.return_value = {
            "name": {"string": "Name", "type": "char", "required": True}
        }
        result = json.loads(mcp_server.read_fields("res.partner"))
        self.assertIn("name", result)
        self.client.execute.assert_called_once_with(
            "res.partner",
            "fields_get",
            attributes=["string", "type", "required", "readonly", "relation"],
        )

    def test_custom_attributes(self):
        self.client.execute.return_value = {}
        mcp_server.read_fields("sale.order", attributes="string,type")
        self.client.execute.assert_called_once_with(
            "sale.order", "fields_get", attributes=["string", "type"]
        )


class TestListModels(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_no_filter(self):
        self.client.execute.return_value = [
            {"id": 1, "model": "res.partner", "name": "Contact"}
        ]
        result = json.loads(mcp_server.list_models())
        self.assertEqual(result[0]["model"], "res.partner")
        self.client.execute.assert_called_once_with(
            "ir.model",
            "search_read",
            [],
            fields=["model", "name"],
            order="model",
        )

    def test_with_filter(self):
        self.client.execute.return_value = []
        mcp_server.list_models(filter="sale")
        self.client.execute.assert_called_once_with(
            "ir.model",
            "search_read",
            [["model", "ilike", "sale"]],
            fields=["model", "name"],
            order="model",
        )


class TestCreateRecord(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_create_returns_list(self):
        """Odoo 19 retorna lista desde create."""
        self.client.execute.return_value = [99]
        result = json.loads(
            mcp_server.create_record("res.partner", '{"name": "Test"}')
        )
        self.assertEqual(result["id"], 99)
        self.client.execute.assert_called_once_with(
            "res.partner", "create", [{"name": "Test"}]
        )

    def test_create_returns_int(self):
        """Compatibilidad con versiones que retornan int."""
        self.client.execute.return_value = 42
        result = json.loads(
            mcp_server.create_record("res.partner", '{"name": "Test"}')
        )
        self.assertEqual(result["id"], 42)


class TestWriteRecord(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_write(self):
        self.client.execute.return_value = True
        result = json.loads(
            mcp_server.write_record("res.partner", "[1, 2]", '{"name": "Updated"}')
        )
        self.assertTrue(result["success"])
        self.client.execute.assert_called_once_with(
            "res.partner", "write", [1, 2], {"name": "Updated"}
        )


class TestUnlinkRecord(unittest.TestCase):
    def setUp(self):
        self.client = _mock_client()

    def tearDown(self):
        mcp_server._client = None

    def test_unlink(self):
        self.client.execute.return_value = True
        result = json.loads(mcp_server.unlink_record("res.partner", "[1, 2]"))
        self.assertTrue(result["success"])
        self.client.execute.assert_called_once_with(
            "res.partner", "unlink", [1, 2]
        )


class TestGetClient(unittest.TestCase):
    def tearDown(self):
        mcp_server._client = None

    @patch("mcp_server.OdooClient")
    def test_lazy_init(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.connect.return_value = 1

        client = mcp_server._get_client()
        self.assertIs(client, mock_instance)
        mock_instance.connect.assert_called_once()

    @patch("mcp_server.OdooClient")
    def test_reuses_client(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.connect.return_value = 1

        c1 = mcp_server._get_client()
        c2 = mcp_server._get_client()
        self.assertIs(c1, c2)
        # Solo se instancia una vez
        mock_cls.assert_called_once()


class TestSerialize(unittest.TestCase):
    def test_basic_types(self):
        result = json.loads(mcp_server._serialize({"a": 1, "b": "text"}))
        self.assertEqual(result, {"a": 1, "b": "text"})

    def test_non_serializable_falls_back_to_str(self):
        from datetime import date
        result = mcp_server._serialize({"date": date(2025, 1, 15)})
        self.assertIn("2025-01-15", result)

    def test_unicode_preserved(self):
        result = mcp_server._serialize({"name": "Año nuevo"})
        self.assertIn("Año nuevo", result)


if __name__ == "__main__":
    unittest.main()
