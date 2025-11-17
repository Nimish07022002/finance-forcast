import json
import datetime
from typing import Dict, Any, List
from .config import DB_CONFIG

# Initialize the global logger outside the class for singleton pattern (imported by agent_service)
DB_LOGGER = None


class DatabaseLogger:
    """
    Handles logging request/response data to a MySQL database or falls back to console.
    """

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        self.is_connected = False
        self.cursor = None
        self.setup_complete = False

    def initialize_db(self):
        """Attempts to connect to MySQL and set up the 'forecasts' table."""
        if self.setup_complete:
            return

        try:
            import mysql.connector

            db_name = self.db_config["database"]
            temp_config = {k: v for k, v in self.db_config.items() if k != "database"}
            self.connection = mysql.connector.connect(**temp_config)
            self.cursor = self.connection.cursor()

            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            self.cursor.execute(f"USE {db_name}")

            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME,
                    company VARCHAR(255),
                    input_task TEXT,
                    output_json JSON,
                    sources JSON
                )
            """
            )
            self.connection.commit()
            self.is_connected = True
            print(
                "DatabaseLogger: Successfully connected to MySQL and initialized table."
            )

        except ImportError:
            self.is_connected = False
            print(
                "DatabaseLogger: Cannot import 'mysql.connector'. Falling back to console logging."
            )
        except Exception as e:
            self.is_connected = False
            print(
                f"DatabaseLogger: Failed to connect to MySQL. Falling back to console logging. Error: {e}"
            )

        self.setup_complete = True

    def log_result(
        self,
        company: str,
        task: str,
        output: Dict[str, Any],
        sources: List[Dict[str, str]],
    ):
        """Logs the forecast result to MySQL if connected, otherwise to console."""
        if not self.setup_complete:
            self.initialize_db()

        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "company": company,
            "input_task": task,
            "output_json": output,
            "sources": sources,
        }

        if self.is_connected:
            try:
                insert_query = (
                    "INSERT INTO forecasts (timestamp, company, input_task, output_json, sources) "
                    "VALUES (%s, %s, %s, %s, %s)"
                )
                output_str = json.dumps(output)
                sources_str = json.dumps(sources)

                self.cursor.execute(
                    insert_query,
                    (log_data["timestamp"], company, task, output_str, sources_str),
                )
                self.connection.commit()
            except Exception as e:
                print(f"DatabaseLogger ERROR (SQL Insertion): {e}")

        # Console Log Fallback
        print("-" * 50)
        print(f"LOG: Forecast for {company} at {log_data['timestamp']}")
        print(f"Task: {task}")
        print(f"Output (JSON):\n{json.dumps(output, indent=2)}")
        print(f"Sources: {len(sources)} citations.")
        print("-" * 50)

    def __del__(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass


# Initialize the global logger instance
DB_LOGGER = DatabaseLogger(DB_CONFIG)
