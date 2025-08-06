"""
This module provides the Database class for managing SQLite operations for news headlines.
Enhanced with batch processing and connection pooling for better performance.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from threading import Lock
import queue

class DatabasePool:
    """Connection pool for managing multiple database connections."""
    
    def __init__(self, db_path: str, pool_size: int = 3):
        """
        Initialize connection pool.
        
        Args:
            db_path: Path to the SQLite database file
            pool_size: Number of connections to maintain in the pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections: queue.Queue = queue.Queue(maxsize=pool_size)
        self.lock = Lock()
        
        # Initialize connections
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent access
            self.connections.put(conn)
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        return self.connections.get()
    
    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool."""
        self.connections.put(conn)
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self.connections.empty():
            conn = self.connections.get()
            conn.close()

class Database:
    def __init__(self, db_path: str, pool_size: int = 3):
        """
        Initialize database with connection pooling.
        
        Args:
            db_path: Path to the SQLite database file
            pool_size: Number of connections in the pool
        """
        if not db_path or not isinstance(db_path, str):
            raise ValueError("db_path must be a non-empty string")
        
        self.db_path = db_path
        self.pool = DatabasePool(db_path, pool_size)
        self.batch_size = 50  # Number of records to batch together
        self.pending_batch: List[Tuple] = []
        self.batch_lock = Lock()

    def init_db(self) -> None:
        """
        Initialize database tables using a connection from the pool.
        
        Raises:
            sqlite3.Error: If database initialization fails
        """
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS headlines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    category TEXT NOT NULL,
                    raw_label TEXT,
                    confidence REAL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization failed: {e}")
            raise
        finally:
            self.pool.return_connection(conn)

    def save(self, source: str, headline: str, category: str, raw_label: str, confidence: float) -> None:
        """
        Save a headline to the database (adds to batch, flushes if batch is full).
        
        Args:
            source: Source website name
            headline: The headline text
            category: Classification category
            raw_label: Raw classification label
            confidence: Classification confidence score
            
        Raises:
            ValueError: If required parameters are invalid
        """
        if not all([source, headline, category]):
            raise ValueError("source, headline, and category cannot be empty")
        
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            raise ValueError("confidence must be a number between 0 and 1")
        
        with self.batch_lock:
            self.pending_batch.append((source, headline, category, raw_label, confidence, datetime.now()))
            
            # Flush batch if it's full
            if len(self.pending_batch) >= self.batch_size:
                self._flush_batch()

    def save_batch(self, headlines_batch: List[Tuple[str, str, str, str, float]]) -> None:
        """
        Save multiple headlines in a single batch operation.
        
        Args:
            headlines_batch: List of (source, headline, category, raw_label, confidence) tuples
        """
        if not headlines_batch:
            return
            
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # Prepare data with timestamps
            data = [(source, headline, category, raw_label, confidence, datetime.now()) 
                   for source, headline, category, raw_label, confidence in headlines_batch]
            
            cursor.executemany(
                "INSERT INTO headlines (source, headline, category, raw_label, confidence, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
                data
            )
            conn.commit()
            print(f"Saved {len(headlines_batch)} headlines in batch")
            
        except sqlite3.Error as e:
            print(f"Failed to save batch: {e}")
            raise
        finally:
            self.pool.return_connection(conn)

    def _flush_batch(self) -> None:
        """Flush the pending batch to the database."""
        if not self.pending_batch:
            return
            
        batch_to_save = self.pending_batch.copy()
        self.pending_batch.clear()
        
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO headlines (source, headline, category, raw_label, confidence, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
                batch_to_save
            )
            conn.commit()
            print(f"Flushed batch of {len(batch_to_save)} headlines")
            
        except sqlite3.Error as e:
            print(f"Failed to flush batch: {e}")
            # Restore the batch if it failed
            self.pending_batch.extend(batch_to_save)
            raise
        finally:
            self.pool.return_connection(conn)

    def clear_all_data(self) -> None:
        """
        Delete all records from the headlines table.
        
        Raises:
            sqlite3.Error: If clear operation fails
        """
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM headlines")
            conn.commit()
            print("All data cleared from database.")
        except sqlite3.Error as e:
            print(f"Failed to clear database: {e}")
            raise
        finally:
            self.pool.return_connection(conn)

    def close(self) -> None:
        """Close all database connections and flush any pending batch."""
        try:
            # Flush any remaining batch
            if self.pending_batch:
                self._flush_batch()
            
            # Close all connections in the pool
            self.pool.close_all()
        except Exception as e:
            print(f"Error closing database: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = self.pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM headlines")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT source) FROM headlines")
            total_sources = cursor.fetchone()[0]
            
            return {
                "total_records": total_records,
                "total_sources": total_sources,
                "pending_batch_size": len(self.pending_batch)
            }
        finally:
            self.pool.return_connection(conn)
