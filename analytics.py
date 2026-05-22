"""
PHASE 4: Economic Analytics & Diagnostics
- Velocity of Money calculation
- Gini Coefficient (wealth distribution)
- Treasury audit trails
- System health metrics
"""

import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from models import EconomicMetrics, TransactionRecord

DB_PATH = "economy.db"


class AnalyticsEngine:
    """Generates system-wide economic metrics and diagnostics"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_total_circulation(self) -> float:
        """Total monetary supply in active circulation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(balance) as total FROM users")
            row = cursor.fetchone()
            return row['total'] or 0.0

    def calculate_velocity_of_money(self, time_window_hours: int = 24) -> float:
        """
        Velocity of Money (V) = Total Transactions / Total Circulation
        
        Higher V = more active trading economy
        Lower V = hoarding behavior
        
        V = (Σ transaction_amounts in last N hours) / (Total circulation)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get transaction volume in time window
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            cursor.execute(
                """
                SELECT SUM(amount) as total_volume FROM transactions
                WHERE timestamp > ?
                """,
                (cutoff_time.isoformat(),)
            )
            volume_row = cursor.fetchone()
            total_volume = volume_row['total_volume'] or 0.0
            
            # Get total circulation
            total_circulation = self.get_total_circulation()
            
            if total_circulation == 0:
                return 0.0
            
            velocity = total_volume / total_circulation
            return velocity

    def calculate_gini_coefficient(self) -> float:
        """
        Gini Coefficient (0 = perfect equality, 1 = perfect inequality)
        
        Measures wealth distribution across players.
        
        Formula:
        G = (2 * Σ(i * balance_i)) / (n * Σ balance_i) - (n+1)/n
        
        Where i = rank (1 to n), n = number of users
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch all balances, ordered
            cursor.execute(
                "SELECT balance FROM users ORDER BY balance ASC"
            )
            balances = [row['balance'] for row in cursor.fetchall()]
            
            if len(balances) <= 1:
                return 0.0
            
            n = len(balances)
            total_balance = sum(balances)
            
            if total_balance == 0:
                return 0.0
            
            # Cumulative sum weighted by index
            weighted_sum = sum((i + 1) * balance for i, balance in enumerate(balances))
            
            # Gini formula
            gini = (2.0 * weighted_sum) / (n * total_balance) - (n + 1.0) / n
            
            # Clamp to [0, 1]
            return max(0.0, min(1.0, gini))

    def get_treasury_balance(self, treasury_id: str = "GOV_01") -> float:
        """Current state treasury balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (treasury_id,)
            )
            row = cursor.fetchone()
            return row['balance'] if row else 0.0

    def get_num_active_players(self) -> int:
        """Count of players with recent activity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Active = has position update in last hour
            cursor.execute(
                """
                SELECT COUNT(DISTINCT user_id) as count FROM player_positions
                WHERE updated_at > datetime('now', '-1 hour')
                """
            )
            row = cursor.fetchone()
            return row['count'] or 0

    def get_total_transactions(self) -> int:
        """Total transaction count in ledger"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM transactions")
            row = cursor.fetchone()
            return row['count'] or 0

    def get_metrics(self) -> EconomicMetrics:
        """
        Aggregate all economic metrics into single snapshot.
        Call this periodically to populate analytics_snapshot table.
        """
        return EconomicMetrics(
            total_circulation=self.get_total_circulation(),
            velocity_of_money=self.calculate_velocity_of_money(time_window_hours=24),
            gini_coefficient=self.calculate_gini_coefficient(),
            treasury_balance=self.get_treasury_balance(),
            num_active_players=self.get_num_active_players(),
            num_transactions=self.get_total_transactions(),
            captured_at=datetime.now()
        )

    def save_metrics_snapshot(self):
        """
        Persist current metrics to analytics_snapshot table.
        Call this on a scheduled interval (e.g., every 5 minutes).
        """
        metrics = self.get_metrics()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO analytics_snapshot
                (total_circulation, velocity_of_money, gini_coefficient, 
                 treasury_balance, num_active_players, num_transactions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.total_circulation,
                    metrics.velocity_of_money,
                    metrics.gini_coefficient,
                    metrics.treasury_balance,
                    metrics.num_active_players,
                    metrics.num_transactions
                )
            )

    def get_recent_metrics_history(self, limit: int = 50) -> List[EconomicMetrics]:
        """Retrieve recent metric snapshots for trend analysis"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM analytics_snapshot
                ORDER BY captured_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            return [
                EconomicMetrics(
                    total_circulation=row['total_circulation'],
                    velocity_of_money=row['velocity_of_money'],
                    gini_coefficient=row['gini_coefficient'],
                    treasury_balance=row['treasury_balance'],
                    num_active_players=row['num_active_players'],
                    num_transactions=row['num_transactions'],
                    captured_at=datetime.fromisoformat(row['captured_at'])
                )
                for row in cursor.fetchall()
            ]

    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve recent audit log entries (tax collection, escrow events, etc.)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            return [
                {
                    "log_id": row['log_id'],
                    "event_type": row['event_type'],
                    "sender_id": row['sender_id'],
                    "receiver_id": row['receiver_id'],
                    "amount": row['amount'],
                    "metadata": row['metadata'],
                    "timestamp": row['timestamp']
                }
                for row in cursor.fetchall()
            ]

    def get_wealth_distribution(self) -> List[Dict]:
        """
        Retrieve sorted wealth distribution by user.
        Useful for dashboards showing who has most/least tokens.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, username, balance, user_type
                FROM users
                ORDER BY balance DESC
                """
            )
            
            total = self.get_total_circulation()
            
            return [
                {
                    "user_id": row['user_id'],
                    "username": row['username'],
                    "balance": row['balance'],
                    "user_type": row['user_type'],
                    "percentage_of_total": (row['balance'] / total * 100) if total > 0 else 0
                }
                for row in cursor.fetchall()
            ]

    def verify_zero_sum_invariant(self) -> Tuple[bool, float, str]:
        """
        Critical health check: verify zero-sum property.
        Should return True at all times if system is functioning correctly.
        
        Returns: (is_valid, total_circulation, error_message)
        """
        total = self.get_total_circulation()
        genesis = 1_000_000.0
        tolerance = 0.01
        
        if abs(total - genesis) < tolerance:
            return (True, total, "")
        else:
            error = f"CRITICAL: Total circulation {total} != genesis {genesis}"
            return (False, total, error)
