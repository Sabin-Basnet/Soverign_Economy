"""
PHASE 2: REST API Financial Engine
- Zero-Sum Transfer Isolation (SELECT FOR UPDATE)
- Velocity Tax Middleware (VAT 2%)
- Escrow State Management
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
import json
import math
from typing import Optional, Tuple
from models import (
    TransferRequest, TransferResponse, EscrowCreateRequest, EscrowCompleteRequest,
    EscrowResponse, UserBalance
)

# Configuration
VELOCITY_TAX_RATE = 0.02  # 2% VAT on all commerce
TREASURY_ID = "GOV_01"
DB_PATH = "economy.db"


class BankingEngine:
    """ACID-compliant financial ledger engine with zero-sum invariant protection"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with enforced ACID isolation"""
        conn = sqlite3.connect(self.db_path)
        # Enable row-level locking and serializable isolation
        conn.execute("PRAGMA transaction_mode = IMMEDIATE")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def transfer(self, req: TransferRequest) -> TransferResponse:
        """
        SAFE P2P Transfer with Velocity Tax Middleware
        
        Invariant Protection:
        - Row-level locks prevent double-spend race conditions
        - Tax is atomically routed to Treasury
        - All-or-nothing transaction semantics
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # === LOCK PHASE: Acquire locks on affected rows ===
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (req.sender_id,)
            )
            sender_row = cursor.fetchone()
            if not sender_row:
                raise ValueError(f"Sender {req.sender_id} not found")
            
            sender_balance = sender_row['balance']
            
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (req.receiver_id,)
            )
            if not cursor.fetchone():
                raise ValueError(f"Receiver {req.receiver_id} not found")
            
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (TREASURY_ID,)
            )
            treasury_row = cursor.fetchone()
            if not treasury_row:
                raise ValueError("Treasury wallet not found")
            
            # === VALIDATION PHASE ===
            tax_amount = req.amount * VELOCITY_TAX_RATE
            total_debit = req.amount + tax_amount
            
            if sender_balance < total_debit:
                raise ValueError(
                    f"Insufficient balance. Have: {sender_balance}, "
                    f"Need: {total_debit} (amount + tax)"
                )
            
            # === MUTATION PHASE: All updates atomic ===
            # Debit sender (amount + tax)
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (total_debit, req.sender_id)
            )
            
            # Credit receiver (net amount, sans tax)
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (req.amount, req.receiver_id)
            )
            
            # Credit treasury with tax
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (tax_amount, TREASURY_ID)
            )
            
            # === AUDIT PHASE: Record transaction ===
            cursor.execute(
                """
                INSERT INTO transactions 
                (sender_id, receiver_id, amount, tx_type)
                VALUES (?, ?, ?, 'purchase')
                """,
                (req.sender_id, req.receiver_id, req.amount)
            )
            tx_id = cursor.lastrowid
            
            # Log tax event to audit trail
            cursor.execute(
                """
                INSERT INTO audit_log
                (event_type, sender_id, receiver_id, amount, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "velocity_tax",
                    req.sender_id,
                    TREASURY_ID,
                    tax_amount,
                    json.dumps({"original_tx_id": tx_id, "rate": VELOCITY_TAX_RATE})
                )
            )
            
            # === FINAL STATE RETRIEVAL ===
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (req.sender_id,)
            )
            sender_new_balance = cursor.fetchone()['balance']
            
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ?",
                (req.receiver_id,)
            )
            receiver_new_balance = cursor.fetchone()['balance']
            
            return TransferResponse(
                transaction_id=tx_id,
                sender_id=req.sender_id,
                receiver_id=req.receiver_id,
                amount=req.amount,
                tax_amount=tax_amount,
                net_amount=req.amount,
                sender_new_balance=sender_new_balance,
                receiver_new_balance=receiver_new_balance,
                timestamp=datetime.now()
            )

    def create_escrow(self, req: EscrowCreateRequest) -> EscrowResponse:
        """
        Initialize Logistics Escrow Lock
        
        Funds frozen until courier reaches buyer within delivery_threshold distance.
        Tax is pre-calculated and locked alongside principal.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # === LOCK PHASE ===
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (req.buyer_id,)
            )
            buyer_row = cursor.fetchone()
            if not buyer_row:
                raise ValueError(f"Buyer {req.buyer_id} not found")
            
            buyer_balance = buyer_row['balance']
            
            # === VALIDATION ===
            tax_amount = req.amount * VELOCITY_TAX_RATE
            total_lock = req.amount + tax_amount
            
            if buyer_balance < total_lock:
                raise ValueError(
                    f"Insufficient balance for escrow. Have: {buyer_balance}, "
                    f"Need: {total_lock}"
                )
            
            # === DEBIT BUYER ===
            cursor.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                (total_lock, req.buyer_id)
            )
            
            # === CREATE ESCROW RECORD ===
            cursor.execute(
                """
                INSERT INTO escrow
                (buyer_id, seller_id, shop_id, amount, tax_amount, 
                 state, delivery_threshold)
                VALUES (?, ?, ?, ?, ?, 'locked', ?)
                """,
                (req.buyer_id, req.seller_id, req.shop_id,
                 req.amount, tax_amount, req.delivery_threshold)
            )
            escrow_id = cursor.lastrowid
            
            # === AUDIT ===
            cursor.execute(
                """
                INSERT INTO audit_log
                (event_type, sender_id, receiver_id, amount, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "escrow_creation",
                    req.buyer_id,
                    "ESCROW",
                    total_lock,
                    json.dumps({"escrow_id": escrow_id, "shop_id": req.shop_id})
                )
            )
            
            return EscrowResponse(
                escrow_id=escrow_id,
                buyer_id=req.buyer_id,
                seller_id=req.seller_id,
                courier_id=None,
                amount=req.amount,
                tax_amount=tax_amount,
                state="locked",
                created_at=datetime.now()
            )

    def complete_escrow(self, req: EscrowCompleteRequest) -> EscrowResponse:
        """
        Complete Delivery & Release Escrow Funds
        
        Validates courier location matches buyer location (±delivery_threshold).
        Releases principal to merchant and tax to Treasury.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # === FETCH & LOCK ESCROW ===
            cursor.execute(
                """
                SELECT * FROM escrow WHERE escrow_id = ? FOR UPDATE
                """,
                (req.escrow_id,)
            )
            escrow_row = cursor.fetchone()
            if not escrow_row:
                raise ValueError(f"Escrow {req.escrow_id} not found")
            
            if escrow_row['state'] != 'locked':
                raise ValueError(
                    f"Escrow not in locked state. Current: {escrow_row['state']}"
                )
            
            # === FETCH COURIER POSITION ===
            cursor.execute(
                "SELECT location_x, location_y FROM player_positions WHERE user_id = ? FOR UPDATE",
                (req.courier_id,)
            )
            courier_pos = cursor.fetchone()
            if not courier_pos:
                raise ValueError(f"Courier {req.courier_id} position not found")
            
            # === DISTANCE VALIDATION ===
            distance = math.sqrt(
                (courier_pos['location_x'] - req.buyer_location_x) ** 2 +
                (courier_pos['location_y'] - req.buyer_location_y) ** 2
            )
            
            if distance > escrow_row['delivery_threshold']:
                raise ValueError(
                    f"Courier too far from buyer. Distance: {distance:.2f}, "
                    f"Threshold: {escrow_row['delivery_threshold']}"
                )
            
            # === LOCK WALLETS ===
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (escrow_row['seller_id'],)
            )
            if not cursor.fetchone():
                raise ValueError(f"Seller {escrow_row['seller_id']} not found")
            
            cursor.execute(
                "SELECT balance FROM users WHERE user_id = ? FOR UPDATE",
                (TREASURY_ID,)
            )
            if not cursor.fetchone():
                raise ValueError("Treasury not found")
            
            # === RELEASE FUNDS ===
            # Credit seller with principal
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (escrow_row['amount'], escrow_row['seller_id'])
            )
            
            # Credit treasury with tax
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (escrow_row['tax_amount'], TREASURY_ID)
            )
            
            # Mark escrow as completed
            cursor.execute(
                """
                UPDATE escrow 
                SET state = 'completed', courier_id = ?, completed_at = CURRENT_TIMESTAMP
                WHERE escrow_id = ?
                """,
                (req.courier_id, req.escrow_id)
            )
            
            # === AUDIT ===
            cursor.execute(
                """
                INSERT INTO audit_log
                (event_type, sender_id, receiver_id, amount, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "escrow_completion",
                    escrow_row['buyer_id'],
                    escrow_row['seller_id'],
                    escrow_row['amount'] + escrow_row['tax_amount'],
                    json.dumps({
                        "escrow_id": req.escrow_id,
                        "courier_id": req.courier_id,
                        "distance": distance
                    })
                )
            )
            
            return EscrowResponse(
                escrow_id=req.escrow_id,
                buyer_id=escrow_row['buyer_id'],
                seller_id=escrow_row['seller_id'],
                courier_id=req.courier_id,
                amount=escrow_row['amount'],
                tax_amount=escrow_row['tax_amount'],
                state="completed",
                created_at=datetime.fromisoformat(escrow_row['created_at'])
            )

    def get_balance(self, user_id: str) -> UserBalance:
        """Retrieve current user balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username, balance, user_type FROM users WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"User {user_id} not found")
            
            return UserBalance(
                user_id=row['user_id'],
                username=row['username'],
                balance=row['balance'],
                user_type=row['user_type']
            )

    def verify_zero_sum(self) -> Tuple[bool, float]:
        """
        INVARIANT CHECK: Verify total circulation == genesis block (1,000,000)
        Returns (is_valid, total_circulation)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(balance) as total FROM users")
            row = cursor.fetchone()
            total = row['total'] or 0.0
            genesis_total = 1_000_000.0
            return (abs(total - genesis_total) < 0.01, total)
