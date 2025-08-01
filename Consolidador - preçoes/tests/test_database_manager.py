"""
Unit tests for the DatabaseManager class.
"""
import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from services.database_manager import DatabaseManager
from models.data_models import PriceRecord


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_precos.db")
        self.db_manager = DatabaseManager(self.db_path)
        
        # Sample test data
        self.sample_record = PriceRecord(
            nome_produto="Produto Teste",
            url="https://example.com/produto",
            preco=99.99,
            preco_alvo=89.99,
            data_hora=datetime.now(),
            status="active"
        )
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close_connections()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_creation(self):
        """Test database and tables are created properly."""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('precos', 'configuracoes', 'db_version')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.assertIn('precos', tables)
        self.assertIn('configuracoes', tables)
        self.assertIn('db_version', tables)
    
    def test_indexes_creation(self):
        """Test that indexes are created properly."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_indexes = [
            'idx_produto_data',
            'idx_data_hora',
            'idx_status'
        ]
        
        for index in expected_indexes:
            self.assertIn(index, indexes)
    
    def test_insert_price_record(self):
        """Test inserting a price record."""
        # Insert record
        self.db_manager.insert_price_record(self.sample_record)
        
        # Verify record was inserted and ID was set
        self.assertIsNotNone(self.sample_record.id)
        
        # Verify record exists in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM precos WHERE id = ?", (self.sample_record.id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_insert_multiple_records(self):
        """Test inserting multiple price records."""
        records = []
        for i in range(5):
            record = PriceRecord(
                nome_produto=f"Produto {i}",
                url=f"https://example.com/produto{i}",
                preco=100.0 + i,
                preco_alvo=90.0 + i,
                data_hora=datetime.now() - timedelta(hours=i),
                status="active"
            )
            records.append(record)
            self.db_manager.insert_price_record(record)
        
        # Verify all records have IDs
        for record in records:
            self.assertIsNotNone(record.id)
        
        # Verify count in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM precos")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 5)
    
    def test_get_price_history(self):
        """Test retrieving price history for a product."""
        product_name = "Produto Histórico"
        
        # Insert multiple records for the same product
        for i in range(10):
            record = PriceRecord(
                nome_produto=product_name,
                url="https://example.com/produto",
                preco=100.0 - i,
                preco_alvo=80.0,
                data_hora=datetime.now() - timedelta(days=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Insert records for different product
        for i in range(3):
            record = PriceRecord(
                nome_produto="Outro Produto",
                url="https://example.com/outro",
                preco=50.0 + i,
                preco_alvo=40.0,
                data_hora=datetime.now() - timedelta(days=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Get history for specific product
        history = self.db_manager.get_price_history(product_name, days=30)
        
        # Verify results
        self.assertEqual(len(history), 10)
        for record in history:
            self.assertEqual(record.nome_produto, product_name)
        
        # Verify records are ordered by date (newest first)
        for i in range(len(history) - 1):
            self.assertGreaterEqual(history[i].data_hora, history[i + 1].data_hora)
    
    def test_get_price_history_with_date_filter(self):
        """Test retrieving price history with date filtering."""
        product_name = "Produto Filtro"
        
        # Insert records spanning different time periods
        base_time = datetime.now()
        for i in range(10):
            record = PriceRecord(
                nome_produto=product_name,
                url="https://example.com/produto",
                preco=100.0 - i,
                preco_alvo=80.0,
                data_hora=base_time - timedelta(days=i * 5),  # Every 5 days
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Get history for last 12 days (should get records at 0, 5, 10 days ago)
        history = self.db_manager.get_price_history(product_name, days=12)
        
        # Verify only recent records are returned
        # Records at 0, 5, 10 days ago should be included (within 12 days)
        # Record at 15 days ago should be excluded
        self.assertLessEqual(len(history), 3)
        self.assertGreaterEqual(len(history), 2)  # At least 0 and 5 days ago
        
        # Verify all returned records are within the time range
        cutoff_date = base_time - timedelta(days=12)
        for record in history:
            self.assertGreaterEqual(record.data_hora, cutoff_date)
    
    def test_get_latest_prices(self):
        """Test retrieving latest prices for all products."""
        products = ["Produto A", "Produto B", "Produto C"]
        
        # Insert multiple records for each product
        for product in products:
            for i in range(5):
                record = PriceRecord(
                    nome_produto=product,
                    url=f"https://example.com/{product.lower().replace(' ', '')}",
                    preco=100.0 + i,
                    preco_alvo=90.0,
                    data_hora=datetime.now() - timedelta(hours=5-i),  # Latest has highest price
                    status="active"
                )
                self.db_manager.insert_price_record(record)
        
        # Get latest prices
        latest_prices = self.db_manager.get_latest_prices()
        
        # Verify results
        self.assertEqual(len(latest_prices), 3)
        
        # Verify each product appears once with latest price
        product_prices = {record.nome_produto: record.preco for record in latest_prices}
        for product in products:
            self.assertIn(product, product_prices)
            self.assertEqual(product_prices[product], 104.0)  # Latest price should be 100 + 4
    
    def test_cleanup_old_records(self):
        """Test cleaning up old records."""
        # Insert old records
        for i in range(5):
            record = PriceRecord(
                nome_produto="Produto Antigo",
                url="https://example.com/antigo",
                preco=100.0,
                preco_alvo=90.0,
                data_hora=datetime.now() - timedelta(days=400 + i),
                status="inactive"  # Old records should be inactive
            )
            self.db_manager.insert_price_record(record)
        
        # Insert recent records
        for i in range(3):
            record = PriceRecord(
                nome_produto="Produto Recente",
                url="https://example.com/recente",
                preco=100.0,
                preco_alvo=90.0,
                data_hora=datetime.now() - timedelta(days=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Cleanup records older than 365 days
        self.db_manager.cleanup_old_records(days=365)
        
        # Verify old inactive records were deleted
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM precos")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM precos WHERE nome_produto = 'Produto Antigo'")
        old_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM precos WHERE nome_produto = 'Produto Recente'")
        recent_count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(old_count, 0)  # Old records should be deleted
        self.assertEqual(recent_count, 3)  # Recent records should remain
        self.assertEqual(total_count, 3)
    
    def test_database_stats(self):
        """Test getting database statistics."""
        # Insert test data
        for i in range(10):
            record = PriceRecord(
                nome_produto=f"Produto {i % 3}",  # 3 unique products
                url=f"https://example.com/produto{i}",
                preco=100.0 + i,
                preco_alvo=90.0,
                data_hora=datetime.now() - timedelta(hours=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Get stats
        stats = self.db_manager.get_database_stats()
        
        # Verify stats
        self.assertEqual(stats['total_records'], 10)
        self.assertEqual(stats['active_records'], 10)
        self.assertEqual(stats['unique_products'], 3)
        self.assertIsNotNone(stats['oldest_record'])
        self.assertIsNotNone(stats['newest_record'])
        self.assertGreater(stats['database_size_bytes'], 0)
        self.assertEqual(stats['database_version'], 1)
    
    def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        # Insert a valid record first
        valid_record = PriceRecord(
            nome_produto="Produto Válido",
            url="https://example.com/produto",
            preco=100.0,
            preco_alvo=90.0,
            data_hora=datetime.now(),
            status="active"
        )
        self.db_manager.insert_price_record(valid_record)
        
        # Now test database-level constraint by directly manipulating the connection
        # This simulates a database error during transaction
        conn = self.db_manager._get_connection()
        
        # Test that transaction rollback works by causing a database error
        with self.assertRaises(sqlite3.Error):
            with self.db_manager._transaction() as trans_conn:
                # Insert a valid record
                trans_conn.execute("""
                    INSERT INTO precos (nome_produto, url, preco, preco_alvo, data_hora, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("Produto Teste", "https://example.com/teste", 50.0, 40.0, datetime.now(), "active"))
                
                # Cause an error by violating a constraint
                trans_conn.execute("""
                    INSERT INTO precos (nome_produto, url, preco, preco_alvo, data_hora, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("Produto Erro", "https://example.com/erro", -10.0, 40.0, datetime.now(), "active"))
        
        # Verify only the original record exists (transaction was rolled back)
        cursor = conn.execute("SELECT COUNT(*) FROM precos")
        count = cursor.fetchone()[0]
        
        self.assertEqual(count, 1)  # Only the first valid record should exist
    
    def test_database_version(self):
        """Test database version tracking."""
        version = self.db_manager.get_db_version()
        self.assertEqual(version, 1)
    
    def test_migration_system(self):
        """Test database migration system."""
        # Initial version should be 1
        self.assertEqual(self.db_manager.get_db_version(), 1)
        
        # Run migrations
        self.db_manager.migrate_database()
        
        # Version should be updated if migrations were applied
        final_version = self.db_manager.get_db_version()
        self.assertGreaterEqual(final_version, 1)
    
    def test_connection_management(self):
        """Test database connection management."""
        # Test that connections are properly managed
        conn1 = self.db_manager._get_connection()
        conn2 = self.db_manager._get_connection()
        
        # Should return same connection for same thread
        self.assertIs(conn1, conn2)
        
        # Test connection close
        self.db_manager.close_connections()
        
        # New connection should be created after close
        conn3 = self.db_manager._get_connection()
        self.assertIsNot(conn1, conn3)
    
    def test_update_price_record(self):
        """Test updating a price record."""
        # Insert a record first
        self.db_manager.insert_price_record(self.sample_record)
        record_id = self.sample_record.id
        
        # Update the record
        self.db_manager.update_price_record(record_id, preco=79.99, status="updated")
        
        # Verify the update
        updated_record = self.db_manager.get_price_record_by_id(record_id)
        self.assertIsNotNone(updated_record)
        self.assertEqual(updated_record.preco, 79.99)
        self.assertEqual(updated_record.status, "updated")
        self.assertEqual(updated_record.nome_produto, self.sample_record.nome_produto)  # Unchanged
    
    def test_update_price_record_invalid_field(self):
        """Test updating with invalid field raises error."""
        # Insert a record first
        self.db_manager.insert_price_record(self.sample_record)
        record_id = self.sample_record.id
        
        # Try to update with invalid field
        with self.assertRaises(ValueError):
            self.db_manager.update_price_record(record_id, invalid_field="value")
    
    def test_update_price_record_no_fields(self):
        """Test updating with no fields raises error."""
        # Insert a record first
        self.db_manager.insert_price_record(self.sample_record)
        record_id = self.sample_record.id
        
        # Try to update with no fields
        with self.assertRaises(ValueError):
            self.db_manager.update_price_record(record_id)
    
    def test_update_nonexistent_record(self):
        """Test updating non-existent record raises error."""
        with self.assertRaises(ValueError):
            self.db_manager.update_price_record(99999, preco=100.0)
    
    def test_delete_price_record(self):
        """Test deleting a price record."""
        # Insert a record first
        self.db_manager.insert_price_record(self.sample_record)
        record_id = self.sample_record.id
        
        # Verify record exists
        record = self.db_manager.get_price_record_by_id(record_id)
        self.assertIsNotNone(record)
        
        # Delete the record
        self.db_manager.delete_price_record(record_id)
        
        # Verify record is deleted
        deleted_record = self.db_manager.get_price_record_by_id(record_id)
        self.assertIsNone(deleted_record)
    
    def test_delete_nonexistent_record(self):
        """Test deleting non-existent record raises error."""
        with self.assertRaises(ValueError):
            self.db_manager.delete_price_record(99999)
    
    def test_get_price_record_by_id(self):
        """Test retrieving a price record by ID."""
        # Insert a record
        self.db_manager.insert_price_record(self.sample_record)
        record_id = self.sample_record.id
        
        # Retrieve the record
        retrieved_record = self.db_manager.get_price_record_by_id(record_id)
        
        # Verify the record
        self.assertIsNotNone(retrieved_record)
        self.assertEqual(retrieved_record.id, record_id)
        self.assertEqual(retrieved_record.nome_produto, self.sample_record.nome_produto)
        self.assertEqual(retrieved_record.preco, self.sample_record.preco)
    
    def test_get_price_record_by_id_not_found(self):
        """Test retrieving non-existent record returns None."""
        record = self.db_manager.get_price_record_by_id(99999)
        self.assertIsNone(record)
    
    def test_get_products_list(self):
        """Test getting list of unique product names."""
        # Insert records for different products
        products = ["Produto A", "Produto B", "Produto A", "Produto C"]
        for i, product_name in enumerate(products):
            record = PriceRecord(
                nome_produto=product_name,
                url=f"https://example.com/produto{i}",
                preco=100.0 + i,
                preco_alvo=90.0,
                data_hora=datetime.now(),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Get products list
        products_list = self.db_manager.get_products_list()
        
        # Verify results
        expected_products = ["Produto A", "Produto B", "Produto C"]
        self.assertEqual(sorted(products_list), sorted(expected_products))
        self.assertEqual(len(products_list), 3)  # Should be unique
    
    def test_get_price_records_by_product(self):
        """Test getting all records for a specific product."""
        product_name = "Produto Específico"
        
        # Insert multiple records for the same product
        for i in range(5):
            record = PriceRecord(
                nome_produto=product_name,
                url="https://example.com/produto",
                preco=100.0 + i,
                preco_alvo=90.0,
                data_hora=datetime.now() - timedelta(hours=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Insert records for different product
        other_record = PriceRecord(
            nome_produto="Outro Produto",
            url="https://example.com/outro",
            preco=50.0,
            preco_alvo=40.0,
            data_hora=datetime.now(),
            status="active"
        )
        self.db_manager.insert_price_record(other_record)
        
        # Get records for specific product
        records = self.db_manager.get_price_records_by_product(product_name)
        
        # Verify results
        self.assertEqual(len(records), 5)
        for record in records:
            self.assertEqual(record.nome_produto, product_name)
        
        # Verify records are ordered by date (newest first)
        for i in range(len(records) - 1):
            self.assertGreaterEqual(records[i].data_hora, records[i + 1].data_hora)
    
    def test_get_price_records_by_product_with_limit(self):
        """Test getting records with limit."""
        product_name = "Produto Limitado"
        
        # Insert more records than the limit
        for i in range(10):
            record = PriceRecord(
                nome_produto=product_name,
                url="https://example.com/produto",
                preco=100.0 + i,
                preco_alvo=90.0,
                data_hora=datetime.now() - timedelta(hours=i),
                status="active"
            )
            self.db_manager.insert_price_record(record)
        
        # Get records with limit
        records = self.db_manager.get_price_records_by_product(product_name, limit=3)
        
        # Verify limit is respected
        self.assertEqual(len(records), 3)
        
        # Verify we get the most recent records
        self.assertEqual(records[0].preco, 100.0)  # Most recent
        self.assertEqual(records[1].preco, 101.0)  # Second most recent
        self.assertEqual(records[2].preco, 102.0)  # Third most recent
    
    def test_comprehensive_crud_operations(self):
        """Test complete CRUD workflow."""
        # CREATE
        record = PriceRecord(
            nome_produto="Produto CRUD",
            url="https://example.com/crud",
            preco=150.0,
            preco_alvo=120.0,
            data_hora=datetime.now(),
            status="active"
        )
        self.db_manager.insert_price_record(record)
        record_id = record.id
        self.assertIsNotNone(record_id)
        
        # READ
        retrieved_record = self.db_manager.get_price_record_by_id(record_id)
        self.assertIsNotNone(retrieved_record)
        self.assertEqual(retrieved_record.nome_produto, "Produto CRUD")
        self.assertEqual(retrieved_record.preco, 150.0)
        
        # UPDATE
        self.db_manager.update_price_record(record_id, preco=140.0, status="updated")
        updated_record = self.db_manager.get_price_record_by_id(record_id)
        self.assertEqual(updated_record.preco, 140.0)
        self.assertEqual(updated_record.status, "updated")
        
        # DELETE
        self.db_manager.delete_price_record(record_id)
        deleted_record = self.db_manager.get_price_record_by_id(record_id)
        self.assertIsNone(deleted_record)


if __name__ == '__main__':
    unittest.main()