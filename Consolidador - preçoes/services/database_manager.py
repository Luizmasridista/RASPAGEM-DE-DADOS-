"""
Database manager for the price monitoring system.
Handles SQLite database operations with connection pooling and transaction management.
"""
import sqlite3
import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

from models.interfaces import DatabaseManagerInterface
from models.data_models import PriceRecord


class DatabaseManager(DatabaseManagerInterface):
    """
    SQLite database manager with connection pooling and transaction support.
    """
    
    def __init__(self, db_path: str = "precos.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Ensure database directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self.create_tables()
        self.logger.info(f"Database manager initialized with path: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection with proper configuration.
        
        Returns:
            SQLite connection object
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                check_same_thread=False
            )
            # Enable foreign keys and WAL mode for better performance
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.row_factory = sqlite3.Row
            
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """
        Context manager for database transactions with automatic rollback on error.
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database transaction failed, rolled back: {e}")
            raise
    
    def create_tables(self) -> None:
        """
        Create database tables with proper indexes and constraints.
        """
        with self._transaction() as conn:
            # Create main price records table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS precos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_produto TEXT NOT NULL,
                    url TEXT NOT NULL,
                    preco REAL NOT NULL,
                    preco_alvo REAL NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    erro TEXT NULL,
                    CONSTRAINT chk_preco_positive CHECK (preco >= 0),
                    CONSTRAINT chk_preco_alvo_positive CHECK (preco_alvo > 0)
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_produto_data 
                ON precos (nome_produto, data_hora DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_data_hora 
                ON precos (data_hora DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON precos (status)
            """)
            
            # Create configuration table for system settings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuracoes (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create database version table for migrations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # Insert initial version if not exists
            conn.execute("""
                INSERT OR IGNORE INTO db_version (version, description)
                VALUES (1, 'Initial schema creation')
            """)
            
        self.logger.info("Database tables created successfully")
    
    def get_db_version(self) -> int:
        """
        Get current database schema version.
        
        Returns:
            Current database version
        """
        conn = self._get_connection()
        cursor = conn.execute("SELECT MAX(version) FROM db_version")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    
    def migrate_database(self) -> None:
        """
        Apply database migrations if needed.
        """
        current_version = self.get_db_version()
        self.logger.info(f"Current database version: {current_version}")
        
        # Define migrations
        migrations = {
            2: {
                'description': 'Add performance indexes',
                'sql': [
                    "CREATE INDEX IF NOT EXISTS idx_produto_preco ON precos (nome_produto, preco)",
                    "CREATE INDEX IF NOT EXISTS idx_url ON precos (url)"
                ]
            }
            # Add more migrations here as needed
        }
        
        # Apply pending migrations
        for version, migration in migrations.items():
            if version > current_version:
                self.logger.info(f"Applying migration {version}: {migration['description']}")
                with self._transaction() as conn:
                    for sql in migration['sql']:
                        conn.execute(sql)
                    
                    conn.execute("""
                        INSERT INTO db_version (version, description)
                        VALUES (?, ?)
                    """, (version, migration['description']))
                
                self.logger.info(f"Migration {version} applied successfully")
    
    def insert_price_record(self, record: PriceRecord) -> None:
        """
        Insert a price record with transaction safety.
        
        Args:
            record: PriceRecord to insert
        """
        try:
            with self._transaction() as conn:
                cursor = conn.execute("""
                    INSERT INTO precos (
                        nome_produto, url, preco, preco_alvo, 
                        data_hora, status, erro
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.nome_produto,
                    record.url,
                    record.preco,
                    record.preco_alvo,
                    record.data_hora,
                    record.status,
                    record.erro
                ))
                
                # Update the record with the generated ID
                record.id = cursor.lastrowid
                
            self.logger.debug(f"Inserted price record for {record.nome_produto}: R$ {record.preco}")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to insert price record: {e}")
            raise
    
    def get_price_history(self, product_name: str, days: int = 30) -> List[PriceRecord]:
        """
        Get price history for a product with efficient queries.
        
        Args:
            product_name: Name of the product
            days: Number of days to look back
            
        Returns:
            List of PriceRecord objects
        """
        try:
            conn = self._get_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = conn.execute("""
                SELECT id, nome_produto, url, preco, preco_alvo, 
                       data_hora, status, erro
                FROM precos
                WHERE nome_produto = ? AND data_hora >= ?
                ORDER BY data_hora DESC
            """, (product_name, cutoff_date))
            
            records = []
            for row in cursor.fetchall():
                record = PriceRecord(
                    id=row['id'],
                    nome_produto=row['nome_produto'],
                    url=row['url'],
                    preco=row['preco'],
                    preco_alvo=row['preco_alvo'],
                    data_hora=datetime.fromisoformat(row['data_hora']),
                    status=row['status'],
                    erro=row['erro']
                )
                records.append(record)
            
            self.logger.debug(f"Retrieved {len(records)} price records for {product_name}")
            return records
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get price history: {e}")
            raise
    
    def get_latest_prices(self) -> List[PriceRecord]:
        """
        Get the latest prices for all products.
        
        Returns:
            List of PriceRecord objects with latest prices
        """
        try:
            conn = self._get_connection()
            
            # Get latest record for each product
            cursor = conn.execute("""
                SELECT p1.id, p1.nome_produto, p1.url, p1.preco, p1.preco_alvo,
                       p1.data_hora, p1.status, p1.erro
                FROM precos p1
                INNER JOIN (
                    SELECT nome_produto, MAX(data_hora) as max_data
                    FROM precos
                    WHERE status = 'active'
                    GROUP BY nome_produto
                ) p2 ON p1.nome_produto = p2.nome_produto 
                     AND p1.data_hora = p2.max_data
                ORDER BY p1.data_hora DESC
            """)
            
            records = []
            for row in cursor.fetchall():
                record = PriceRecord(
                    id=row['id'],
                    nome_produto=row['nome_produto'],
                    url=row['url'],
                    preco=row['preco'],
                    preco_alvo=row['preco_alvo'],
                    data_hora=datetime.fromisoformat(row['data_hora']),
                    status=row['status'],
                    erro=row['erro']
                )
                records.append(record)
            
            self.logger.debug(f"Retrieved latest prices for {len(records)} products")
            return records
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get latest prices: {e}")
            raise
    
    def update_price_record(self, record_id: int, **kwargs) -> None:
        """
        Update a price record with new values.
        
        Args:
            record_id: ID of the record to update
            **kwargs: Fields to update (preco, status, erro, etc.)
        """
        if not kwargs:
            raise ValueError("No fields provided for update")
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        allowed_fields = {'preco', 'preco_alvo', 'status', 'erro', 'nome_produto', 'url'}
        for field, value in kwargs.items():
            if field not in allowed_fields:
                raise ValueError(f"Field '{field}' is not allowed for update")
            set_clauses.append(f"{field} = ?")
            values.append(value)
        
        values.append(record_id)
        
        try:
            with self._transaction() as conn:
                cursor = conn.execute(f"""
                    UPDATE precos 
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """, values)
                
                if cursor.rowcount == 0:
                    raise ValueError(f"No record found with ID {record_id}")
                
            self.logger.debug(f"Updated price record {record_id}")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update price record: {e}")
            raise
    
    def delete_price_record(self, record_id: int) -> None:
        """
        Delete a specific price record.
        
        Args:
            record_id: ID of the record to delete
        """
        try:
            with self._transaction() as conn:
                cursor = conn.execute("DELETE FROM precos WHERE id = ?", (record_id,))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"No record found with ID {record_id}")
                
            self.logger.debug(f"Deleted price record {record_id}")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete price record: {e}")
            raise
    
    def get_price_record_by_id(self, record_id: int) -> Optional[PriceRecord]:
        """
        Get a specific price record by ID.
        
        Args:
            record_id: ID of the record to retrieve
            
        Returns:
            PriceRecord object or None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT id, nome_produto, url, preco, preco_alvo, 
                       data_hora, status, erro
                FROM precos
                WHERE id = ?
            """, (record_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return PriceRecord(
                id=row['id'],
                nome_produto=row['nome_produto'],
                url=row['url'],
                preco=row['preco'],
                preco_alvo=row['preco_alvo'],
                data_hora=datetime.fromisoformat(row['data_hora']),
                status=row['status'],
                erro=row['erro']
            )
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get price record by ID: {e}")
            raise
    
    def get_products_list(self) -> List[str]:
        """
        Get list of all unique product names in the database.
        
        Returns:
            List of product names
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT DISTINCT nome_produto 
                FROM precos 
                ORDER BY nome_produto
            """)
            
            return [row[0] for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get products list: {e}")
            raise
    
    def get_price_records_by_product(self, product_name: str, limit: int = 100) -> List[PriceRecord]:
        """
        Get all price records for a specific product with limit.
        
        Args:
            product_name: Name of the product
            limit: Maximum number of records to return
            
        Returns:
            List of PriceRecord objects
        """
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT id, nome_produto, url, preco, preco_alvo, 
                       data_hora, status, erro
                FROM precos
                WHERE nome_produto = ?
                ORDER BY data_hora DESC
                LIMIT ?
            """, (product_name, limit))
            
            records = []
            for row in cursor.fetchall():
                record = PriceRecord(
                    id=row['id'],
                    nome_produto=row['nome_produto'],
                    url=row['url'],
                    preco=row['preco'],
                    preco_alvo=row['preco_alvo'],
                    data_hora=datetime.fromisoformat(row['data_hora']),
                    status=row['status'],
                    erro=row['erro']
                )
                records.append(record)
            
            return records
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get price records by product: {e}")
            raise
    
    def cleanup_old_records(self, days: int = 365) -> None:
        """
        Clean up old price records to maintain database size.
        
        Args:
            days: Keep records newer than this many days
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self._transaction() as conn:
                cursor = conn.execute("""
                    DELETE FROM precos
                    WHERE data_hora < ? AND status != 'active'
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                
            self.logger.info(f"Cleaned up {deleted_count} old price records")
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
            raise
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            conn = self._get_connection()
            
            # Get total record count
            cursor = conn.execute("SELECT COUNT(*) FROM precos")
            total_records = cursor.fetchone()[0]
            
            # Get active record count
            cursor = conn.execute("SELECT COUNT(*) FROM precos WHERE status = 'active'")
            active_records = cursor.fetchone()[0]
            
            # Get unique products count
            cursor = conn.execute("SELECT COUNT(DISTINCT nome_produto) FROM precos")
            unique_products = cursor.fetchone()[0]
            
            # Get oldest and newest records
            cursor = conn.execute("SELECT MIN(data_hora), MAX(data_hora) FROM precos")
            date_range = cursor.fetchone()
            
            # Get database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            return {
                'total_records': total_records,
                'active_records': active_records,
                'unique_products': unique_products,
                'oldest_record': date_range[0],
                'newest_record': date_range[1],
                'database_size_bytes': db_size,
                'database_version': self.get_db_version()
            }
            
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get database stats: {e}")
            raise
    
    def close_connections(self) -> None:
        """
        Close all database connections.
        """
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        
        self.logger.info("Database connections closed")
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.close_connections()
        except:
            pass  # Ignore errors during cleanup